import requests
from typing import Any, Dict, Optional

class HttpClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        r = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=self.timeout)

        if r.status_code >= 400:
            raise requests.HTTPError(f"HTTP {r.status_code} for {r.url} :: {r.text[:300]}", response=r)

        return r.json()