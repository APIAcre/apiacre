# API Acre

API Acre is a live catalog of 76 focused, pay-per-call HTTP products for web
research, documents, scholarly metadata, organization discovery, structured
data, developer workflows, public-company research, Base network evidence, and
agent advertising. The 75 fixed-price APIs are also available as MCP tools.
Each paid operation uses x402 v2 with exact USDC payment on Base or Solana;
discovery, schemas, examples, and workflow recipes are free.

This repository is the public integration and discovery hub. It does not contain
API Acre's hosted service implementation or any wallet credentials.

## Discover the APIs

- [Service catalog](https://apiacre.com/catalog) — prices, schemas, examples,
  checkout links, and exact-cap agent commands
- [OpenAPI document](https://apiacre.com/openapi.json) — all HTTP operations
- [First-party APIs.json index](https://apiacre.com/.well-known/apis.json) for
  the live OpenAPI contract, pricing catalog, buyer guide, and agent endpoints.
- [RFC 9727 API catalog](https://apiacre.com/.well-known/api-catalog) lists paid
  endpoints with a free contract and documentation for each.
- [x402 discovery](https://apiacre.com/.well-known/x402) — machine-readable
  payment resources
- [MCP discovery](https://apiacre.com/.well-known/mcp.json),
  [browse MCP tools](https://apiacre.com/mcp/tools), and
  [remote MCP connection guide](#connect-over-mcp)
- [A2A agent card](https://apiacre.com/.well-known/agent-card.json) and
  [free A2A discovery example](#discover-over-a2a)
- [Free result samples](https://apiacre.com/samples) and
  [multi-call workflows](https://apiacre.com/workflows)
- [Request custom work](https://apiacre.com/request-api) for a custom API,
  evidence audit, or volume integration.
- [Live Pixel Acre inventory](https://apiacre.com/pixel-acre/state) — claimed,
  reserved, checkout, and currently available pixels; reading it cannot reserve
  inventory or make a payment
- Free MCP resource templates let connected agents select a service, read its
  complete contract, and inspect its static result envelope before deciding
  whether to authorize a paid call
- [Free intent selector](https://apiacre.com/recommend?task=inspect%20an%20EVM%20address&max_price=0.002&limit=3)
  — compact, ranked choices without executing or paying for a service
- [Python standard-library example](#discover-from-python) for recommendations
  and live checkout links
- [Free code-metrics trial](https://apiacre.com/free-trial/developer.code-metrics)
  — one bounded live deterministic run per client per hour
- [Buyer guide](https://apiacre.com/buyers)
- [Base Python quickstart](#get-a-base-quote) for unpaid quotes on 75 fixed-price APIs
- [Solana Python quickstart](#get-a-solana-quote) for unpaid quotes on 75 fixed-price APIs
- [Crossref publication previews](#preview-crossref-publication-metadata) for searches and single-DOI records
- [Geocoding previews](#preview-geocoding) for global place names, coordinates, and U.S. street addresses
- [Technical SEO preview](#preview-a-technical-seo-audit) for single-page checks and page metadata
- [Base stock evidence preview](#preview-base-stock-evidence) for unpaid contract and SEC evidence quotes
- [CSV redaction and schema workflow](#preview-csv-redaction-and-schema-inference) for four editable checkout previews
- [Schema API price check](#preview-schema-prices-in-ci) for an unsigned GitHub Actions example
- [Agent integration guide](https://apiacre.com/integrations) — portable skill,
  plugin package, and connection instructions

## Discover from Python

Send a task and a USDC price cap to the free selector. The response includes a
checkout link for each recommendation. Discovery requires no wallet or payment.

```python
import json
from urllib.request import Request, urlopen

query = {"task": "read eth_getBlockByNumber on Base", "max_price": "0.001", "limit": 1}
request = Request(
    "https://apiacre.com/recommend",
    data=json.dumps(query).encode(),
    headers={
        "Content-Type": "application/json",
        "User-Agent": "APIAcre-python-discovery-example/1.0",
    },
)
with urlopen(request, timeout=10) as response:
    recommendations = json.load(response)["recommendations"]

for recommendation in recommendations:
    service = recommendation["service"]
    purchase = service["purchase"]
    print(f'{service["slug"]} ({purchase["exactAmount"]} USDC)')
    print(purchase["browserCheckoutUrl"])
```

Set a descriptive `User-Agent` for your application. Cloudflare can return
HTTP 403 with error 1010 for the default `urllib` header.
[Cloudflare error 1010](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)

## Discover over A2A

Ask the discovery agent to recommend an API. Its response includes the
input schema, sample link, and purchase instructions. Any paid call
requires separate authorization.

```bash
curl --fail-with-body --silent --show-error https://apiacre.com/a2a \
  --header 'Content-Type: application/json' \
  --header 'A2A-Version: 1.0' \
  --data '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "SendMessage",
    "params": {"message": {
      "messageId": "grant-search-example",
      "role": "ROLE_USER",
      "parts": [{"text": "Find an API to search NIH grant records"}]
    }}
  }'
```

Read `result.message.parts[1].data.recommendations` for the matching APIs.
The agent card advertises A2A 1.0 HTTP+JSON and JSON-RPC, plus JSON-RPC 0.3
for clients that use `message/send`.

## Institution and funding research — 30 October 2026

| Service | USDC per call | Free sample | Checkout |
|---|---:|---|---|
| [ROR institution and affiliation evidence](https://apiacre.com/catalog/research.ror-organization-search) | 0.003 | [View sample](https://apiacre.com/samples/research.ror-organization-search) | [Review request](https://apiacre.com/try/research.ror-organization-search) |
| [NIH research grant search](https://apiacre.com/catalog/research.nih-grant-search) | 0.005 | [View sample](https://apiacre.com/samples/research.nih-grant-search) | [Review request](https://apiacre.com/try/research.nih-grant-search) |

Resolve research-organization names, exact ROR IDs or affiliations, then inspect
NIH RePORTER administrative awards by topic, institution and fiscal year.
Both use free official data sources and return bounded records with retrieval
times and source hashes. NIH amounts are application/fiscal-year figures;
source matches do not establish cross-registry identity.

The [research-funding-landscape workflow](https://apiacre.com/workflows/research-funding-landscape)
totals 0.008 USDC across two separately authorized calls. Read the
[service guide](docs/SCHOLARLY_RESEARCH_SERVICES.md), free schemas and samples
before approving a purchase.

## Preview Crossref publication metadata

Search Crossref by title, author, citation, or DOI fragment. Once you have a
specific DOI, retrieve its publication record and any correction or retraction
links reported by Crossref. Both endpoints return bibliographic metadata.

| Task | USDC per call | Free sample | Checkout |
| --- | ---: | --- | --- |
| Find candidate publications and their DOIs | 0.008 | [Search sample](https://apiacre.com/samples/research.crossref-work-search) | [Work Search](https://apiacre.com/try/research.crossref-work-search) |
| Look up one known DOI | 0.003 | [DOI sample](https://apiacre.com/samples/research.crossref-doi-metadata) | [DOI Metadata](https://apiacre.com/try/research.crossref-doi-metadata) |

The two calls have a combined price of **0.011 USDC** on Base or Solana. Review
the search results and select a DOI before authorizing the second call.

## Preview geocoding

Choose the API based on the input you have. Each paid endpoint accepts `POST` and
quotes the same USDC price on Base and Solana. The sample links show a free JSON
response, and the checkout links let you edit the input before authorizing a call.

| Input you have | Result | USDC per call | Free sample | Checkout |
| --- | --- | ---: | --- | --- |
| Place name such as `London, GB` | Ranked cities or localities with coordinates | 0.002 | [Place sample](https://apiacre.com/samples/data.place-geocode) | [Place geocoding](https://apiacre.com/try/data.place-geocode) |
| Latitude `51.5074` and longitude `-0.1278` | Populated places ranked by distance from the point | 0.002 | [Reverse sample](https://apiacre.com/samples/data.reverse-geocode) | [Reverse geocoding](https://apiacre.com/try/data.reverse-geocode) |
| U.S. street address such as `4600 Silver Hill Rd, Washington, DC 20233` | Census coordinates with optional geography and source details | 0.005 | [Address sample](https://apiacre.com/samples/data.us-address-geocode) | [Street-address geocoding](https://apiacre.com/try/data.us-address-geocode) |

The [free street-address recommendation](https://apiacre.com/recommend?task=lookup%20a%20postal%20address&max_price=0.005&limit=1)
returns the address service and its checkout link at a **0.005 USDC** cap. A
[0.003 USDC cap](https://apiacre.com/recommend?task=lookup%20a%20postal%20address&max_price=0.003&limit=1)
returns an empty list for the same request.

## Preview a technical SEO audit

The technical SEO audit takes one public URL and returns a score and prioritized
issue codes for metadata, canonical and robots signals, headings, image alt text,
and structured data. The metadata endpoint returns page fields and source evidence
for integrations that need the underlying values.

| Task | USDC per call | Free sample | Checkout |
| --- | ---: | --- | --- |
| Get a technical SEO score and issues for one URL | 0.01 | [SEO audit sample](https://apiacre.com/samples/web.seo-audit) | [Technical SEO audit](https://apiacre.com/try/web.seo-audit) |
| Extract a page's title, canonical URL, and social tags | 0.002 | [Metadata sample](https://apiacre.com/samples/web.metadata) | [Webpage metadata](https://apiacre.com/try/web.metadata) |

Both endpoints accept `POST` and quote the listed price on Base and Solana.

## Preview Base stock evidence

Run the [Python 3.11+ example](examples/base-stock-evidence.py) to retrieve the
TSLAc contract address and preview two optional API Acre calls on Base. The
example needs only the Python standard library. It sends unsigned requests and
prints each request body, live quote, free sample link, and checkout link.

```bash
python3 examples/base-stock-evidence.py
```

- [Base contract read](https://apiacre.com/catalog/crypto.base-contract-read)
  reads the token's `decimals()` value. The example caps its quote at 0.005 USDC.
- [SEC company evidence](https://apiacre.com/catalog/research.sec-company-evidence)
  looks up TSLA issuer disclosures and financial evidence. Its quote cap is 0.02 USDC.

To review the exact request in a browser, open `browserCheckout.url` for either
service. Paste `browserCheckout.bodyJson` into **Change the request** and select
**Verify changed input** to get a fresh quote for that request.

Run `python3 examples/base-stock-evidence.py --agentcash` to print AgentCash
commands for a POSIX shell. `checkCommand` retrieves an unpaid quote for the
same request. AgentCash may initialize a local wallet on first use. Review the
quote before using `paidCommand`, which can spend USDC on Base up to the printed
quote amount. See the
[AgentCash CLI guide](https://github.com/Merit-Systems/agentcash-skills/tree/master/skills/agentcash).

The preview is free. Each optional paid call requires separate authorization,
with a combined cap of 0.025 USDC if you choose both. The source links identify
the [Base token metadata](https://docs.base.org/sdks/tokenized-stocks/api-reference/get-token-metadata)
and the [issuer's SEC filing](https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm).

## Preview CSV redaction and schema inference

The [CSV workflow](https://apiacre.com/workflows/csv-pii-contract) uses one
synthetic CSV across four checkout examples. Open any step to check its price
and review the request before authorizing it.

1. [Extract CSV text](https://apiacre.com/workflows/csv-pii-contract/start/1) · 0.010 USDC
2. [Redact sensitive patterns](https://apiacre.com/workflows/csv-pii-contract/start/2) · 0.010 USDC
3. [Profile the redacted rows](https://apiacre.com/workflows/csv-pii-contract/start/3) · 0.025 USDC
4. [Infer a schema from the redacted rows](https://apiacre.com/workflows/csv-pii-contract/start/4) · 0.025 USDC

All four steps cost **0.070 USDC** in total and require separate authorization.
For your own file, review the extracted text and the redaction findings, then
pass the reviewed redacted CSV into both the profiling and schema steps.
[Read the machine-readable recipe](https://apiacre.com/workflows/csv-pii-contract.json).

## Preview schema prices in CI

In a fork, open **Actions**, select **Preview schema API prices**, and choose
**Run workflow**. You can also run the same check locally with Python 3.11+.

```bash
python3 examples/schema-quote-preview.py
```

The check uses the published synthetic inputs for schema inference and JSON
Schema validation. The validation fixture pairs an integer field with a string
value so buyers can review how the free result sample reports a type mismatch.
The workflow compares the catalog with live unsigned Base quotes and puts both
prices, free samples, and exact-request checkout links in the job summary.
[View the workflow](.github/workflows/schema-quote-preview.yml).

The two optional purchases cost up to 0.035 USDC combined. Each requires
separate authorization through its checkout. The example uses the Python
standard library and needs no API key or wallet.

## Pricing update — 25 October 2026

The standard x402 USDC prices for these services are now:

| Service | USDC per call |
|---|---:|
| [SEC company evidence](https://apiacre.com/catalog/research.sec-company-evidence) | 0.02 |
| [Current weather](https://apiacre.com/catalog/data.current-weather) | 0.002 |
| [IANA timezone conversion](https://apiacre.com/catalog/data.timezone-convert) | 0.002 |

HTTP and MCP execution use the same prices. Read a fresh quote before paying;
an older listing or quote does not authorize an increase to your spending cap.
The [live catalogue](https://apiacre.com/catalog) lists every current price.

## Verified Production Use

Through 22 November 2026 at 21:00 UTC, API Acre's production ledger recorded
at least **383 independently attributed settled calls from 63 payers**,
totaling **1.747 USDC on Base** across 47 services. These totals exclude
operator validation.

These are privacy-bounded historical minimums, not buyer endorsements, evidence
of per-service unique payers, a repeat-demand claim, a forecast, or a guarantee.
No payer records or settlement identifiers are published. Inspect the current
[machine-readable aggregate](https://apiacre.com/catalog) or the
[customer-evidenced service collection](https://apiacre.com/use-cases#customer-evidenced).

## Claim a Piece of Pixel Acre

[Pixel Acre](https://apiacre.com/pixel-acre) is a public 1,250 × 800
near-60:40 advertising canvas built for agents. Its exactly one million square
coordinates each cost **1 USDC** and can carry a colour, an optional public note
of up to 280 characters, and an optional sponsored HTTPS destination. Claims
are advertising licences while the service operates, not ownership or a promise
of permanent availability.

Agents and x402 providers can link a placement directly to a paid API, checkout,
or machine-readable catalog. One atomic reservation may combine multiple
non-overlapping blocks, each with its own colour, note, and destination, or cover
every available coordinate up to the full one-million-pixel canvas. The live
landscape canvas includes grid guides, exact-coordinate inspection, and a
maximize control. Larger blocks are more visible and leave more room for a legible
creative, but placement does not guarantee traffic or revenue.

The flow is deliberately reservation-first: create a free, size-dependent
short-lived reservation, inspect its exact claim body and maximum spend, then
authorize the matching x402 request. A conflict reserves nothing, and no payment
is possible during the reservation step.

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

The current public package is version `1.5.1`. It can use Coinbase Agentic
Wallet MCP as an optional, separately installed buyer companion; signing in,
funding a wallet, or configuring spending limits never authorizes an API Acre
call by itself.

## Read a Quote Without Paying

An unsigned request returns HTTP `402` with the exact price, supported Base and
Solana network choices, official USDC asset, recipient, and resource metadata.
It cannot transfer funds:

```bash
curl -i https://apiacre.com/v1/developer/code-metrics \
  -X POST \
  -H 'content-type: application/json' \
  -d '{"code":"def greet(name):\n    return name","language":"python"}'
```

The 402 response also links to the selected service's free full contract,
static sample, and no-custody checkout review. Following those links carries
neither the request payload nor a payment signature and does not execute or pay.

### Preview a quote with AgentCash

This command checks the live price and recipient for a schema inference request
without paying. AgentCash may initialize a local wallet on first use.
`npx --yes` approves installing the AgentCash CLI.

```bash
npx --yes agentcash@0.17.1 check https://apiacre.com/v1/data/schema \
  --method POST \
  --header 'content-type: application/json' \
  --body '{"content":"[{\"name\":\"Ada\",\"score\":98}]","format":"json","root_mode":"records"}'
```

The [schema inference contract](https://apiacre.com/catalog/data.schema) links
to a free sample and provides exact-cap payment commands if you choose to buy.
The [browser checkout](https://apiacre.com/try/data.schema) lets you copy the
unpaid quote command and the capped payment command separately. The
[downloadable shell example](https://apiacre.com/examples/agentcash-buyer.sh)
checks the quote by default and requires an explicit `pay` argument to purchase.

To buy a result, use the service's browser checkout or a compatible x402 client
and enforce the amount published in the catalog. Every follow-up call is optional
and requires separate authorization; API Acre does not silently chain spending.

## Connect over MCP

Use `https://apiacre.com/mcp` as a Streamable HTTP MCP server. Tool discovery,
workflow recipes, task-to-service recommendations, complete single-service
contracts, static result samples, and live Pixel Acre inventory are free.
Individual tool execution advertises its own x402 requirement at call time;
reading the advertising inventory neither reserves pixels nor authorizes a claim.

Copy the server URL into your MCP client's connection settings. It is a protocol
endpoint, not a webpage: MCP clients send JSON-RPC `POST` requests. Opening
`https://apiacre.com/mcp` directly in a browser sends `GET` and returns
**405 Method Not Allowed** (`Allow: POST`), because this server does not offer a
standalone SSE stream. That response is expected; it does not mean the MCP server
is missing. For browser-readable JSON, use [MCP discovery](https://apiacre.com/.well-known/mcp.json)
or [the tool catalog](https://apiacre.com/mcp/tools).

```json
{
  "mcpServers": {
    "apiacre": {
      "url": "https://apiacre.com/mcp"
    }
  }
}
```

To check the connection without a wallet or payment, send an initialization
request using the supported `2025-06-18` protocol:

```bash
curl -i https://apiacre.com/mcp \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"connection-check","version":"1.0"}}}'
```

A working connection returns HTTP `200` with `result.serverInfo` and the
negotiated protocol version. This request only reads server capabilities; it
does not execute a paid tool. Use an MCP client for subsequent tool discovery
and calls. Current protocol support is also published in the
[discovery document](https://apiacre.com/.well-known/mcp.json).

## Get a Base quote

Save the [SEC Filing Signals example](https://apiacre.com/examples/python-buyer.py)
as `python-buyer.py`. Its default run shows the live recipient and the 0.05 USDC
quote on Base mainnet.

```sh
python3 -m pip install "x402[httpx,evm]>=2.29,<2.30"
python3 python-buyer.py
```

Choose **Use Python on Base** on any fixed-price service page or checkout. For
example, the [Code Metrics script](https://apiacre.com/examples/python-buyer.py?service=developer.code-metrics)
quotes 0.025 USDC per call. Agents can find each download under
`purchase.basePythonExampleUrl` in the [x402 discovery document](https://apiacre.com/.well-known/x402).

Pass `--input request.json` to quote your own JSON, or use `--input -` to read
a JSON object from standard input. Quoting requires no wallet. See the
[buyer guide](https://apiacre.com/buyers) to authorize a paid call separately.

## Get a Solana quote

[Download the Python example](https://apiacre.com/examples/python-solana-buyer.py)
to check the live quote for timezone conversion on Solana mainnet. The default
run displays the recipient and the 0.002 USDC price.

```sh
python3 -m pip install "x402[httpx,svm]>=2.29,<2.30"
python3 python-solana-buyer.py
```

Open a fixed-price API from the [service catalog](https://apiacre.com/catalog)
and choose **Use Python on Solana** on the service page or in browser checkout.
The full [x402 discovery document](https://apiacre.com/.well-known/x402) lists the
same links under `purchase.solanaPythonExampleUrl`.

| API | Exact price per call | Python example |
| --- | ---: | --- |
| Code Metrics | 0.025 USDC | [Open example](https://apiacre.com/examples/python-solana-buyer.py?service=developer.code-metrics) |
| U.S. Address Geocode | 0.005 USDC | [Open example](https://apiacre.com/examples/python-solana-buyer.py?service=data.us-address-geocode) |

Each example checks the live Solana quote with its bundled request by default.
To quote your own request, save its JSON to `request.json` and run the downloaded
script with `--input request.json`. Pass `--input -` to read a JSON object
from standard input.
The [buyer guide](https://apiacre.com/buyers) explains how to authorize one paid
call after checking the quote.

## Rookfall: Lastlight Bastion

[Play Lastlight Bastion](https://apiacre.com/arcade/rookfall?mode=defense),
a free cooperative tower defense mode for one to four players. Defend two relay
towers through eight waves on a dedicated coastal fortress map, ending with a
siege engine.

Build autocannons, chain lightning pylons, mortars and cryo projectors, plus walls
and support relays. Upgrade and repair defenses using shared scrap. Quick Play
joins a public squad; private room codes let friends play together.

Play in a browser without a wallet or payment. [Browse the arcade](https://apiacre.com/arcade).

## Network and Safety

- Networks: Base mainnet (`eip155:8453`) and Solana mainnet
  (`solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp`)
- Asset: official native USDC
- Payment model: exact listed price per authorized call; no account or subscription
- Wallet keys: never requested by API Acre
- Public evidence services: factual signals, not identity, ownership, investment,
  legal, or compliance verdicts

Questions and integration requests: [hello@apiacre.com](mailto:hello@apiacre.com)
