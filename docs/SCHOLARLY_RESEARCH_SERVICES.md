# Scholarly institutions and research funding

API Acre provides two paid HTTP/MCP services for institution and funding
research. Their official upstream APIs are free; the API Acre fee covers
bounded retrieval, normalization, source evidence and x402 delivery.

| Service | HTTP route | USDC per call | Atomic USDC |
| --- | --- | ---: | ---: |
| `research.ror-organization-search` | `POST /v1/research/ror-organization-search` | 0.003 | 3,000 |
| `research.nih-grant-search` | `POST /v1/research/nih-grant-search` | 0.005 | 5,000 |

Both accept exact USDC on Base and Solana mainnet. The same service names are
MCP tools at `https://apiacre.com/mcp`. Schemas, samples, recommendation results
and payment quotes are free to inspect.

## Institution and affiliation evidence

The ROR service supports three modes:

- `name` searches organization names and external identifiers. An optional
  two-letter `country_code` restricts name results.
- `affiliation` sends an affiliation string to ROR's matching service and
  preserves its scores, matching type and `chosen` evidence.
- `id` resolves one checksum-valid compact ROR ID or canonical
  `https://ror.org/` URL. The source request always goes to the official API.

`query` is required, with 2–300 characters. `max_results` defaults to 10 and
is bounded to 1–20. Country filters are supported only in name mode.

Example request:

```json
{
  "query": "Department of Computer Science, University of Oxford, United Kingdom",
  "match_mode": "affiliation",
  "max_results": 5
}
```

Results include canonical ROR IDs, display and alternate names, organization
types and status, establishment year, domains, links, locations, external
identifiers and relationships. Record-modified dates and schema versions are
preserved when present. Source attribution and a SHA-256 hash accompany the
normalized data.

Name matches are candidates. ROR explicitly advises against automatically
choosing the first search result. `sourceChosenRorIds` preserves source choices
even when the selected record falls outside the requested result limit.
Affiliation scores and choices remain ROR's evidence; API Acre does not issue
an independent identity or ownership verdict. A valid ID that has no source
record returns an explicit empty result.

Searches use ROR's active-record default. Exact ID lookup can return an inactive
or withdrawn record. `resultsTruncated` describes result-page limits;
`fieldsTruncated` identifies bounded record lists. Metadata strings are
limited to 2,000 characters.

ROR registry metadata is CC0. GeoNames-derived location fields retain separate
CC BY 3.0 attribution. See the official
[ROR API documentation](https://ror.readme.io/docs/rest-api),
[matching guidance](https://ror.readme.io/docs/matching),
[identifier specification](https://ror.readme.io/docs/identifier) and
[data policy](https://ror.org/blog/2026-03-27-strengthening-commitment-to-posi/).

## Research grant search

The NIH service searches administrative award records in NIH RePORTER,
including participating non-NIH federal agencies. Supply `query`,
`organization`, or both. Topic words are joined with AND and searched in
project titles and indexed terms. Organization filtering uses the source's
organization-name search.

Optional `fiscal_year` accepts 1985–2100. `max_results` defaults to 10 and
is bounded to 1–20. A fiscal-year descending sort is requested; the response
also preserves the source's reported sorting and relevance flags.

```json
{
  "query": "robotics",
  "organization": "JOHNS HOPKINS UNIVERSITY",
  "fiscal_year": 2025,
  "max_results": 10
}
```

Records contain application and project identifiers, title, fiscal year,
source-reported award amount, funded organization, available UEI/DUNS
identifiers, administering agency, investigator names, project and budget
dates, and a canonical RePORTER project link. Abstracts, scientific results
and investigator contact details are excluded.

Award amounts belong to the reported application/fiscal year. They are not a
lifetime project total, and related project numbers can recur across years or
subprojects. Missing amounts remain null. The first bounded page must not be
extrapolated into a complete funding total. These are award records, rather
than open application opportunities.

An organization name in NIH is separate evidence from a ROR candidate.
Confirm the organization using its identifiers before joining records.
The service does not infer that similarly named organizations are identical.
See the official [NIH RePORTER API](https://api.reporter.nih.gov/) for criteria,
field definitions, data coverage and traffic limits.

## Retrieval, caching and failures

Every successful result includes `retrievedAt`, a source-response SHA-256 hash,
source attribution and `sourceCacheHit`. Successfully normalized results can
be reused for up to 600 seconds; a cache hit keeps the original retrieval time.
The cache is bounded in both bytes and entries.

Source access is serialized and throttled independently: at most five ROR
requests per second and fewer than one NIH request per second. Responses are
limited to two million decompressed bytes. Timeouts, rate limits, redirects,
invalid JSON and inconsistent result counts produce an error. They are not
reported as successful searches with zero matches. There are no automatic
source retries.

## Free inspection and use

- Full contracts:
  `https://apiacre.com/catalog/research.ror-organization-search` and
  `https://apiacre.com/catalog/research.nih-grant-search`.
- Static samples: use the same slugs under
  `https://apiacre.com/samples/`, optionally with `?format=json`.
- Browser checkout: use the slugs under `https://apiacre.com/try/`.
- Agent selection:
  `GET /recommend?task=research+institution+affiliation+ROR&max_price=0.003`.
- MCP: list tools and inspect each published input/output schema before
  approving a paid call.

Sending a valid request without a payment signature returns an HTTP 402 quote
and does not fetch the source. A paid retry requires the buyer's approval for
the exact endpoint, input, network and maximum USDC amount.

The `research-funding-landscape` recipe at
`https://apiacre.com/workflows/research-funding-landscape.json` combines the
two services for 0.008 USDC across separately authorized calls. The recipe
requires a caller-confirmed NIH organization name; it performs no automatic
cross-registry identity linkage.
