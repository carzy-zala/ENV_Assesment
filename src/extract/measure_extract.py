from __future__ import annotations
from typing import Any, Dict, List
from utils.connection.http_client import HttpClient

def _norm_text(s: str) -> str:
    return " ".join((s or "").strip().lower().replace("-", " ").replace("_", " ").split())

def get_station_item(station_payload: Dict[str, Any]) -> Dict[str, Any]:
    items = station_payload.get("items") or []
    if not items:
        raise RuntimeError("Station payload has no items[]")
    return items[0]

def get_available_observed_properties(station_item: Dict[str, Any]) -> List[str]:
    props = station_item.get("observedProperty") or []
    out = []
    for p in props:
        pid = (p or {}).get("@id", "")
        if pid:
            last = pid.rstrip("/").split("/")[-1]  # e.g. dissolved-oxygen
            out.append(_norm_text(last))           # -> "dissolved oxygen"
    return out

def validate_requested_parameters(station_item: Dict[str, Any], requested_params: List[str]) -> None:
    available = set(get_available_observed_properties(station_item))
    missing = [rp for rp in requested_params if _norm_text(rp) not in available]
    if missing:
        raise RuntimeError(
            f"Requested parameter(s) not available at this station: {missing}. "
            f"Available: {sorted(available)}"
        )

def resolve_all_measure_ids_from_station(
    station_item: Dict[str, Any],
    requested_params: List[str],
) -> Dict[str, List[str]]:
    """
    Returns {param_norm: [measure_id1, measure_id2, ...]}
    If a parameter has multiple measures (e.g. DO mgL + pct), returns all of them.
    """
    measures = station_item.get("measures") or []
    if not measures:
        raise RuntimeError("Station item has no measures[]")

    # Group measures by normalized measure['parameter'] (data-driven)
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for m in measures:
        p = _norm_text(m.get("parameter", ""))
        if p:
            grouped.setdefault(p, []).append(m)

    out: Dict[str, List[str]] = {}
    for rp in requested_params:
        rp_norm = _norm_text(rp)
        candidates = grouped.get(rp_norm, [])
        if not candidates:
            raise RuntimeError(f"No measures found for requested parameter: {rp}")

        # return stable ordering
        ids = sorted([c["@id"].rstrip("/").split("/")[-1] for c in candidates])
        out[rp_norm] = ids

    return out

def fetch_latest_readings(client: HttpClient, measure_id: str, limit: int = 10) -> Dict[str, Any]:
    endpoint = f"/id/measures/{measure_id}/readings.json"
    params = {"_sort": "-dateTime", "_limit": limit, "_view": "full"}
    return client.get_json(endpoint, params=params)

def validate_and_fetch_latest_all_units(
    client: HttpClient,
    station_payload: Dict[str, Any],
    requested_params: List[str],
    limit: int = 10,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Returns:
      {
        "dissolved oxygen": {
            "<measure_id>": <readings_json>,
            "<measure_id>": <readings_json>,
        },
        "conductivity": {
            "<measure_id>": <readings_json>
        }
      }
    """
    station_item = get_station_item(station_payload)

    # 1) validate availability
    validate_requested_parameters(station_item, requested_params)

    # 2) resolve ALL measure ids per parameter
    measure_ids = resolve_all_measure_ids_from_station(station_item, requested_params)

    # 3) fetch latest readings for each measure id
    out: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for param_norm, ids in measure_ids.items():
        out[param_norm] = {}
        for mid in ids:
            out[param_norm][mid] = fetch_latest_readings(client, mid, limit=limit)

    return out