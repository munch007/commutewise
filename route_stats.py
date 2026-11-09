"""Route statistics, representative stop patterns, and ordered stop matching."""
from math import radians, sin, cos, asin, sqrt
import pandas as pd

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 2 * 6371 * asin(sqrt(max(0, min(1, a))))

def build_route_stops(data):
    trips, stop_times, stops = data["trips"], data["stop_times"], data["stops"]
    trip_len = stop_times.groupby("trip_id").size().rename("n_stops").reset_index()
    candidates = trips.merge(trip_len, on="trip_id", how="inner")
    if candidates.empty:
        return pd.DataFrame(columns=["route_id","direction_id","stop_sequence","stop_name","stop_lat","stop_lon","cum_km"])
    # Select the longest available trip per route/direction as a representative pattern.
    best = candidates.sort_values(["n_stops","trip_id"], ascending=[False,True]).drop_duplicates(["route_id","direction_id"])
    rows = stop_times.merge(best[["trip_id","route_id","direction_id"]], on="trip_id", how="inner")
    rows = rows.merge(stops, on="stop_id", how="left")
    rows = rows.dropna(subset=["stop_sequence"]).sort_values(["route_id","direction_id","stop_sequence"]).reset_index(drop=True)
    grp = rows.groupby(["route_id","direction_id"], sort=False)
    prev_lat, prev_lon = grp["stop_lat"].shift(), grp["stop_lon"].shift()
    distances = []
    for lat, lon, plat, plon in zip(rows.stop_lat, rows.stop_lon, prev_lat, prev_lon):
        if pd.isna(lat) or pd.isna(lon) or pd.isna(plat) or pd.isna(plon):
            distances.append(0.0)
        else:
            distances.append(haversine(plat, plon, lat, lon))
    rows["seg_km"] = distances
    rows["cum_km"] = rows.groupby(["route_id","direction_id"])["seg_km"].cumsum()
    return rows

def count_trips(data):
    return data["trips"].groupby(["route_id","direction_id"]).size().rename("trips").reset_index()

def overview_table(data, route_stops):
    if route_stops.empty:
        return pd.DataFrame(columns=["route_id","route_short_name","route_long_name","n_stops","length_km","trips"])
    longest = route_stops.groupby("route_id").agg(
        n_stops=("stop_sequence","size"), length_km=("cum_km","max")
    ).reset_index()
    trips = data["trips"].groupby("route_id").size().rename("trips").reset_index()
    out = data["routes"].drop_duplicates("route_id").merge(longest,on="route_id",how="inner").merge(trips,on="route_id",how="left")
    return out.sort_values("n_stops",ascending=False).reset_index(drop=True)

def routes_between(data, route_stops, area_a, area_b):
    """Return every ordered matching origin/destination pair on a route direction."""
    a, b = str(area_a).strip().casefold(), str(area_b).strip().casefold()
    if not a or not b or a == b or route_stops.empty:
        return pd.DataFrame()
    trip_counts = count_trips(data)
    names = data["routes"].drop_duplicates("route_id").set_index("route_id")["route_long_name"].to_dict()
    results = []
    for (route_id, direction), group in route_stops.groupby(["route_id","direction_id"], sort=False):
        g = group.sort_values("stop_sequence").reset_index(drop=True)
        names_lower = g["stop_name"].fillna("").str.casefold()
        origins = [i for i, name in enumerate(names_lower) if a in name]
        destinations = [j for j, name in enumerate(names_lower) if b in name]
        # Evaluate all ordered pairs; retain the shortest matching segment for this direction.
        pairs = [(i,j) for i in origins for j in destinations if j > i]
        if not pairs:
            continue
        i,j = min(pairs, key=lambda pair: (pair[1]-pair[0], pair[0]))
        start_km, end_km = float(g["cum_km"].iloc[i]), float(g["cum_km"].iloc[j])
        results.append({
            "route_id": route_id, "direction_id": direction,
            "route_name": names.get(route_id, str(route_id)),
            "board_at": g["stop_name"].iloc[i], "get_off_at": g["stop_name"].iloc[j],
            "stops_between": int(j-i), "distance_km": round(max(0,end_km-start_km),2),
        })
    result = pd.DataFrame(results)
    if result.empty:
        return result
    result = result.merge(trip_counts,on=["route_id","direction_id"],how="left")
    return result.sort_values(["distance_km","stops_between"]).reset_index(drop=True)
