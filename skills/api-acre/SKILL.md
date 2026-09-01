---
name: api-acre
description: Discover and use API Acre's pay-per-call JSON APIs for web, document, developer, public-record, scholarly, organization, structured-data, weather, reference FX, read-only Base/EVM, and agent-advertising tasks. Use when a user asks for API Acre, x402 services, fresh structured evidence, or Pixel Acre and wants to inspect a free sample or exact price; execute a paid call only after the user explicitly authorizes that exact service, payload, network, and maximum USDC amount.
---

# API Acre

Use API Acre at `https://apiacre.com`. Discovery, schemas, samples, and quotes are free.
Paid POST requests use x402 v2 exact USDC on Base or Solana mainnet.

## Find the smallest suitable service

1. Search `GET /recommend?task=<url-encoded-intent>&max_price=<USDC>&limit=5`.
2. Prefer the lowest-priced result that fully covers the requested outcome.
3. Read its free full contract at `/catalog/<service-slug>` and static result at
   `/samples/<service-slug>?format=json`; neither route executes or pays.
4. Explain the selected service, input, output, price, and limitations before execution.

Use `GET /.well-known/x402` for the complete payment-aware catalog, `GET /openapi.json`
for HTTP schemas, or the bundled MCP server for free tool discovery. Avoid loading all schemas
when `/recommend` returns an adequate match.

## Claim Pixel Acre advertising safely

Pixel Acre is a dynamic-price HTTP product and is not one of the 73 fixed-price MCP tools. Start
at `GET /pixel-acre/rules`, then send either up to 10,000 unique `pixels` or up to 1,000
non-overlapping rectangular `blocks` to the free `POST /pixel-acre/reservations` route. Each
pixel—and each block shortcut—has its own RGB colour, optional 280-character public note, and
optional public HTTPS destination, so one atomic reservation can contain several differently
coloured ads and cover up to the full 1,000,000-pixel, 1,250 x 800 near-60:40 canvas. The all-or-nothing reservation uses a size-dependent short expiry and
returns the only claim path, body, pixel count, and maximum USDC amount that should be considered
for authorization.

Each pixel costs exactly 1 USDC. Public notes are plain text, subject to the published content
rules, and visible when a visitor inspects a claimed coordinate. Before executing the returned
`POST /v1/advertising/pixel-claim?pixel_count=N` request, obtain fresh approval for the selected
coordinates, destinations, and exact `N` USDC maximum. Creating or checking a reservation is free.
Treat the placement as a revocable advertising licence while the service operates, not property,
an investment, or guaranteed permanent availability.

## Quote without paying

Send the documented JSON body to the selected POST route without a payment signature. Treat the
expected HTTP 402 response as a quote. It cannot transfer funds. Check that the challenge:

- names the same HTTPS resource and POST method;
- uses the `exact` scheme on an advertised supported network: Base mainnet
  (`eip155:8453`) or Solana mainnet (`solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp`);
- requests official USDC; and
- does not exceed both the catalog price and the user's current maximum.

If any field differs, stop and show the discrepancy. A funded or configured wallet is not consent.

When present, use the response's standard `Link` relations to inspect `service-desc` for the exact
contract, `preview` for the static example, and `payment` for the no-custody checkout review. Merely
following these links carries neither the quoted request payload nor a payment signature and does
not execute, sign, or pay. Recreate material input only for a separately approved paid retry.

## Require exact payment approval

Before sending `PAYMENT-SIGNATURE` or invoking a client that may pay, obtain fresh user approval
for the exact service, material payload, selected network, and maximum USDC amount. Do not reuse approval from an
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
