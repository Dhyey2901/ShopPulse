from include.holidays import parse_holidays_response

SAMPLE_RESPONSE = [
    {
        "date": "2026-01-01",
        "localName": "New Year's Day",
        "name": "New Year's Day",
        "countryCode": "AU",
    },
    {
        "date": "2026-01-26",
        "localName": "Australia Day",
        "name": "Australia Day",
        "countryCode": "AU",
    },
]


def test_parse_holidays_response_shapes_rows_for_bigquery():
    rows = parse_holidays_response(SAMPLE_RESPONSE, 2026)

    assert rows == [
        {
            "date": "2026-01-01",
            "local_name": "New Year's Day",
            "name": "New Year's Day",
            "country_code": "AU",
            "year": 2026,
        },
        {
            "date": "2026-01-26",
            "local_name": "Australia Day",
            "name": "Australia Day",
            "country_code": "AU",
            "year": 2026,
        },
    ]


def test_parse_holidays_response_handles_empty_year():
    assert parse_holidays_response([], 2026) == []
