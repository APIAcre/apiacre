---
name: api-acre
description: Discover and use API Acre's pay-per-call JSON APIs for web, document, developer, public-record, structured-data, weather, and read-only Base/EVM tasks. Use when a user asks for API Acre, x402 services, or fresh structured evidence and wants to inspect a free sample or exact price; execute a paid call only after the user explicitly authorizes that exact service, payload, and maximum USDC amount.
---

# API Acre

Use API Acre at `https://apiacre.com`. Discovery, schemas, samples, and quotes are free.
Paid POST requests use x402 v2 exact USDC on Base mainnet.

## Find the smallest suitable service

1. Search `GET /recommend?task=<url-encoded-intent>&max_price=<USDC>&limit=5`.
2. Prefer the lowest-priced result that fully covers the requested outcome.
3. Read its free full contract at `/catalog/<service-slug>` and static result at
   `/samples/<service-slug>?format=json`; neither route executes or pays.
4. Explain the selected service, input, output, price, and limitations before execution.

Use `GET /.well-known/x402` for the complete payment-aware catalog, `GET /openapi.json`
for HTTP schemas, or the bundled MCP server for free tool discovery. Avoid loading all schemas
when `/recommend` returns an adequate match.

## Quote without paying

Send the documented JSON body to the selected POST route without a payment signature. Treat the
expected HTTP 402 response as a quote. It cannot transfer funds. Check that the challenge:

- names the same HTTPS resource and POST method;
- uses the `exact` scheme on Base mainnet (`eip155:8453`);
- requests official USDC; and
- does not exceed both the catalog price and the user's current maximum.

If any field differs, stop and show the discrepancy. A funded or configured wallet is not consent.

When present, use the response's standard `Link` relations to inspect `service-desc` for the exact
contract, `preview` for the static example, and `payment` for the no-custody checkout review. Merely
following these links carries neither the quoted request payload nor a payment signature and does
not execute, sign, or pay. Recreate material input only for a separately approved paid retry.

## Require exact payment approval

Before sending `PAYMENT-SIGNATURE` or invoking a client that may pay, obtain fresh user approval
for the exact service, material payload, and maximum USDC amount. Do not reuse approval from an
earlier call, test, batch, wallet funding, or similar service. Do not approve on the user's behalf.

Treat every `next_action` as optional and separately paid. Ask again before each one. When approval
is absent, return the sample, schema, or quote and stop.

## Execute and report

Use an x402 v2 client with the approved maximum. Keep private keys in the buyer's local wallet;
never send seed phrases, private keys, authentication tokens, or unrelated confidential data to
API Acre. Use a unique `Idempotency-Key` when retrying the same paid request, and do not pay twice
after an ambiguous network result until settlement status is checked.

If Coinbase Agentic Wallet MCP is available, use its requirement-checking action before approval;
that check does not pay. Use its x402 request action only after fresh approval for the selected
API Acre service, material payload, and exact maximum. A signed-in or funded wallet and its stored
spending limits are safeguards, not consent for the current call.

Return the structured result, service name, actual price, source/evidence limitations, and
settlement transaction when available. Do not present factual signals as legal, identity,
ownership, compliance, or investment verdicts.

## Connection options

- Remote MCP: `https://apiacre.com/mcp` (Streamable HTTP). Listing tools and reading its
  recommendation, full-contract, sample, and workflow resources are free; a tool call may return
  an x402 requirement and still needs exact approval.
- Optional Coinbase Agentic Wallet MCP buyer: `npx @coinbase/payments-mcp`. Running this separate
  installer executes a Coinbase package; sign-in, funding, and wallet limits remain buyer-owned
  steps. Installation alone does not pay or authorize a call.
- HTTP: `https://apiacre.com/openapi.json` and `https://apiacre.com/buyers`.
- Custom volume or integration request: `https://apiacre.com/request-api`. Drafting a request is
  free and does not create an order.
