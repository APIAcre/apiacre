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
- [Node.js MCP quote example](#read-an-mcp-quote-from-nodejs) for an unsigned
  price check with the x402 SDK
- [Node.js MCP buyer](examples/mcp-buyer/) to quote any API Acre MCP tool and
  approve a single call on Base or Solana
- [A2A agent card](https://apiacre.com/.well-known/agent-card.json) and
  [free A2A discovery example](#discover-over-a2a)
- [Free result samples](https://apiacre.com/samples) and
  [multi-call workflows](https://apiacre.com/workflows)
- [Prepare a custom-work brief](https://apiacre.com/request-api#request-builder)
  for a custom API, evidence audit, or volume integration. Describe the
  deliverable, timeline, and optional budget, then review the draft before
  sending it. [View a completed commission](https://apiacre.com/request-api#proof-case).
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
- [Browser quote example](#check-a-quote-from-your-web-app) for apps on a different origin
- [Base Python quickstart](#get-a-base-quote) for unpaid quotes on 75 fixed-price APIs
- [Solana Python quickstart](#get-a-solana-quote) for unpaid quotes on 75 fixed-price APIs
- [Use reviewed checkout JSON in Python](#use-reviewed-checkout-json-in-python) to quote the same request from your terminal
- [Country and company evidence](#preview-country-and-company-evidence) for World Bank indicators and SEC filings
- [Crossref publication previews](#preview-crossref-publication-metadata) for searches and single-DOI records
- [Geocoding previews](#preview-geocoding) for global place names, coordinates, and U.S. street addresses
- [Time-zone quote preview](#preview-a-time-zone-conversion) for ISO 8601 timestamps and repeated local times
- [Weather quote previews](#preview-weather) for current conditions and forecasts by place or coordinates
- [ECB FX quote preview](#preview-an-ecb-fx-conversion) for currency pairs, amounts, and historical dates
- [Web extraction previews](#preview-web-extraction) for plain text or Markdown from one URL
- [Technical SEO preview](#preview-a-technical-seo-audit) for single-page checks and page metadata
- [Base gas fee and history previews](#preview-base-gas-fees-and-fee-history) with a selected block window
- [Base account balance previews](#preview-base-account-balances) for native balances and selected ERC-20 contracts
- [Base stock evidence preview](#preview-base-stock-evidence) for unpaid contract and SEC evidence quotes
- [CSV redaction and schema workflow](#preview-csv-redaction-and-schema-inference) for four editable checkout previews
- [Schema API price check](#preview-schema-prices-in-ci) for an unsigned GitHub Actions example
- [Install the Agent Skill](#install-the-agent-skill) in a Codex project
- [Install in Claude Code](#install-in-claude-code) for the API Acre skill and remote MCP connection
- [Agent integration guide](https://apiacre.com/integrations) — portable skill,
  plugin package, and connection instructions

## Discover from Python

Send a task and a USDC price cap to the free selector. The response includes a
checkout link for each service and a recipe link for each workflow. Discovery
requires no wallet or payment.

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
    result = json.load(response)

for recommendation in result["recommendations"]:
    service = recommendation["service"]
    purchase = service["purchase"]
    print(f'{service["slug"]} ({purchase["exactAmount"]} USDC)')
    print(purchase["browserCheckoutUrl"])

for recommendation in result["workflowRecommendations"]:
    workflow = recommendation["workflow"]
    print(f'{workflow["id"]} ({workflow["totalPrice"]} total)')
    print(workflow["documentationUrl"])
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

Use `maxPrice` in a JSON data part to set an inclusive per-call USDC cap.
This works for both task recommendations and exact service lookups.

```json
{"data": {"service": "data.timezone-convert", "maxPrice": "0.002"}}
```

For a text request, end with a phrase like `for 0.002 USDC or less`.

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

## Preview country and company evidence

The [World Bank checkout](https://apiacre.com/try/data.worldbank-snapshot)
accepts one country name or code, such as `Canada` or `GBR`, and a window of
3 to 20 calendar years. Select **Verify request quote** to review the country
code and **0.005 USDC** price before authorizing a payment.

Search for `Show World Bank GDP and population for Japan over the last 5 years` to
prepare `{"country_code":"JPN","lookback_years":5}` in HTTP, MCP, and A2A
discovery. **Review your World Bank snapshot** opens the same request in browser
checkout. The snapshot covers six fixed indicators including GDP, GDP growth,
population, inflation, unemployment, and life expectancy. Each result includes
source links, observation years, and missing-data notes.
[Free recommendation](https://apiacre.com/recommend?task=Show%20World%20Bank%20GDP%20and%20population%20for%20Japan%20over%20the%20last%205%20years&max_price=0.005&limit=1) · [World Bank result sample](https://apiacre.com/samples/data.worldbank-snapshot)

For company filings, search for `Show SEC 10-K filings for ticker AAPL` and select
**Review your SEC company request**. Checkout shows the ticker, 10-K filing
filter, and **0.02 USDC** price. You can also ask
`What has Apple Inc. filed with the SEC?` or supply one exact SEC CIK.

A form filter applies to the filing-activity section. The evidence report
also includes financial facts and Form 4 insider disclosures. HTTP, MCP, and
A2A discovery expose the same ticker and form filter through `suggestedInput`.
[Free recommendation](https://apiacre.com/recommend?task=Show%20SEC%2010-K%20filings%20for%20ticker%20AAPL&max_price=0.02&limit=1) · [SEC result sample](https://apiacre.com/samples/research.sec-company-evidence)

## Preview Crossref publication metadata

Search Crossref by title, author, citation, or DOI fragment. Once you have a
specific DOI, retrieve its publication record and any correction or retraction
links reported by Crossref. Both endpoints return bibliographic metadata.

| Task | USDC per call | Free sample | Checkout |
| --- | ---: | --- | --- |
| Find candidate publications and their DOIs | 0.008 | [Search sample](https://apiacre.com/samples/research.crossref-work-search) | [Work Search](https://apiacre.com/try/research.crossref-work-search) |
| Look up one known DOI | 0.003 | [DOI sample](https://apiacre.com/samples/research.crossref-doi-metadata) | [DOI Metadata](https://apiacre.com/try/research.crossref-doi-metadata) |

In Work Search, enter a title, author, DOI fragment, or citation. You can set
publication dates, work type, result count, and sorting. Select **Verify request
quote** after editing. Use **Edit the exact JSON request** if you want to review
or paste the raw input.

To start from the [API Acre homepage](https://apiacre.com/), enter
`Find academic papers on renewable energy storage` or
`Get DOI metadata for 10.1126/science.169.3946.635`. Select **Find APIs for this
task**, then **Review your Crossref request**. The quote shows the exact input
and per-call price before payment authorization.

Try `Find 5 recent journal articles on lithium-ion battery recycling from 2022 to 2025`
to prefill the topic, article type, result limit, newest-first sorting, and
inclusive publication dates. The
[free recommendation](https://apiacre.com/recommend?task=Find%205%20recent%20journal%20articles%20on%20lithium-ion%20battery%20recycling%20from%202022%20to%202025&max_price=0.008&limit=1)
returns the same fields in `suggestedInput`. Crossref results contain publication
metadata. Confirm peer-review status with the publisher.

The free [title recommendation](https://apiacre.com/recommend?task=Search+Crossref+for+%22Attention+Is+All+You+Need%22&max_price=0.008&limit=1)
and [DOI recommendation](https://apiacre.com/recommend?task=Resolve+DOI+10.1126%2Fscience.169.3946.635&max_price=0.003&limit=1) return the validated
request in `suggestedInput`. Use that JSON as the request body to check the
price from a terminal or agent. The lookup accepts plain DOIs and full
`https://doi.org/` links.

To limit a search to a publication window, use
`Search Crossref for "agentic commerce" published from 2026-01-01 through 2026-11-24`.
The free [date-range recommendation](https://apiacre.com/recommend?task=Search%20Crossref%20for%20%22agentic%20commerce%22%20published%20from%202026-01-01%20through%202026-11-24&max_price=0.008&limit=1) includes both dates in `suggestedInput`, and the checkout shows them before payment approval.
A start date also works on its own.

The [Crossref publication workflow](https://apiacre.com/workflows/crossref-publication-record)
opens each checkout with a real example and links to the underlying Crossref
records. The two calls total **0.011 USDC** on Base or Solana. Review the search
results and select your DOI before authorizing the second call.

## Preview geocoding

Choose the API based on the input you have. Each paid endpoint accepts `POST` and
quotes the same USDC price on Base and Solana. The sample links show a free JSON
response, and the checkout links let you edit the input before authorizing a call.

| Input you have | Result | USDC per call | Free sample | Checkout |
| --- | --- | ---: | --- | --- |
| Place name such as `London, GB` | Ranked cities or localities with coordinates | 0.002 | [Place sample](https://apiacre.com/samples/data.place-geocode) | [Place geocoding](https://apiacre.com/try/data.place-geocode) |
| Latitude `51.5074` and longitude `-0.1278` | Populated places ranked by distance from the point | 0.002 | [Reverse sample](https://apiacre.com/samples/data.reverse-geocode) | [Reverse geocoding](https://apiacre.com/try/data.reverse-geocode) |
| U.S. street address such as `4600 Silver Hill Rd, Washington, DC 20233` | Census coordinates with optional geography and source details | 0.005 | [Address sample](https://apiacre.com/samples/data.us-address-geocode) | [Street-address geocoding](https://apiacre.com/try/data.us-address-geocode) |

Search API Acre for `Find the lat/long of Paris, Texas, US` and choose
**Review your place request** to see the locality and **0.002 USDC** price.
The free recommendation returns the same place in `suggestedInput`.
[API Acre](https://apiacre.com/) · [Free recommendation](https://apiacre.com/recommend?task=Find%20the%20lat%2Flong%20of%20Paris%2C%20Texas%2C%20US&max_price=0.002&limit=1)

Search for `Reverse geocode 47.6062, -122.3321` and choose **Review your
reverse-geocoding request** to carry the coordinates into checkout.
Agents can retrieve the validated coordinates in `suggestedInput`.
[API Acre catalog](https://apiacre.com/#catalog) · [Free recommendation](https://apiacre.com/recommend?task=Reverse%20geocode%2047.6062%2C%20-122.3321&max_price=0.002)

The [free street-address recommendation](https://apiacre.com/recommend?task=lookup%20a%20postal%20address&max_price=0.005&limit=1)
returns the address service and its checkout link at a **0.005 USDC** cap. A
[0.003 USDC cap](https://apiacre.com/recommend?task=lookup%20a%20postal%20address&max_price=0.003&limit=1)
returns an empty list for the same request.

The [city-to-local-time workflow](https://apiacre.com/workflows/place-local-time)
looks up a city and its IANA time zone, then converts an offset-aware timestamp
for the place you choose. Each call costs **0.002 USDC** on Base or Solana.
The [free workflow recommendation](https://apiacre.com/recommend?task=convert%20a%20UTC%20timestamp%20to%20local%20time%20in%20London&max_total_price=0.004&limit=2)
shows the recipe at a **0.004 USDC** total cap. Use the
[time zone converter](https://apiacre.com/services/data.timezone-convert)
directly when you know the IANA zone or its representative city.

## Preview a time-zone conversion

The [time-zone converter](https://apiacre.com/services/data.timezone-convert)
costs **0.002 USDC** per call on Base or Solana. On the
[API Acre homepage](https://apiacre.com/), search for
`Convert 2026-12-08 09:30 from London to New York`. Select **Find APIs for this
task**, then **Review your time-zone request** to see the timestamp, zones and
live price before connecting a wallet. The
[free city-name recommendation](https://apiacre.com/recommend?task=Convert%202026-12-08%2009%3A30%20from%20London%20to%20New%20York&max_price=0.002&limit=1)
fills `Europe/London` and `America/New_York` into the request. Recognized
IANA representative city names also work in
[checkout](https://apiacre.com/try/data.timezone-convert), with an optional
two-letter country code such as `London, GB`.

For a 12-hour clock, supply an explicit date as `YYYY-MM-DD`. Try
`Convert 9:30 AM from New York to London on 2026-11-25` and verify the
local timestamp and both zones in checkout. [Free AM/PM recommendation](https://apiacre.com/recommend?task=Convert%209%3A30%20AM%20from%20New%20York%20to%20London%20on%202026-11-25&max_price=0.002&limit=1)

A local timestamp without an offset requires a source IANA zone. For a time
that occurs twice when clocks go back, name the earlier or later occurrence
in the search. The [free repeated-hour recommendation](https://apiacre.com/recommend?task=Convert+2026-11-01T01%3A30%3A00+from+America%2FNew_York+to+Europe%2FLondon+using+the+later+occurrence&max_price=0.002&limit=1)
returns the following request in `suggestedInput`.

```json
{
  "timestamp": "2026-11-01T01:30:00",
  "source_timezone": "America/New_York",
  "target_timezone": "Europe/London",
  "ambiguous_time": "later"
}
```

The [static result sample](https://apiacre.com/samples/data.timezone-convert)
shows that the later New York occurrence corresponds to 06:30 UTC. If no
occurrence was chosen or the local time falls in a spring-forward gap,
`suggestedInput` is null. An offset-aware timestamp identifies an exact instant.

## Preview weather

Enter `What's the weather like in London, GB right now?` or
`Show me the 6-hour weather forecast for London, GB` in the service search. Choose
**Find APIs for this task**, then **Review your weather request** to see the
exact location and price before authorizing a call. [Open API Acre](https://apiacre.com/)

| Request | Exact price per call | Free previews |
| --- | ---: | --- |
| Current conditions by city or coordinates | 0.002 USDC | [Free recommendation](https://apiacre.com/recommend?task=What%27s%20the%20weather%20like%20in%20London%2C%20GB%20right%20now%3F&max_price=0.002&limit=1) · [Result sample](https://apiacre.com/samples/data.current-weather) |
| Global forecast by place or coordinates | 0.003 USDC | [Free recommendation](https://apiacre.com/recommend?task=Show%20me%20the%206-hour%20weather%20forecast%20for%20London%2C%20GB&max_price=0.003&limit=1) · [Result sample](https://apiacre.com/samples/data.us-weather-forecast) |

The forecast example requests six hourly periods. A `7-day weather forecast
for London, GB` requests up to 14 day/night periods. For up to 24 hourly periods
at coordinates, try `24-hour forecast for 38.9,-77.0`. REST, MCP, and A2A
recommendations expose the validated JSON as `suggestedInput` for unsigned
quotes on Base or Solana. [Read the forecast schema](https://apiacre.com/services/data.us-weather-forecast)

## Preview an ECB FX conversion

The [ECB reference FX API](https://apiacre.com/services/data.ecb-fx-reference)
converts a decimal amount using the latest available ECB observation on or
before the requested date. One successful call costs **0.002 USDC** on Base or
Solana. The [free result sample](https://apiacre.com/samples/data.ecb-fx-reference)
shows the observation date, rate, and converted amount.

Search for `Convert 25.5 CHF to EUR as of 2025-11-21` on the
[API Acre homepage](https://apiacre.com/), select **Find APIs for this task**,
then choose **Review your FX request**. Checkout opens with those inputs and
checks the price before you connect a wallet.

Ask `Convert 100 EUR to USD using ECB reference rates` to prepare the latest
available common business-day observation. Add `as of YYYY-MM-DD` to use a
historical cutoff. The quote review shows the amount, currency pair, and cutoff
before payment. [Free conversion recommendation](https://apiacre.com/recommend?task=Convert%20100%20EUR%20to%20USD%20using%20ECB%20reference%20rates&max_price=0.002&limit=1)

For a terminal preview, save the validated `suggestedInput` from the free
selector. This example checks the service and price before writing the JSON.
The same field is available in MCP and A2A recommendations. A `null` value
means the amount or date needs correction before quoting.

```sh
recommendation=$(curl --fail --silent --show-error --max-time 12 \
  https://apiacre.com/recommend \
  --header 'Content-Type: application/json' \
  --data '{"task":"Convert 25.5 CHF to EUR as of 2025-11-21","maxPrice":"0.002","limit":1}') &&
printf '%s\n' "$recommendation" | jq -e '
  (select(.paymentRequired == false and .executesService == false)
   | .recommendations[0]
   | select(.service.slug == "data.ecb-fx-reference" and .service.purchase.exactAmount == "0.002")
   | .suggestedInput | objects) // error("No validated FX request at 0.002 USDC")
' > fx-request.json
```

With the dependencies from the [Base Python quickstart](#get-a-base-quote),
run the downloaded example against that JSON to check the live price and
recipient. The command requests a quote without a wallet or payment.

```sh
curl --fail --silent --show-error --max-time 12 \
  'https://apiacre.com/examples/python-buyer.py?service=data.ecb-fx-reference' \
  --output fx-buyer.py &&
python3 fx-buyer.py --input fx-request.json
```

For Solana, pass the same JSON to the [Solana FX example](https://apiacre.com/examples/python-solana-buyer.py?service=data.ecb-fx-reference)
using the [Solana Python quickstart](#get-a-solana-quote).

## Preview web extraction

[Web extraction](https://apiacre.com/catalog/web.extract) returns readable text
or Markdown from one public HTTP or HTTPS page for **0.01 USDC** per call. The
result also includes the source URL and a bounded list of links. See the
[free output sample](https://apiacre.com/samples/web.extract).

Paste one of these requests into **Find a service** on the [API Acre homepage](https://apiacre.com/#catalog).
Select **Review your web extraction request** to check the URL, output format,
and exact quote.

```text
Extract the main article text from https://apiacre.com/use-cases
Convert https://apiacre.com/use-cases to Markdown
```

[Plain-text recommendation](https://apiacre.com/recommend?task=Extract+the+main+article+text+from+https%3A%2F%2Fapiacre.com%2Fuse-cases&max_price=0.01&limit=1) and
[Markdown recommendation](https://apiacre.com/recommend?task=Convert+https%3A%2F%2Fapiacre.com%2Fuse-cases+to+Markdown&max_price=0.01&limit=1) return the prepared JSON
in `suggestedInput` for scripts and agents. Quote review is free. Each purchase
requires its own authorization.

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

Paste either request into **Find a service** to review the URL before paying.
[Open the service catalog](https://apiacre.com/#catalog).

- `Run an SEO audit for https://apiacre.com/use-cases`
- `Get website metadata for https://apiacre.com/use-cases`

## Preview Base gas fees and fee history

[Base network status](https://apiacre.com/catalog/crypto.base-network-status)
returns the current Base mainnet gas price and block, plus fee history for **1 to
20 recent blocks**, for **0.001 USDC** per call. The default window is five
blocks. See the [free output sample](https://apiacre.com/samples/crypto.base-network-status).

[Preview a 12-block quote in the browser](https://apiacre.com/try/crypto.base-network-status?from=quote&fee_history_blocks=12).
Use `fee_history_blocks` from `1` to `20` to share a different window.

Paste either question into **Find a service** on the [API Acre homepage](https://apiacre.com/#catalog).
Select **Review your Base network status request** to see the quote and any
requested block count.

```text
What were the gas fees on Base over the last 12 blocks?
What is the current gas price on Base?
```

[12-block fee history recommendation](https://apiacre.com/recommend?task=What+were+the+gas+fees+on+Base+over+the+last+12+blocks%3F&max_price=0.001&limit=1) and
[current gas price recommendation](https://apiacre.com/recommend?task=What+is+the+current+gas+price+on+Base%3F&max_price=0.001&limit=1) return the exact
prepared JSON in `suggestedInput`. Quote review is free. Each purchase requires
its own authorization.

## Preview Base account balances

Use [Base account status](https://apiacre.com/catalog/crypto.base-account-status)
for ETH and native USDC at one Base block for **0.003 USDC**. Use a
[Base account snapshot](https://apiacre.com/catalog/crypto.base-account-snapshot)
to include up to four specified ERC-20 contracts for **0.01 USDC**. Both calls
include the account nonce and contract-code status. Available block tags are
`latest`, `safe`, and `finalized`. The default is `safe`.

Paste one of these requests into **Find a service** on the [API Acre homepage](https://apiacre.com/#catalog),
then select **Review your Base account request** to check the exact input and quote.

```text
Check the ETH and USDC balance of 0x000000000000000000000000000000000000dEaD on Base at the safe block
Read ERC-20 balances for 0x000000000000000000000000000000000000dEaD on Base at the finalized block, including token contract 0x4200000000000000000000000000000000000006
```

[Free account-status recommendation](https://apiacre.com/recommend?task=Check+the+ETH+and+USDC+balance+of+0x000000000000000000000000000000000000dEaD+on+Base+at+the+safe+block&max_price=0.003&limit=1) and
[free account-snapshot recommendation](https://apiacre.com/recommend?task=Read+ERC-20+balances+for+0x000000000000000000000000000000000000dEaD+on+Base+at+the+finalized+block%2C+including+token+contract+0x4200000000000000000000000000000000000006&max_price=0.01&limit=1) return the
same JSON in `suggestedInput` for scripts and agents. Search and quote review
are free. Each purchase requires its own authorization.

## Preview Base stock evidence

[Open the Base stock evidence workflow](https://apiacre.com/workflows/base-stock-evidence)
for two prefilled quotes and the original token metadata and SEC filing.

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
For each call, the workflow checks the catalog price against unsigned quotes in
native USDC on Base and Solana. The job summary includes the price, free result
sample, and checkout for each input.
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

Through 24 November 2026 at 06:02 UTC, API Acre's production ledger recorded
at least **392 independently attributed settled calls from 63 payers**,
totaling **1.767 USDC on Base** across 47 services. These totals exclude
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

Review [`skills/api-acre/SKILL.md`](skills/api-acre/SKILL.md) before using the skill.
From a Codex project's root, run the [Skills CLI](https://www.skills.sh/docs/cli)
command and confirm the project installation when prompted.

```bash
npx skills@1.9.0 add APIAcre/apiacre --skill api-acre --agent codex --copy
```

The command copies the skill into `.agents/skills/api-acre`. Use the CLI’s `use`
command to print the current instructions in a terminal.

```bash
npx skills@1.9.0 use APIAcre/apiacre@api-acre
```

Hosts that manage skill files directly can copy the complete `skills/api-acre`
directory into their skill directory. The live version and its checksum are
published in [API Acre's integration manifest](https://apiacre.com/integrations.json).

For Codex-compatible hosts, this repository also includes a plugin manifest and
remote MCP configuration. No wallet or API credential is bundled. Installing the
skill permits free discovery and quote checks; it does not authorize payment.

The current public package is [v1.5.2 on GitHub](https://github.com/APIAcre/apiacre/releases/tag/v1.5.2).
Save [api-acre.zip](https://github.com/APIAcre/apiacre/releases/download/v1.5.2/api-acre.zip)
and [SHA256SUMS](https://github.com/APIAcre/apiacre/releases/download/v1.5.2/SHA256SUMS)
to the same directory. Run `sha256sum -c SHA256SUMS` before unpacking the ZIP.

The skill includes a wallet-free Python quote path for fixed-price APIs on Base
and Solana. Coinbase Agentic Wallet MCP is an optional, separately installed
buyer companion. Each paid call requires its own approval.

### Install in Claude Code

Install the API Acre skill and remote MCP connection from this repository.

```bash
claude plugin marketplace add APIAcre/apiacre
claude plugin install api-acre@api-acre-tools
```

In a session, try `/api-acre:api-acre Find an API to convert a timestamp to London
local time and show me the example and price.` The plugin connects to
`https://apiacre.com/mcp` for free discovery. When you are ready to buy a result,
use the service's checkout or a compatible x402 client and approve the specific
request, network, and maximum USDC amount.

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

## Check a quote from your web app

Run this JavaScript in the console of a page you control, such as your app on
localhost. The time-zone converter returns an unpaid quote on Base and Solana.
The browser can read the `PAYMENT-REQUIRED` header without credentials or a
wallet. The example stops after displaying the price and recipient.

```javascript
const endpoint = "https://apiacre.com/v1/data/timezone-convert";
const request = {
  timestamp: "2026-11-01T06:30:00Z",
  target_timezone: "Europe/London",
};
const response = await fetch(endpoint, {
  method: "POST",
  mode: "cors",
  credentials: "omit",
  redirect: "error",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(request),
});
const encodedQuote = response.headers.get("PAYMENT-REQUIRED");
if (response.status !== 402 || !encodedQuote) {
  throw new Error("Expected an unpaid x402 quote");
}
const bytes = Uint8Array.from(atob(encodedQuote), (char) => char.charCodeAt(0));
const quote = JSON.parse(new TextDecoder().decode(bytes));
if (quote.x402Version !== 2 || quote.resource?.url !== endpoint) {
  throw new Error("The quote does not match this API");
}

const base = "eip155:8453";
const solana = "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp";
const offers = quote.accepts.filter((offer) => {
  const nativeUsdc = offer.network === base
    ? offer.asset?.toLowerCase() === "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
    : offer.network === solana
      && offer.asset === "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
  return nativeUsdc && offer.scheme === "exact" && offer.amount === "2000" && offer.payTo;
});
if (offers.length !== 2 || new Set(offers.map((offer) => offer.network)).size !== 2) {
  throw new Error("Expected 0.002 USDC quotes on Base and Solana");
}
console.table(offers.map(({ network, amount, payTo }) => ({ network, amount, payTo })));
```

The amount is in atomic USDC units. For more routes and their input examples,
fetch the [x402 discovery document](https://apiacre.com/.well-known/x402)
from the same app. For a paid call, review the input, network, amount and
recipient before authorizing payment. See the [buyer guide](https://apiacre.com/buyers).

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

### Read an MCP quote from Node.js

The x402 SDK reads payment terms from an MCP tool result. In a new project, install
the verified versions and save the example as `mcp-quote.mjs`.

```sh
npm init -y
npm install @x402/mcp@2.32.0 @x402/core@2.32.0 @modelcontextprotocol/sdk@1.32.2
node mcp-quote.mjs
```

```js
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { createx402MCPClient } from "@x402/mcp";

const name = "data.current-weather";
const client = createx402MCPClient({
  name: "apiacre-quote-example",
  version: "1.0.0",
  schemes: [],
  autoPayment: false,
});

const transport = new StreamableHTTPClientTransport(new URL("https://apiacre.com/mcp"), {
  requestInit: { headers: { "User-Agent": "APIAcre-x402-MCP-Quote/1.0" } },
});

try {
  await client.connect(transport);
  const { tools } = await client.listTools();
  const input = tools.find((tool) => tool.name === name)?.inputSchema.examples?.[0];
  if (!input) throw new Error(`No request example found for ${name}`);
  const quote = await client.getToolPaymentRequirements(name, input);
  if (!quote) throw new Error(`Expected a payment quote for ${name}`);
  console.log(JSON.stringify({ tool: name, input, quote }, null, 2));
} finally {
  await client.close();
}
```

Current weather quotes 0.002 USDC on Base and Solana. Each `amount` is in
millionths of USDC, so `2000` means 0.002 USDC. This client has no signing schemes and
automatic payment is disabled. For the HTTP contract and the checkout link, see the
[current-weather catalog entry](https://apiacre.com/catalog/data.current-weather).
[x402 MCP SDK](https://github.com/x402-foundation/x402/tree/main/typescript/packages/mcp)

Use the [runnable Node.js buyer](examples/mcp-buyer/) to choose a tool and approve
one purchase with your own wallet, USDC limit, and reviewed recipient.

### Find MCP tools within a budget

Read the free recommendation resource with `max_price` for a per-service cap
and `max_total_price` for a whole-workflow cap, both in USDC. The optional
`limit` returns up to that many matches in each list, from 1 to 10. The example
below requests one service and one workflow within their respective limits.

```bash
curl -fsS https://apiacre.com/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"resources/read","params":{"uri":"https://apiacre.com/recommend?task=search%20NIH%20funding%20grants%20for%20an%20institution&max_price=0.005&max_total_price=0.008&limit=1"}}'
```

Parse `result.contents[0].text` as JSON. Read `recommendations` for services
and `workflowRecommendations` for recipes. If nothing matches a cap, its list
is empty. Each paid step still requires separate authorization. The server
marks these selector responses as private and non-cacheable.

### Find a service with Python

Save this as `discover.py`. Send a descriptive `User-Agent` with your application's
name and version. The default Python `urllib` user agent can receive HTTP 403 with
Cloudflare error 1010. [Cloudflare error 1010 reference](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)

```python
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

params = {"task": "Inspect Base block 25000000", "max_price": "0.001", "limit": 1}
request = Request(
    f"https://apiacre.com/recommend?{urlencode(params)}",
    headers={"Accept": "application/json", "User-Agent": "ResearchExample/1.0"},
)
with urlopen(request, timeout=15) as response:
    rows = json.load(response)["recommendations"]
if not rows or rows[0]["service"]["slug"] != "crypto.base-block-inspect":
    raise SystemExit("No Base block inspection recommendation within the budget.")
print(json.dumps(rows[0]["suggestedInput"]))
```

Save the linked script as `python-buyer.py` and pass it the suggested request. This
prints an unsigned quote for the selected block. [Base block Python buyer](https://apiacre.com/examples/python-buyer.py?service=crypto.base-block-inspect)

```sh
python3 discover.py | python3 python-buyer.py --input -
```

## Get a Base quote

Search for `What is the timestamp of Base block 34600000?` and choose
**Review your Base block request** to preview the exact block at **0.001 USDC**.
The free recommendation puts the block number in `suggestedInput`. Search for
`Get the finalized Base block header` to prepare a request with the finalized tag.
[API Acre catalog](https://apiacre.com/#catalog) · [Free recommendation](https://apiacre.com/recommend?task=What%20is%20the%20timestamp%20of%20Base%20block%2034600000%3F&max_price=0.001&limit=1)

Search for `Inspect Base transaction` followed by your transaction hash to
review the receipt request at **0.005 USDC**. Search for
`Get the Base mainnet network status` to preview the current block and gas fees
at **0.001 USDC**. Both services quote these prices on Base and Solana.

Save the [SEC Filing Signals example](https://apiacre.com/examples/python-buyer.py)
as `python-buyer.py`. Its default run shows the live recipient and the 0.05 USDC
quote on Base mainnet. The quote needs only Python 3.10 or later.

```sh
python3 python-buyer.py
```

Choose **Use Python on Base** on any fixed-price service page or checkout. For
example, the [Code Metrics script](https://apiacre.com/examples/python-buyer.py?service=developer.code-metrics)
quotes 0.025 USDC per call. Agents can find each download under
`purchase.basePythonExampleUrl` in the [x402 discovery document](https://apiacre.com/.well-known/x402).

Pass `--input request.json` to quote your own JSON, or use `--input -` to read
a JSON object from standard input. The [buyer guide](https://apiacre.com/buyers)
covers SDK setup and explicit authorization for one paid call.

## Get a Solana quote

[Download the Python example](https://apiacre.com/examples/python-solana-buyer.py)
to check the live quote for timezone conversion on Solana mainnet. The default
run displays the recipient and the 0.002 USDC price using Python 3.10 or later.

```sh
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

## Use reviewed checkout JSON in Python

1. Open [Code Metrics checkout](https://apiacre.com/try/developer.code-metrics).
   The default request gets an unsigned quote automatically. If you edit the
   JSON, select **Verify changed input**.
2. Select **Download reviewed request JSON** once the quote is shown. The file
   contains the exact JSON from the quote request.
3. Select **Use Python on Base** or **Use Python on Solana** and save the script
   beside the JSON file. Run the command for your network.

```sh
# Base
python3 apiacre-developer.code-metrics-base.py --input apiacre-developer.code-metrics-request.json

# Solana
python3 apiacre-developer.code-metrics-solana.py --input apiacre-developer.code-metrics-request.json
```

Each command checks the current price and recipient for the exported request
without signing in to a wallet or paying. The same handoff works on the other
fixed-price checkouts with their own scripts and filenames.

If browser verification fails, select **Download draft request JSON** to save
the editor's contents locally. Pass the draft filename with `--input` to get an
unpaid quote in Python. The terminal quote checks the live price and recipient
for that draft.

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
