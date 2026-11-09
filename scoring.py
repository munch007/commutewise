"""Transparent, project-defined convenience score (not an official PMPML rating)."""
WEIGHTS = {"stops": 0.4, "distance": 0.3, "trips": 0.3}

def to_score(series, higher_is_better):
    values = series.fillna(series.median() if series.notna().any() else 0)
    low, high = values.min(), values.max()
    if high == low:
        return values * 0 + 100
    scaled = (values-low)/(high-low)*100
    return scaled if higher_is_better else 100-scaled

def add_convenience_score(df):
    if df.empty:
        return df.copy()
    out = df.copy()
    out["stops_score"] = to_score(out["stops_between"], False)
    out["distance_score"] = to_score(out["distance_km"], False)
    out["trips_score"] = to_score(out["trips"], True)
    out["convenience_score"] = (
        WEIGHTS["stops"]*out["stops_score"] +
        WEIGHTS["distance"]*out["distance_score"] +
        WEIGHTS["trips"]*out["trips_score"]
    ).round(1)
    return out.sort_values(["convenience_score","distance_km"],ascending=[False,True]).reset_index(drop=True)

def recommendation_text(df):
    if df.empty:
        return "No direct route found between these areas."
    best = df.iloc[0]
    return (f"{best['route_name']} ranks highest in this comparison "
            f"({best['convenience_score']}/100): {int(best['stops_between'])} stops, "
            f"about {best['distance_km']} km and {int(best['trips'])} trips in the GTFS feed. "
            "This is a project-defined score, not an official PMPML rating.")
