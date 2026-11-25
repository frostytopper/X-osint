"""Phone number OSINT: offline parsing via phonenumbers + optional API enrichment."""

from __future__ import annotations

from typing import Any

import phonenumbers
import requests
from phonenumbers import carrier, geocoder, timezone

from xosint.config import get_secret

DEFAULT_TIMEOUT = 10

_NUMBER_TYPE_NAMES = {
    phonenumbers.PhoneNumberType.FIXED_LINE: "fixed_line",
    phonenumbers.PhoneNumberType.MOBILE: "mobile",
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
    phonenumbers.PhoneNumberType.TOLL_FREE: "toll_free",
    phonenumbers.PhoneNumberType.PREMIUM_RATE: "premium_rate",
    phonenumbers.PhoneNumberType.SHARED_COST: "shared_cost",
    phonenumbers.PhoneNumberType.VOIP: "voip",
    phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "personal_number",
    phonenumbers.PhoneNumberType.PAGER: "pager",
    phonenumbers.PhoneNumberType.UAN: "uan",
    phonenumbers.PhoneNumberType.VOICEMAIL: "voicemail",
    phonenumbers.PhoneNumberType.UNKNOWN: "unknown",
}


def parse_phone_number(raw_number: str, default_region: str | None = None) -> dict[str, Any]:
    """Parse and inspect a phone number locally using libphonenumber."""
    parsed = phonenumbers.parse(raw_number.strip(), default_region)
    num_type = phonenumbers.number_type(parsed)
    return {
        "input": raw_number.strip(),
        "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        "international": phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        ),
        "valid": phonenumbers.is_valid_number(parsed),
        "possible": phonenumbers.is_possible_number(parsed),
        "country_code": parsed.country_code,
        "region_code": phonenumbers.region_code_for_number(parsed),
        "location": geocoder.description_for_number(parsed, "en") or None,
        "carrier": carrier.name_for_number(parsed, "en") or None,
        "timezones": list(timezone.time_zones_for_number(parsed)),
        "line_type": _NUMBER_TYPE_NAMES.get(num_type, "unknown"),
    }


def enrich_ipqualityscore(
    e164_number: str,
    *,
    api_key: str | None = None,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Optional phone reputation lookup via IPQualityScore."""
    key = api_key or get_secret("ipqualityscore_key")
    if not key:
        raise RuntimeError(
            "IPQualityScore API key not configured. "
            "Set XOSINT_IPQUALITYSCORE_KEY or add ipqualityscore_key "
            "under [secrets] in config.toml."
        )
    client = session or requests.Session()
    resp = client.get(
        f"https://ipqualityscore.com/api/json/phone/{key}/{e164_number}",
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()
