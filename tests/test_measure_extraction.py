from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from unittest.mock import Mock
import pytest

from src.extract.measure_extract import (
    get_station_item,
    validate_requested_parameters,
    resolve_all_measure_ids_from_station,
    validate_and_fetch_latest_all_units,
)

def make_station_payload():
    return {
        "meta": {},
        "items": [{
            "label": "HIPPER_PARK ROAD BRIDGE_E_202312",
            "notation": "E64999A",
            "observedProperty": [
                {"@id": "http://environment.data.gov.uk/reference/def/op/dissolved-oxygen"},
                {"@id": "http://environment.data.gov.uk/reference/def/op/conductivity"},
            ],
            "measures": [
                {"@id": "http://environment.data.gov.uk/hydrology/id/measures/E64999A-do-i-subdaily-mgL", "parameter": "DISSOLVED OXYGEN"},
                {"@id": "http://environment.data.gov.uk/hydrology/id/measures/E64999A-do-i-subdaily-pct", "parameter": "DISSOLVED OXYGEN"},
                {"@id": "http://environment.data.gov.uk/hydrology/id/measures/E64999A-cond-i-subdaily-uS", "parameter": "CONDUCTIVITY"},
            ],
        }]
    }

def test_resolve_all_measure_ids_returns_all_do_units():
    item = get_station_item(make_station_payload())
    ids = resolve_all_measure_ids_from_station(item, ["dissolved oxygen", "conductivity"])

    assert "dissolved oxygen" in ids
    assert "conductivity" in ids
    assert len(ids["dissolved oxygen"]) == 2
    assert any(x.endswith("mgL") for x in ids["dissolved oxygen"])
    assert any(x.endswith("pct") for x in ids["dissolved oxygen"])
    assert ids["conductivity"][0].endswith("uS")

def test_validate_and_fetch_latest_all_units_calls_client_for_each_measure():
    client = Mock()
    # 3 measures total: DO mgL, DO pct, conductivity uS
    client.get_json.side_effect = [
        {"items": [{"dateTime": "2026-02-25T00:00:00Z", "value": 1.0}]},
        {"items": [{"dateTime": "2026-02-25T00:00:00Z", "value": 99.0}]},
        {"items": [{"dateTime": "2026-02-25T00:00:00Z", "value": 200.0}]},
    ]

    out = validate_and_fetch_latest_all_units(
        client,
        make_station_payload(),
        ["dissolved oxygen", "conductivity"],
        limit=10,
    )

    assert "dissolved oxygen" in out
    assert "conductivity" in out
    assert len(out["dissolved oxygen"]) == 2
    assert len(out["conductivity"]) == 1
    assert client.get_json.call_count == 3