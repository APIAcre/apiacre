# API Acre MCP buyer for Node.js

Run these commands in `examples/mcp-buyer` in the API Acre integration repository.
Use Node.js 24 or later. The first command installs the locked SDK versions.

```sh
npm ci --ignore-scripts
node buy.mjs
```

The default command quotes the current-weather example. It shows the request,
exact USDC amount and recipient on each offered network. It needs no wallet.

Choose a different MCP tool with `--tool`. To use your own request, pass a JSON
object in a local file. The script validates it against the tool's input schema.
The quote and any authorized call use the numeric literals from your file,
including integer IDs larger than JavaScript's safe integer range.

```sh
node buy.mjs --tool research.crossref-work-search
printf '%s\n' '{"country_code":"GBR","lookback_years":8}' > country.json
node buy.mjs --tool data.worldbank-snapshot --input country.json
```

These examples request unsigned quotes. Crossref Work Search costs 0.008 USDC
per call, and World Bank Country Snapshot costs 0.005 USDC per call. Both offer
exact USDC quotes on Base and Solana. The browser forms accept the same inputs
if you prefer to review them without installing SDKs.
[Crossref checkout](https://apiacre.com/try/research.crossref-work-search) ·
[World Bank checkout](https://apiacre.com/try/data.worldbank-snapshot).

## Approve one tool call

Use a local buyer wallet funded with native USDC on the network you select. Load
`APIACRE_BASE_PRIVATE_KEY` for a Base wallet or `APIACRE_SOLANA_PRIVATE_KEY` for
a Solana wallet through your local secret manager. The Base key is a `0x`-prefixed
private key. The Solana key is a base58-encoded 64-byte keypair. Keys stay in the
local process. Keep them out of command-line arguments and repository files.

Set `REVIEWED_USDC_RECIPIENT` to the recipient you verified for the selected
network in the [live x402 catalog](https://apiacre.com/.well-known/x402). This
example caps the weather purchase at 0.002 USDC. For Solana, use `--network solana`
and that network's recipient and wallet.

```sh
node buy.mjs --pay --network base --max-usdc 0.002 --pay-to "$REVIEWED_USDC_RECIPIENT"
```

The command reads a fresh quote and shows the exact tool, input, network, amount
and recipient. Type `PAY` at the prompt to authorize that call. A successful
response prints the settlement receipt and the tool result with exact numeric
values when API Acre includes matching JSON result text. If the response is
lost or the receipt differs from the reviewed call, check your wallet history
before trying again. The example sends one signed request per confirmation.

The local tests use throwaway signers, a fixture Solana RPC and mocked tool
responses. They check the spend limit, recipient, both signing paths and the
single submission after confirmation.

```sh
npm test
```

Use the [browser checkout](https://apiacre.com/try/data.current-weather) if you
prefer your wallet's approval prompt.
