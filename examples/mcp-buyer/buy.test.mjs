import assert from "node:assert/strict";
import { once } from "node:events";
import { createServer } from "node:http";
import { test } from "node:test";

import { generateKeyPairSigner, getTransactionDecoder } from "@solana/kit";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { ExactSvmScheme } from "@x402/svm/exact/client";
import { generatePrivateKey, privateKeyToAccount } from "viem/accounts";

import { exactOffers, purchaseOnce, selectOffer } from "./buy.mjs";

const tool = "data.current-weather";
const input = { city: "Washington, DC, US" };
const baseOffer = {
  scheme: "exact", network: "eip155:8453", amount: "2000",
  asset: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  payTo: "0x1111111111111111111111111111111111111111", maxTimeoutSeconds: 300,
  extra: { name: "USD Coin", version: "2" },
};
const quote = {
  x402Version: 2,
  resource: { url: `mcp://tool/${tool}` },
  accepts: [baseOffer],
  extensions: { example: { info: {} } },
};

test("requires the exact tool, scheme, USDC asset and unambiguous network", () => {
  assert.deepEqual(exactOffers(tool, quote), [{ rail: "base", offer: baseOffer }]);
  assert.throws(() => exactOffers("another-tool", quote), /Expected an x402 v2 quote/);
  for (const offers of [
    [baseOffer, baseOffer],
    [{ ...baseOffer, amount: "2e3" }],
    [{ ...baseOffer, asset: baseOffer.payTo }],
    [{ ...baseOffer, extra: { assetTransferMethod: "permit2" } }],
  ]) {
    assert.throws(() => exactOffers(tool, { ...quote, accepts: offers }), /Unexpected base payment terms/);
  }
});

test("uses integer USDC limits and requires the reviewed recipient", () => {
  const offers = exactOffers(tool, quote);
  const approval = { network: "base", "max-usdc": "0.002", "pay-to": baseOffer.payTo };
  assert.equal(selectOffer(offers, approval), baseOffer);
  assert.throws(() => selectOffer(offers, { ...approval, "max-usdc": "0.001999" }), /exceeds --max-usdc/);
  assert.throws(() => selectOffer(offers, { ...approval, "max-usdc": "0.0020001" }), /six fractional digits/);
  assert.throws(() => selectOffer(offers, { ...approval, "pay-to": baseOffer.asset }), /quote and --pay-to differ/);
  assert.throws(() => selectOffer(offers, { ...approval, network: "solana" }), /Choose an offered network/);
});

async function exercisePurchase(offer, scheme, verifySignature) {
  let attempts = 0;
  const receipt = { success: true, network: offer.network, transaction: "fixture-transaction" };
  const result = await purchaseOnce({
    async callTool(params) {
      attempts++;
      assert.equal(params.name, tool);
      assert.deepEqual(params.arguments, input);
      const payload = params._meta["x402/payment"];
      assert.equal(payload.resource.url, quote.resource.url);
      assert.deepEqual(payload.accepted, offer);
      assert.deepEqual(payload.extensions, quote.extensions);
      verifySignature(payload.payload);
      return { content: [], structuredContent: { service: tool }, _meta: { "x402/payment-response": receipt } };
    },
  }, tool, input, { ...quote, accepts: [offer] }, offer, scheme);
  assert.deepEqual(result, { receipt, result: { service: tool }, toolError: false });
  assert.equal(attempts, 1);
}

test("signs one Base authorization and preserves the quote in the MCP request", async () => {
  const account = privateKeyToAccount(generatePrivateKey());
  await exercisePurchase(baseOffer, new ExactEvmScheme(account), ({ authorization, signature }) => {
    assert.equal(authorization.from.toLowerCase(), account.address.toLowerCase());
    assert.equal(authorization.to.toLowerCase(), baseOffer.payTo.toLowerCase());
    assert.equal(authorization.value, baseOffer.amount);
    assert.match(signature, /^0x[0-9a-f]{130}$/i);
  });
});

test("signs one Solana transaction using only the local fixture RPC", async () => {
  const [signer, receiver, facilitator] = await Promise.all([
    generateKeyPairSigner(), generateKeyPairSigner(), generateKeyPairSigner(),
  ]);
  const mint = Buffer.alloc(82);
  mint[44] = 6;
  mint[45] = 1;
  const methods = [];
  const rpc = createServer(async (request, response) => {
    let body = "";
    for await (const part of request) body += part;
    const { id, method } = JSON.parse(body);
    methods.push(method);
    response.setHeader("Content-Type", "application/json");
    const fixture = {
      data: [mint.toString("base64"), "base64"], executable: false, lamports: 1461600,
      owner: "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", rentEpoch: 0, space: mint.length,
    };
    response.end(JSON.stringify({ jsonrpc: "2.0", id, result: { context: { slot: 1 }, value: fixture } }));
  }).listen(0, "127.0.0.1");
  await once(rpc, "listening");
  try {
    const offer = {
      ...baseOffer,
      network: "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
      asset: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
      payTo: receiver.address,
      extra: { feePayer: facilitator.address, recentBlockhash: "11111111111111111111111111111111", lastValidBlockHeight: "1" },
    };
    const choice = selectOffer(exactOffers(tool, { ...quote, accepts: [offer] }), {
      network: "solana", "max-usdc": "0.002", "pay-to": receiver.address,
    });
    const scheme = new ExactSvmScheme(signer, { rpcUrl: `http://127.0.0.1:${rpc.address().port}` });
    await exercisePurchase(choice, scheme, ({ transaction }) => {
      const decoded = getTransactionDecoder().decode(Buffer.from(transaction, "base64"));
      assert.equal(decoded.signatures[signer.address]?.length, 64);
      assert.equal(decoded.signatures[facilitator.address], null);
    });
    assert.deepEqual(methods, ["getAccountInfo"]);
  } finally {
    rpc.close();
    await once(rpc, "close");
  }
});

test("does not submit again after an ambiguous response", async () => {
  const scheme = new ExactEvmScheme(privateKeyToAccount(generatePrivateKey()));
  for (const simulate of [
    () => { throw new Error("connection lost"); },
    () => ({ content: [], isError: true }),
  ]) {
    let attempts = 0;
    await assert.rejects(purchaseOnce({
      async callTool() {
        attempts++;
        return simulate();
      },
    }, tool, input, quote, baseOffer, scheme), /Check your wallet history before retrying/);
    assert.equal(attempts, 1);
  }
});
