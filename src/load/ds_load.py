import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from utils.connection.db import init_raw_table, insert_raw_payload, delete_datasets
from utils.connection.http_client import HttpClient

from src.extract.station_extract import fetch_station_data
from src.extract.measure_extract import validate_and_fetch_latest_all_units


def extract_and_load_ds(
    conn,
    client: HttpClient,
    station_ref: str,
    requested_params: List[str],
    limit: int = 10,
    append_mode: bool = True,
) -> Dict[str, Any]:

    init_raw_table(conn)

    # single ingestion timestamp for this run
    ingested_at = datetime.now(timezone.utc).isoformat()

    # overwrite logic
    if not append_mode:
        conn.execute("DELETE FROM raw_landing WHERE dataset LIKE 'readings_latest%'")
        delete_datasets(conn, ["station_search"])

    # ---- Station (raw) ----
    station_payload = fetch_station_data(client, station_ref, limit=5)
    insert_raw_payload(
        conn,
        "station_search",
        json.dumps(station_payload, ensure_ascii=False),
        ingested_at=ingested_at,
    )

    # ---- Readings (raw) ----
    readings_map = validate_and_fetch_latest_all_units(
        client=client,
        station_payload=station_payload,
        requested_params=requested_params,
        limit=limit,
    )

    inserted = 1
    for param_norm, measure_dict in readings_map.items():
        for measure_id, readings_payload in measure_dict.items():
            dataset_name = f"readings_latest__{param_norm.replace(' ', '_')}__{measure_id}"

            insert_raw_payload(
                conn,
                dataset_name,
                json.dumps(readings_payload, ensure_ascii=False),
                ingested_at=ingested_at,
            )
            inserted += 1

    return {
        "raw_rows_inserted": inserted,
        "ingested_at": ingested_at,
    }