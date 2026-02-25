from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from unittest.mock import Mock
from src.extract.station_extract import fetch_station_data


def test_fetch_station_data_calls_client_with_correct_endpoint_and_params():
    client = Mock()
    client.get_json.return_value = {
        "meta": {"limit": 5},
        "items": [{"label": "HIPPER_PARK ROAD BRIDGE_E_202312"}],
    }

    station_ref = "HIPPER_PARK ROAD BRIDGE_E_202312"
    limit = 5

    result = fetch_station_data(client, station_ref, limit=limit)

    assert "items" in result
    assert result["items"][0]["label"] == "HIPPER_PARK ROAD BRIDGE_E_202312"

    client.get_json.assert_called_once()
    args, kwargs = client.get_json.call_args

    assert args[0] == "/id/stations.json"
    assert kwargs["params"]["search"] == station_ref
    assert kwargs["params"]["_limit"] == limit
    assert kwargs["params"]["_view"] == "default"