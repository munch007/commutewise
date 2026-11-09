# CommuteWise — ambitious redesign

A refreshed Streamlit interface for the existing Pune PMPML GTFS project.

## What's changed
- Product-style visual system, responsive layout, custom typography and reusable metric cards.
- Dedicated Overview, Plan a commute, Route explorer and Scoring methodology workspaces.
- Searchable stop selectors and ordered origin → destination matching.
- Interactive OpenStreetMap route display using Plotly's `line_map`.
- Safer GTFS loading, missing-file/column checks, empty-data handling and more robust route matching.
- Explicit explanation of what the score and GTFS trip counts do — and do not — mean.

## Install and run
Use Python 3.10 or newer.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Required data
Keep the existing GTFS files in `data/`:
- `routes.txt`
- `trips.txt`
- `stops.txt`
- `stop_times.txt`

This redesign ZIP intentionally does not replace or redistribute the dataset. Copy these files from your existing repository into the `data/` directory.

## Deploy on Streamlit Community Cloud
1. Replace the corresponding Python files in your GitHub repository with these versions.
2. Keep the existing `data/` directory and its four GTFS files.
3. Commit and push to the branch configured in Streamlit Community Cloud.
4. In the app's settings, reboot the app if it does not redeploy automatically.

## Important modelling notes
- Route patterns are represented by the longest available trip for each route and direction.
- Distances are Haversine distances between consecutive stop coordinates, not road-network distances.
- GTFS trip counts are dataset records, not live bus frequency or real-time arrivals.
- Convenience scores are relative, min-max normalized scores for the routes returned by a particular search. They are not official PMPML ratings.
