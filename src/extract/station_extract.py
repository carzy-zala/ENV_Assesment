from utils.connection.http_client import HttpClient


def fetch_station_data(client: HttpClient, station_ref: str, limit: int = 5) -> dict:
    """
    Calls the Hydrology API to search for a station by name/reference.

    Returns the full JSON response from the API.
    """
    endpoint = "/id/stations.json"

    params = {
        "search": station_ref,
        "_limit": limit,
         "_view": "default",
    }

    data = client.get_json(endpoint, params=params)
    return data