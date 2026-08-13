# API Acre

API Acre is a live catalog of 59 focused, pay-per-call APIs for web research,
documents, structured data, developer workflows, public-company research, and
Base network evidence. Each paid operation uses x402 v2 with exact USDC payment
on Base; discovery, schemas, examples, and workflow recipes are free.

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
- [Buyer guide](https://apiacre.com/buyers)
- [Agent integration guide](https://apiacre.com/integrations) — portable skill,
  plugin package, and connection instructions

## Install the Agent Skill

The repository contains an instruction-only Agent Skill at
[`skills/api-acre/SKILL.md`](skills/api-acre/SKILL.md). Review it before
installing, then copy the complete `skills/api-acre` directory into your
agent host's skill directory. The same version is published with a checksum at
[`https://apiacre.com/integrations.json`](https://apiacre.com/integrations.json).

For Codex-compatible hosts, this repository also includes a plugin manifest and
remote MCP configuration. No wallet or API credential is bundled. Installing the
skill permits free discovery and quote checks; it does not authorize payment.

## Read a Quote Without Paying

An unsigned request returns HTTP `402` with the exact price, Base network,
official USDC asset, recipient, and resource metadata. It cannot transfer funds:

```bash
curl -i https://apiacre.com/v1/developer/code-metrics \
  -X POST \
  -H 'content-type: application/json' \
  -d '{"code":"def greet(name):\n    return name","language":"python"}'
```

To buy a result, use the service's browser checkout or a compatible x402 client
and enforce the amount published in the catalog. Every follow-up call is optional
and requires separate authorization; API Acre does not silently chain spending.

## Connect over MCP

Use `https://apiacre.com/mcp` as a Streamable HTTP MCP server. Tool discovery and
the workflow resource are free. Individual tool execution advertises its own
x402 requirement at call time.

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
