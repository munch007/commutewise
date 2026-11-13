"""Helpers for displaying scheduled PMPML GTFS trips and stop times."""
import pandas as pd


def _time_sort_key(value):
    if pd.isna(value) or not str(value).strip():
        return float("inf")
    try:
        hours, minutes, seconds = [int(part) for part in str(value).split(":")]
        return hours * 3600 + minutes * 60 + seconds
    except (TypeError, ValueError):
        return float("inf")


def format_gtfs_time(value):
    """Format GTFS HH:MM:SS, including times after midnight (24+ hours)."""
    if pd.isna(value) or not str(value).strip():
        return "—"
    try:
        hours, minutes, _seconds = [int(part) for part in str(value).split(":")]
        day_offset, clock_hour = divmod(hours, 24)
        suffix = "AM" if clock_hour < 12 else "PM"
        display_hour = clock_hour % 12 or 12
        formatted = f"{display_hour:02d}:{minutes:02d} {suffix}"
        if day_offset:
            formatted += f" (+{day_offset} day)"
        return formatted
    except (TypeError, ValueError):
        return str(value)


def get_route_trip_summary(data, route_id, direction_id):
    """Return one row per scheduled trip for a route and direction."""
    trips = data["trips"].copy()
    trips = trips.loc[
        (trips["route_id"].astype(str) == str(route_id))
        & (trips["direction_id"].astype(str) == str(direction_id))
    ]
    if trips.empty:
        return pd.DataFrame()

    stop_times = data["stop_times"].merge(
        data["stops"][["stop_id", "stop_name"]], on="stop_id", how="left"
    )
    stop_times = stop_times.loc[stop_times["trip_id"].isin(trips["trip_id"])].copy()
    if stop_times.empty:
        return pd.DataFrame()

    stop_times = stop_times.sort_values(["trip_id", "stop_sequence"])
    rows = []
    for trip_id, group in stop_times.groupby("trip_id", sort=False):
        first = group.iloc[0]
        last = group.iloc[-1]
        headsign = trips.loc[trips["trip_id"] == trip_id, "trip_headsign"]
        rows.append({
            "trip_id": trip_id,
            "direction": headsign.iloc[0] if not headsign.empty and str(headsign.iloc[0]).strip() else f"Direction {direction_id}",
            "first_stop": first.get("stop_name", "—"),
            "first_departure_raw": first.get("departure_time", pd.NA),
            "last_stop": last.get("stop_name", "—"),
            "last_arrival_raw": last.get("arrival_time", pd.NA),
        })

    result = pd.DataFrame(rows)
    result["_sort"] = result["first_departure_raw"].map(_time_sort_key)
    result = result.sort_values(["_sort", "trip_id"]).drop(columns="_sort")
    result["Start time"] = result["first_departure_raw"].map(format_gtfs_time)
    result["Destination time"] = result["last_arrival_raw"].map(format_gtfs_time)
    return result.reset_index(drop=True)


def get_trip_stop_times(data, trip_id):
    """Return the ordered stop-by-stop times for a single GTFS trip."""
    rows = data["stop_times"].loc[
        data["stop_times"]["trip_id"].astype(str) == str(trip_id)
    ].copy()
    if rows.empty:
        return pd.DataFrame()
    rows = rows.merge(data["stops"][["stop_id", "stop_name"]], on="stop_id", how="left")
    rows = rows.sort_values("stop_sequence")
    result = pd.DataFrame({
        "Stop sequence": rows["stop_sequence"],
        "Stop": rows["stop_name"],
        "Arrival": rows["arrival_time"].map(format_gtfs_time),
        "Departure": rows["departure_time"].map(format_gtfs_time),
    })
    return result.reset_index(drop=True)
