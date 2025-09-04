from flask import Flask, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

artists_df = None

# Load CSV data
def load_artists_data():
    global artists_df
    if artists_df is not None:
        return artists_df
    
    try:
        csv_path = os.path.join("public", "Artisans.csv")
        df = pd.read_csv(csv_path).fillna("")
        
        # Normalize and fix types
        if "age" in df.columns:
            df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(0).astype(int)
        if "languages" in df.columns:
            df["languages"] = df["languages"].apply(lambda x: [lang.strip().lower() for lang in str(x).split(",") if lang.strip()])
        if "phone_available" in df.columns:
            df["phone_available"] = df["phone_available"].apply(lambda x: str(x).lower() == "yes")
        
        artists_df = df
        print(f"Loaded {len(df)} artists")
        return df
    except Exception as e:
        print("Error loading CSV:", e)
        return pd.DataFrame()

# --- Utility for filtering ---
def apply_filters(df, filters):
    results = df.copy()

    # State filter (simple version, you can extend with mappings later)
    if "state" in filters:
        results = results[results["state"].str.lower().str.contains(filters["state"].lower())]

    # District
    if "district" in filters:
        results = results[results["district"].str.lower().str.contains(filters["district"].lower())]

    # Craft type
    if "craft_type" in filters:
        results = results[results["craft_type"].str.lower().str.contains(filters["craft_type"].lower())]

    # Name
    if "name" in filters:
        results = results[results["name"].str.lower().str.contains(filters["name"].lower())]

    # Language
    if "language" in filters:
        results = results[results["languages"].apply(lambda langs: filters["language"].lower() in langs)]

    # Cluster code
    if "cluster_code" in filters:
        results = results[results["cluster_code"].str.lower().str.contains(filters["cluster_code"].lower())]

    # Age range
    if "age_min" in filters:
        results = results[results["age"] >= int(filters["age_min"])]
    if "age_max" in filters:
        results = results[results["age"] <= int(filters["age_max"])]

    # Gender
    if "gender" in filters:
        results = results[results["gender"].str.lower() == filters["gender"].lower()]

    # Phone availability
    if "phone_available" in filters:
        results = results[results["phone_available"] == bool(filters["phone_available"])]

    # Sorting
    if "sort_by" in filters:
        sort_field = filters["sort_by"]
        sort_order = filters.get("sort_order", "asc")
        ascending = sort_order == "asc"
        if sort_field in results.columns:
            results = results.sort_values(by=sort_field, ascending=ascending)

    return results

# --- API Route ---
@app.route("/search", methods=["POST"])
def search_artists():
    df = load_artists_data()
    if df.empty:
        return jsonify({"error": "No data available"}), 500
    
    filters = request.json or {}
    results = apply_filters(df, filters)

    # Pagination
    limit = int(filters.get("limit", 20))
    offset = int(filters.get("offset", 0))
    paginated = results.iloc[offset:offset+limit]

    # Stats
    stats = {
        "total_artists": len(results),
        "unique_states": results["state"].nunique(),
        "unique_districts": results["district"].nunique(),
        "unique_crafts": results["craft_type"].nunique(),
        "unique_clusters": results["cluster_code"].nunique(),
        "states_found": sorted(results["state"].unique().tolist()),
        "crafts_found": sorted(results["craft_type"].unique().tolist()),
        "age_range": {
            "min": int(results["age"].min()) if not results.empty else 0,
            "max": int(results["age"].max()) if not results.empty else 0,
        }
    }

    response = {
        "artists": paginated.to_dict(orient="records"),
        "total": len(results),
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < len(results),
        "status": "online",
        "search_metadata": {
            "filters_applied": list(filters.keys()),
            "available_states": sorted(df["state"].unique().tolist()),
            "search_statistics": stats
        }
    }

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
