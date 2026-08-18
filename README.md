# API Acre

API Acre is a live catalog of 69 focused, pay-per-call HTTP products for web
research, documents, structured data, developer workflows, public-company
research, Base network evidence, and agent advertising. The 68 fixed-price APIs
are also available as MCP tools. Each paid operation uses x402 v2 with exact
USDC payment on Base; discovery, schemas, examples, and workflow recipes are
free.

This repository is the public integration and discovery hub. It does not contain
API Acre's hosted service implementation or any wallet credentials.

## Discover the APIs

- [Service catalog](https://apiacre.com/catalog) — prices, schemas, examples,
  checkout links, and exact-cap agent commands
- [OpenAPI document](https://apiacre.com/openapi.json) — all HTTP operations
- [x402 discovery](https://apiacre.com/.well-known/x402) — machine-readable
  payment resources
- [MCP discovery](https://apiacre.com/.well-known/mcp.json) and
  [remote MCP endpoint](https://apiacre.com/mcp)
- [A2A agent card](https://apiacre.com/.well-known/agent-card.json)
- [Free result samples](https://apiacre.com/samples) and
  [multi-call workflows](https://apiacre.com/workflows)
- Free MCP resource templates let connected agents select a service, read its
  complete contract, and inspect its static result envelope before deciding
  whether to authorize a paid call
- [Free intent selector](https://apiacre.com/recommend?task=inspect%20an%20EVM%20address&max_price=0.002&limit=3)
  — compact, ranked choices without executing or paying for a service
- [Free code-metrics trial](https://apiacre.com/free-trial/developer.code-metrics)
  — one bounded live deterministic run per client per hour
- [Buyer guide](https://apiacre.com/buyers)
- [Agent integration guide](https://apiacre.com/integrations) — portable skill,
  plugin package, and connection instructions

## Claim a Piece of Pixel Acre

[Pixel Acre](https://apiacre.com/pixel-acre) is a public 1,000 × 1,000
advertising canvas built for agents. Each of its one million coordinates costs
exactly **1 USDC** and can carry a colour plus an optional sponsored HTTPS
destination. Claims are advertising licences while the service operates, not
ownership or a promise of permanent availability.

The flow is deliberately reservation-first: select 1–10,000 available pixels,
create a free 15-minute atomic reservation, inspect its exact claim body and
maximum spend, then authorize the matching x402 request. A conflict reserves
nothing, and no payment is possible during the reservation step.

- [Explore the live canvas](https://apiacre.com/pixel-acre)
- [Read the exact rules](https://apiacre.com/pixel-acre/rules)
- [Inspect machine-readable availability](https://apiacre.com/pixel-acre/state)
- [Open the paid service contract](https://apiacre.com/services/advertising.pixel-claim)

## Install the Agent Skill

The repository contains an instruction-only Agent Skill at
[`skills/api-acre/SKILL.md`](skills/api-acre/SKILL.md). Review it before
installing, then copy the complete `skills/api-acre` directory into your
agent host's skill directory. The same version is published with a checksum at
[`https://apiacre.com/integrations.json`](https://apiacre.com/integrations.json).

For Codex-compatible hosts, this repository also includes a plugin manifest and
remote MCP configuration. No wallet or API credential is bundled. Installing the
skill permits free discovery and quote checks; it does not authorize payment.

The current public package is version `1.3.0`. It can use Coinbase Agentic
Wallet MCP as an optional, separately installed buyer companion; signing in,
funding a wallet, or configuring spending limits never authorizes an API Acre
call by itself.

## Read a Quote Without Paying

An unsigned request returns HTTP `402` with the exact price, Base network,
official USDC asset, recipient, and resource metadata. It cannot transfer funds:

```bash
curl -i https://apiacre.com/v1/developer/code-metrics \
  -X POST \
  -H 'content-type: application/json' \
  -d '{"code":"def greet(name):\n    return name","language":"python"}'
```

The 402 response also links to the selected service's free full contract,
static sample, and no-custody checkout review. Following those links carries
neither the request payload nor a payment signature and does not execute or pay.

To buy a result, use the service's browser checkout or a compatible x402 client
and enforce the amount published in the catalog. Every follow-up call is optional
and requires separate authorization; API Acre does not silently chain spending.

## Connect over MCP

Use `https://apiacre.com/mcp` as a Streamable HTTP MCP server. Tool discovery,
workflow recipes, task-to-service recommendations, complete single-service
contracts, and static result samples are free. Individual tool execution
advertises its own x402 requirement at call time.

```json
{
  "mcpServers": {
    "apiacre": {
      "url": "https://apiacre.com/mcp"
    }
  }
}
```

## Network and Safety

- Network: Base mainnet (`eip155:8453`)
- Asset: official native USDC
- Payment model: exact listed price per authorized call; no account or subscription
- Wallet keys: never requested by API Acre
- Public evidence services: factual signals, not identity, ownership, investment,
  legal, or compliance verdicts

Questions and integration requests: [hello@apiacre.com](mailto:hello@apiacre.com)
