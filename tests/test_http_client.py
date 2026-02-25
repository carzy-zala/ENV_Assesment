from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from unittest.mock import Mock, patch
import requests

from utils.connection.http_client import HttpClient


def test_get_json_success():
    client = HttpClient(base_url="https://example.com")

    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.url = "https://example.com/test"
    fake_response.text = ""
    fake_response.json.return_value = {"ok": True}

    with patch("utils.connection.http_client.requests.get", return_value=fake_response) as mock_get:
        data = client.get_json("/test", params={"a": 1})

    assert data == {"ok": True}
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert args[0] == "https://example.com/test"
    assert kwargs["params"] == {"a": 1}
    assert kwargs["headers"]["Accept"] == "application/json"


def test_get_json_raises_http_error_on_400():
    client = HttpClient(base_url="https://example.com")

    fake_response = Mock()
    fake_response.status_code = 400
    fake_response.url = "https://example.com/test"
    fake_response.text = "Bad Request"

    with patch("utils.connection.http_client.requests.get", return_value=fake_response):
        with pytest.raises(requests.HTTPError) as e:
            client.get_json("/test")

    assert "HTTP 400" in str(e.value)
    assert "Bad Request" in str(e.value)