import { readFile } from "node:fs/promises";
import { stdin, stderr } from "node:process";
import { createInterface } from "node:readline/promises";
import { isDeepStrictEqual, parseArgs } from "node:util";

import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { AjvJsonSchemaValidator } from "@modelcontextprotocol/sdk/validation/ajv";
import { x402Client } from "@x402/core/client";
import { attachPaymentToMeta, createx402MCPClient, extractPaymentResponseFromMeta } from "@x402/mcp";

const endpoint = "https://apiacre.com/mcp";
const rails = {
  base: { network: "eip155:8453", asset: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913" },
  solana: { network: "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp", asset: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" },
};

function sameAddress(rail, left, right) {
  if (typeof left !== "string" || typeof right !== "string") return false;
  return rail === "base" ? left.toLowerCase() === right.toLowerCase() : left === right;
}

function formatUsdc(amount) {
  const digits = amount.padStart(7, "0");
  const fractional = digits.slice(-6).replace(/0+$/, "");
  return fractional ? `${digits.slice(0, -6)}.${fractional}` : digits.slice(0, -6);
}

export function parseExactJson(text) {
  return JSON.parse(text, (_key, value, { source }) =>
    typeof value === "number" && JSON.stringify(value) !== source ? JSON.rawJSON(source) : value);
}

function toolResult(result) {
  const { content, structuredContent } = result;
  const [item] = content;
  if (structuredContent !== undefined && content.length === 1 && item.type === "text") {
    try {
      // API Acre includes the same result as JSON text, which retains exact numeric literals.
      if (isDeepStrictEqual(JSON.parse(item.text), structuredContent)) return parseExactJson(item.text);
    } catch (error) {
      if (!(error instanceof SyntaxError)) throw error;
    }
  }
  return structuredContent ?? content;
}

export function exactOffers(tool, quote) {
  if (quote?.x402Version !== 2 || quote.resource?.url !== `mcp://tool/${tool}` || !Array.isArray(quote.accepts)) {
    throw new Error(`Expected an x402 v2 quote for ${tool}`);
  }
  return Object.entries(rails).flatMap(([rail, { network, asset }]) => {
    const matches = quote.accepts.filter((offer) => offer?.network === network);
    if (matches.length === 0) return [];
    const [offer] = matches;
    const addressPattern = rail === "base" ? /^0x[\da-f]{40}$/i : /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
    const transferMethod = offer.extra?.assetTransferMethod ?? "eip3009";
    if (matches.length !== 1 || offer.scheme !== "exact" || !sameAddress(rail, offer.asset, asset) ||
        typeof offer.amount !== "string" || !/^[1-9]\d*$/.test(offer.amount) ||
        typeof offer.payTo !== "string" || !addressPattern.test(offer.payTo) ||
        (rail === "base" && transferMethod !== "eip3009")) {
      throw new Error(`Unexpected ${rail} payment terms for ${tool}`);
    }
    return [{ rail, offer }];
  });
}

export function selectOffer(offers, { network, "max-usdc": maxUsdc, "pay-to": recipient }) {
  if (!/^(?:0|[1-9]\d*)(?:\.\d{1,6})?$/.test(maxUsdc ?? "")) {
    throw new Error("Set --max-usdc to a decimal with up to six fractional digits");
  }
  const [whole, fraction = ""] = maxUsdc.split(".");
  const limit = BigInt(whole) * 1_000_000n + BigInt(fraction.padEnd(6, "0"));
  const selected = offers.find(({ rail }) => rail === network)?.offer;
  if (!selected) throw new Error("Choose an offered network with --network base or --network solana");
  if (BigInt(selected.amount) > limit) throw new Error("The quoted price exceeds --max-usdc");
  if (!sameAddress(network, selected.payTo, recipient)) throw new Error("The quote and --pay-to differ");
  return selected;
}

async function localScheme(network) {
  if (network === "base") {
    const [{ privateKeyToAccount }, { ExactEvmScheme }] = await Promise.all([
      import("viem/accounts"), import("@x402/evm/exact/client"),
    ]);
    try {
      return new ExactEvmScheme(privateKeyToAccount(process.env.APIACRE_BASE_PRIVATE_KEY));
    } catch {
      throw new Error("Set APIACRE_BASE_PRIVATE_KEY to a local buyer wallet's 0x-prefixed private key");
    }
  }
  const [{ createKeyPairSignerFromBytes }, { base58 }, { ExactSvmScheme }] = await Promise.all([
    import("@solana/kit"), import("@scure/base"), import("@x402/svm/exact/client"),
  ]);
  try {
    const signer = await createKeyPairSignerFromBytes(base58.decode(process.env.APIACRE_SOLANA_PRIVATE_KEY));
    return new ExactSvmScheme(signer);
  } catch {
    throw new Error("Set APIACRE_SOLANA_PRIVATE_KEY to a local buyer wallet's base58-encoded keypair");
  }
}

export async function purchaseOnce(mcp, tool, input, quote, selected, scheme) {
  const payer = new x402Client().register(selected.network, scheme);
  const payload = await payer.createPaymentPayload({ ...quote, accepts: [selected] });
  if (payload.resource?.url !== `mcp://tool/${tool}` ||
      ["network", "asset", "amount", "payTo", "scheme"].some((field) => payload.accepted?.[field] !== selected[field])) {
    throw new Error("The signed payload changed the reviewed payment terms");
  }
  let result;
  try {
    result = await mcp.callTool(attachPaymentToMeta({ name: tool, arguments: input }, payload));
  } catch {
    throw new Error("The payment outcome is unknown. Check your wallet history before retrying");
  }
  const receipt = extractPaymentResponseFromMeta(result);
  if (receipt?.success !== true || receipt.network !== selected.network ||
      typeof receipt.transaction !== "string" || !receipt.transaction ||
      (receipt.amount !== undefined && receipt.amount !== selected.amount)) {
    throw new Error("No matching settlement receipt was returned. Check your wallet history before retrying");
  }
  return { receipt, result: toolResult(result), toolError: result.isError === true };
}

async function main() {
  const { values } = parseArgs({ options: {
    tool: { type: "string", default: "data.current-weather" },
    input: { type: "string" },
    pay: { type: "boolean" },
    network: { type: "string" },
    "max-usdc": { type: "string" },
    "pay-to": { type: "string" },
  } });
  if (values.pay && (!stdin.isTTY || !stderr.isTTY)) throw new Error("Use an interactive terminal to approve payment");

  const client = createx402MCPClient({
    name: "apiacre-mcp-buyer", version: "1.0.0", schemes: [], autoPayment: false,
  });
  const transport = new StreamableHTTPClientTransport(new URL(endpoint), {
    requestInit: { redirect: "error", headers: { "User-Agent": "APIAcre-x402-MCP-Buyer/1.0" } },
  });
  try {
    await client.connect(transport);
    const { tools } = await client.listTools();
    const tool = tools.find(({ name }) => name === values.tool);
    if (!tool) throw new Error(`Unknown API Acre MCP tool ${values.tool}`);
    const inputText = values.input ? await readFile(values.input, "utf8") : undefined;
    const input = inputText === undefined ? tool.inputSchema.examples?.[0] : JSON.parse(inputText);
    if (!input || typeof input !== "object" || Array.isArray(input)) throw new Error("Supply a JSON object with --input FILE");
    const validate = new AjvJsonSchemaValidator().getValidator(tool.inputSchema);
    const validation = validate(input);
    if (!validation.valid) throw new Error(`The input for ${tool.name} is invalid. ${validation.errorMessage}`);
    const request = inputText === undefined ? input : parseExactJson(inputText);

    const quote = await client.getToolPaymentRequirements(tool.name, request);
    const offers = exactOffers(tool.name, quote);
    if (offers.length === 0) throw new Error("No supported USDC network was offered");
    if (!values.pay) {
      console.log(JSON.stringify({ tool: tool.name, input: request, offers: offers.map(({ rail, offer }) => ({
        rail, network: offer.network, amountUsdc: formatUsdc(offer.amount), recipient: offer.payTo,
      })) }, null, 2));
      return;
    }

    const selected = selectOffer(offers, values);
    const prompt = createInterface({ input: stdin, output: stderr });
    let answer;
    try {
      stderr.write(`${JSON.stringify(request, null, 2)}\n`);
      answer = await prompt.question(`Pay ${formatUsdc(selected.amount)} USDC on ${values.network} to ${selected.payTo} for ${tool.name}? Type PAY to sign once: `);
    } finally {
      prompt.close();
    }
    if (answer !== "PAY") return;

    const scheme = await localScheme(values.network);
    const result = await purchaseOnce(client.client, tool.name, request, quote, selected, scheme);
    console.log(JSON.stringify(result, null, 2));
    if (result.toolError) process.exitCode = 1;
  } finally {
    await client.close();
  }
}

if (import.meta.main) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
