from flask import Flask, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

artists_df = None

# Load dataset once
def load_artists_data():
    global artists_df
    if artists_df is not None:
        return artists_df
    
    try:
        csv_path = os.path.join("public", "Artisans.csv")
        df = pd.read_csv(csv_path).fillna("")
        
        # Normalize age
        if "age" in df.columns:
            df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(0).astype(int)
        
        # Languages → list
        if "languages" in df.columns:
            df["languages"] = df["languages"].apply(
                lambda x: [lang.strip().lower() for lang in str(x).split(",") if lang.strip()]
            )
        
        # Phone availability
        if "phone_available" in df.columns:
            df["phone_available"] = df["phone_available"].apply(lambda x: str(x).lower() == "yes")
        
        artists_df = df
        print(f"Loaded {len(df)} artists for Similar API")
        return df
    except Exception as e:
        print("Error loading CSV:", e)
        return pd.DataFrame()

@app.route("/similar", methods=["GET"])
def similar_artists():
    df = load_artists_data()
    if df.empty:
        return jsonify({"error": "No data available"}), 500

    artist_id = request.args.get("artistId")
    limit = int(request.args.get("limit", 5))

    if not artist_id:
        return jsonify({"error": "Artist ID is required"}), 400

    # Find target artist
    target_artist = df[df["id"].astype(str) == str(artist_id)]
    if target_artist.empty:
        return jsonify({"error": "Artist not found"}), 404

    target = target_artist.iloc[0]

    # Similarity filter: craft type > state > cluster
    def is_similar(a):
        if str(a["id"]) == str(artist_id):
            return False
        if a["craft_type"] == target["craft_type"]:
            return True
        if a["state"] == target["state"]:
            return True
        if a["cluster_code"] and target["cluster_code"] and a["cluster_code"] == target["cluster_code"]:
            return True
        return False

    similar = df[df.apply(is_similar, axis=1)].copy()

    # Sort: craft type match first, then state match
    def sort_key(a):
        return (
            a["craft_type"] != target["craft_type"],
            a["state"] != target["state"]
        )
    similar_sorted = similar.sort_values(by=["craft_type", "state"], key=lambda col: col != target[col.name])

    response = {
        "similar_artists": similar_sorted.head(limit).to_dict(orient="records"),
        "total_found": len(similar_sorted),
        "target_artist": target.to_dict(),
        "status": "online"
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
