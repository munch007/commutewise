"""Load the subset of PMPML GTFS tables used by CommuteWise."""
from pathlib import Path
import pandas as pd

REQUIRED = {
    "routes": ["route_id", "route_short_name", "route_long_name"],
    "trips": ["route_id", "trip_id", "direction_id"],
    "stops": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
    "stop_times": ["trip_id", "stop_id", "stop_sequence"],
}

OPTIONAL = {
    "trips": ["trip_headsign"],
    "stop_times": ["arrival_time", "departure_time"],
}


def load_gtfs(folder="data"):
    base = Path(folder)
    data = {}
    missing = []

    for table, required_columns in REQUIRED.items():
        path = base / f"{table}.txt"
        if not path.exists():
            missing.append(str(path))
            continue

        wanted = required_columns + OPTIONAL.get(table, [])
        frame = pd.read_csv(
            path,
            usecols=lambda column: column in wanted,
            low_memory=False,
            dtype={"route_short_name": "string"} if table == "routes" else None,
        )
        absent = sorted(set(required_columns) - set(frame.columns))
        if absent:
            raise ValueError(
                f"{path} is missing required columns: {', '.join(absent)}"
            )
        data[table] = frame.copy()

    if missing:
        raise FileNotFoundError(
            "Missing GTFS file(s): " + ", ".join(missing)
            + ". Add routes.txt, trips.txt, stops.txt and stop_times.txt to the data/ folder."
        )

    for table, column in [
        ("routes", "route_id"),
        ("trips", "route_id"),
        ("trips", "trip_id"),
        ("stop_times", "trip_id"),
        ("stop_times", "stop_id"),
        ("stops", "stop_id"),
    ]:
        data[table][column] = data[table][column].astype(str)

    data["stop_times"]["stop_sequence"] = pd.to_numeric(
        data["stop_times"]["stop_sequence"], errors="coerce"
    )
    data["stops"]["stop_lat"] = pd.to_numeric(
        data["stops"]["stop_lat"], errors="coerce"
    )
    data["stops"]["stop_lon"] = pd.to_numeric(
        data["stops"]["stop_lon"], errors="coerce"
    )
    data["trips"]["direction_id"] = (
        data["trips"]["direction_id"].fillna(0).astype(str)
    )
    data["routes"]["route_short_name"] = (
        data["routes"]["route_short_name"].fillna("").astype(str).str.strip()
    )
    data["routes"]["route_long_name"] = (
        data["routes"]["route_long_name"]
        .fillna(data["routes"]["route_short_name"])
        .astype(str)
    )
    data["stops"]["stop_name"] = (
        data["stops"]["stop_name"].fillna("Unnamed stop").astype(str)
    )

    # Older or partial GTFS feeds may omit timetable fields. Keep the app usable,
    # but the timetable page will explain that scheduled times are unavailable.
    for column in ("arrival_time", "departure_time"):
        if column not in data["stop_times"].columns:
            data["stop_times"][column] = pd.NA
        else:
            data["stop_times"][column] = (
                data["stop_times"][column].astype("string").str.strip()
            )

    if "trip_headsign" not in data["trips"].columns:
        data["trips"]["trip_headsign"] = ""
    else:
        data["trips"]["trip_headsign"] = (
            data["trips"]["trip_headsign"].fillna("").astype(str)
        )

    return data