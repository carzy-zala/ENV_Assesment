import pytest
from unittest.mock import patch, Mock

from utils.connection.http_client import HttpClient


def test_get_json_builds_correct_url_and_returns_json():
    client = HttpClient(base_url="https://example.com")

    fake_response = Mock()
    fake_response.json.return_value = {"hello": "world"}
    fake_response.raise_for_status.return_value = None

    with patch("utils.connection.http_client.requests.get", return_value=fake_response) as mock_get:
        result = client.get_json("/test", params={"a": 1})

        # verify result
        assert result == {"hello": "world"}

        # verify correct request call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args

        # URL should be base + path
        assert args[0] == "https://example.com/test"

        # params forwarded
        assert kwargs["params"] == {"a": 1}

        # JSON header present
        assert kwargs["headers"]["Accept"] == "application/json"


def test_get_json_raises_on_http_error():
    client = HttpClient(base_url="https://example.com")

    fake_response = Mock()
    fake_response.raise_for_status.side_effect = Exception("HTTP error")

    with patch("utils.connection.http_client.requests.get", return_value=fake_response):
        with pytest.raises(Exception):
            client.get_json("/fail")