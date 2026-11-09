"""Load the subset of PMPML GTFS tables used by CommuteWise."""
from pathlib import Path
import pandas as pd

REQUIRED = {
    "routes": ["route_id", "route_short_name", "route_long_name"],
    "trips": ["route_id", "trip_id", "direction_id"],
    "stops": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
    "stop_times": ["trip_id", "stop_id", "stop_sequence"],
}

def load_gtfs(folder="data"):
    base = Path(folder)
    data = {}
    missing = []
    for table, columns in REQUIRED.items():
        path = base / f"{table}.txt"
        if not path.exists():
            missing.append(str(path))
            continue
        frame = pd.read_csv(path, usecols=lambda c: c in columns, low_memory=False)
        absent = sorted(set(columns) - set(frame.columns))
        if absent:
            raise ValueError(f"{path} is missing required columns: {', '.join(absent)}")
        data[table] = frame[columns].copy()
    if missing:
        raise FileNotFoundError(
            "Missing GTFS file(s): " + ", ".join(missing) +
            ". Add routes.txt, trips.txt, stops.txt and stop_times.txt to the data/ folder."
        )
    # Normalize types to make joins and sorting predictable.
    for table, col in [("routes","route_id"),("trips","route_id"),("trips","trip_id"),
                       ("stop_times","trip_id"),("stop_times","stop_id"),("stops","stop_id")]:
        data[table][col] = data[table][col].astype(str)
    data["stop_times"]["stop_sequence"] = pd.to_numeric(data["stop_times"]["stop_sequence"], errors="coerce")
    data["stops"]["stop_lat"] = pd.to_numeric(data["stops"]["stop_lat"], errors="coerce")
    data["stops"]["stop_lon"] = pd.to_numeric(data["stops"]["stop_lon"], errors="coerce")
    data["trips"]["direction_id"] = data["trips"]["direction_id"].fillna(0).astype(str)
    data["routes"]["route_long_name"] = data["routes"]["route_long_name"].fillna(data["routes"]["route_short_name"]).astype(str)
    data["stops"]["stop_name"] = data["stops"]["stop_name"].fillna("Unnamed stop").astype(str)
    return data
