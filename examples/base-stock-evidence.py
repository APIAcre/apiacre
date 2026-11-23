"""Preview API Acre Base quotes for the TSLAc reference and TSLA issuer example."""

import base64
import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ORIGIN = "https://apiacre.com"
TOKEN_METADATA = "https://api.coinbase.com/v1/tokenized-stocks/metadata/TSLAc"
SEC_FILING = "https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm"
BASE = "eip155:8453"
BASE_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
MAX_JSON_BYTES = 1_048_576


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


opener = build_opener(NoRedirects())


def request(url, body=None):
    headers = {"Accept": "application/json", "User-Agent": "APIAcre-stock-evidence-example/1"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    try:
        return opener.open(Request(url, data=data, headers=headers), timeout=12)
    except HTTPError as response:
        return response


def get_json(url):
    with request(url) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        data = response.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise RuntimeError(f"{url} returned too much data")
    return json.loads(data)


def preview(slug, path, body, maximum_usdc):
    contract_url = f"{ORIGIN}/catalog/{slug}"
    purchase = get_json(contract_url)["purchase"]
    endpoint = f"{ORIGIN}{path}"
    price = purchase["exactAmount"]
    if not isinstance(price, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,6})?", price):
        raise RuntimeError(f"The advertised price has invalid USDC precision for {slug}")
    amount = Decimal(price)
    if purchase["endpoint"] != endpoint or not 0 < amount <= Decimal(maximum_usdc):
        raise RuntimeError(f"The endpoint or advertised price changed for {slug}")
    atomic_amount = int(amount * 1_000_000)

    with request(endpoint, body) as response:
        challenge = response.headers.get("PAYMENT-REQUIRED")
        if response.status != 402 or not challenge or response.headers.get("PAYMENT-RESPONSE"):
            raise RuntimeError(f"Expected an unpaid quote for {slug}, got HTTP {response.status}")
    quote = json.loads(base64.b64decode(challenge, validate=True))
    if quote["x402Version"] != 2 or quote["resource"]["url"] != endpoint:
        raise RuntimeError(f"Unexpected resource in the quote for {slug}")
    offers = [offer for offer in quote["accepts"] if offer["network"] == BASE]
    if len(offers) != 1:
        raise RuntimeError(f"Expected one Base offer for {slug}")
    (offer,) = offers
    if (
        offer["scheme"] != "exact"
        or offer["asset"].lower() != BASE_USDC
        or offer["amount"] != str(atomic_amount)
        or not ADDRESS.fullmatch(offer["payTo"])
    ):
        raise RuntimeError(f"Unexpected Base payment terms for {slug}")
    return {
        "service": slug,
        "contractUrl": contract_url,
        "sampleUrl": purchase["sampleUrl"],
        "request": {"method": "POST", "url": endpoint, "body": body},
        "quote": {
            "network": BASE,
            "asset": BASE_USDC,
            "amountUsdc": str(amount),
            "payTo": offer["payTo"],
        },
        "separatePaymentAuthorizationRequired": True,
    }


def main():
    reference = get_json(TOKEN_METADATA)
    token_contract = reference["contract_address"]
    if reference["symbol"] != "TSLAc" or not ADDRESS.fullmatch(token_contract):
        raise RuntimeError("Unexpected token metadata")

    quotes = [
        preview(
            "crypto.base-contract-read",
            "/v1/crypto/base-contract-read",
            {
                "contract": token_contract,
                "call_data": "0x313ce567",
                "block_tag": "safe",
                "output_types": ["uint8"],
            },
            "0.005",
        ),
        preview(
            "research.sec-company-evidence",
            "/v1/research/sec-company-evidence",
            {"identifier": "TSLA"},
            "0.02",
        ),
    ]
    total = sum(Decimal(item["quote"]["amountUsdc"]) for item in quotes)
    packet = {
        "checkedAt": datetime.now(UTC).isoformat(),
        "tokenReference": {
            "symbol": "TSLAc",
            "baseContract": token_contract,
            "source": TOKEN_METADATA,
        },
        "issuerReference": {"ticker": "TSLA", "cik": "0001318605", "source": SEC_FILING},
        "optionalEvidenceQuotes": quotes,
        "quotedTotalUsdcIfBothSeparatelyAuthorized": str(total),
    }
    print(json.dumps(packet, indent=2))


if __name__ == "__main__":
    main()
