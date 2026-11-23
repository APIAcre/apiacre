"""Check live Base prices for two synthetic schema requests using Python 3.11+."""

import base64
import json
import re
from decimal import Decimal
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ORIGIN = "https://apiacre.com"
BASE = "eip155:8453"
BASE_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
PRICE = re.compile(r"[0-9]+(?:\.[0-9]{1,6})?")
MAX_CATALOG_BYTES = 1_048_576
CASES = (
    (
        "data.schema",
        "/v1/data/schema",
        "0.025",
        {"content": '[{"name":"Ada","score":98}]', "format": "json", "root_mode": "records"},
    ),
    (
        "data.schema-validate",
        "/v1/data/schema-validate",
        "0.01",
        {
            "check_formats": True,
            "instance": {"name": "Ada", "score": "98"},
            "max_errors": 25,
            "schema": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "additionalProperties": False,
                "properties": {
                    "name": {"minLength": 1, "type": "string"},
                    "score": {"minimum": 0, "type": "integer"},
                },
                "required": ["name", "score"],
                "type": "object",
            },
        },
    ),
)


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


opener = build_opener(NoRedirects())


def request(url, body=None):
    headers = {"Accept": "application/json", "User-Agent": "APIAcre-schema-quote-preview/1"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, separators=(",", ":")).encode()
    try:
        return opener.open(Request(url, data=data, headers=headers), timeout=12)
    except HTTPError as response:
        return response


def preview(slug, path, maximum, body):
    contract_url = f"{ORIGIN}/catalog/{slug}"
    endpoint = f"{ORIGIN}{path}"
    sample = f"{ORIGIN}/samples/{slug}"
    checkout = f"{ORIGIN}/try/{slug}"
    with request(contract_url) as response:
        if response.status != 200:
            raise RuntimeError(f"{slug} catalog returned HTTP {response.status}")
        data = response.read(MAX_CATALOG_BYTES + 1)
    if len(data) > MAX_CATALOG_BYTES:
        raise RuntimeError(f"{slug} catalog response exceeded the size limit")
    contract = json.loads(data)
    purchase = contract["purchase"]
    expected = {
        "endpoint": endpoint,
        "method": "POST",
        "network": BASE,
        "asset": "USDC",
        "sampleUrl": sample,
        "browserCheckoutUrl": checkout,
        "authorizationRequired": True,
    }
    if contract["inputExample"] != body or any(
        purchase.get(key) != value for key, value in expected.items()
    ):
        raise RuntimeError(f"{slug} no longer matches the checkout and fixture in this example")
    price = purchase["exactAmount"]
    if not isinstance(price, str) or not PRICE.fullmatch(price):
        raise RuntimeError(f"{slug} catalog price is not decimal USDC")
    amount = Decimal(price)
    if not 0 < amount <= Decimal(maximum):
        raise RuntimeError(f"{slug} price is outside the example cap of {maximum} USDC")

    with request(endpoint, body) as response:
        encoded = response.headers.get("PAYMENT-REQUIRED")
        if response.status != 402 or not encoded or response.headers.get("PAYMENT-RESPONSE"):
            raise RuntimeError(
                f"{slug} expected an unpaid quote and received HTTP {response.status}"
            )
    quote = json.loads(base64.b64decode(encoded, validate=True))
    if quote["x402Version"] != 2 or quote["resource"]["url"] != endpoint:
        raise RuntimeError(f"{slug} received a quote for a different resource or protocol version")
    offers = [offer for offer in quote["accepts"] if offer["network"] == BASE]
    if len(offers) != 1:
        raise RuntimeError(f"{slug} expected one Base payment option")
    (base_offer,) = offers
    if (
        base_offer["scheme"] != "exact"
        or base_offer["asset"].lower() != BASE_USDC
        or base_offer["amount"] != str(int(amount * 1_000_000))
        or not ADDRESS.fullmatch(base_offer["payTo"])
    ):
        raise RuntimeError(f"{slug} Base quote does not match the expected USDC terms")
    return amount, contract_url, sample, checkout


def main():
    rows = [preview(*case) for case in CASES]
    totals = sum(row[0] for row in rows)
    print(
        "## Live API Acre schema prices on Base\n\n"
        "| Service | USDC per call | Free result sample | Browser checkout |\n"
        "| --- | ---: | --- | --- |"
    )
    for (slug, *_), (amount, contract, sample, checkout) in zip(CASES, rows, strict=True):
        print(f"| [{slug}]({contract}) | {amount} | [Sample]({sample}) | [Review]({checkout}) |")
    print(
        f"\nUnsigned quote preview. Both calls would total **{totals} USDC** "
        "if authorized separately. The checkout links use the synthetic requests previewed here."
    )


if __name__ == "__main__":
    main()
