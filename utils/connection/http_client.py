import requests
from typing import Any, Dict, Optional

class HttpClient:
    """
    Thin wrapper around requests so HTTP behavior is centralized.
    Keeps timeout + JSON parsing consistent across the project.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        r = requests.get(
            url,
            params=params,
            headers={"Accept": "application/json"},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()