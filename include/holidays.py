"""Nager.Date public holidays API client, kept separate from the DAG so it's unit-testable."""
import requests

API_BASE = "https://date.nager.at/api/v3/PublicHolidays"


def fetch_holidays(year: int, country_code: str) -> list[dict]:
    """Fetch one year of public holidays and shape rows for the raw.holidays table."""
    resp = requests.get(f"{API_BASE}/{year}/{country_code}", timeout=30)
    resp.raise_for_status()
    return parse_holidays_response(resp.json(), year)


def parse_holidays_response(holidays: list[dict], year: int) -> list[dict]:
    return [
        {
            "date": h["date"],
            "local_name": h["localName"],
            "name": h["name"],
            "country_code": h["countryCode"],
            "year": year,
        }
        for h in holidays
    ]
