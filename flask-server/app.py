from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import pandas as pd
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])

data = None

def load_data():
    global data
    csv_path = os.getenv("CSV_PATH", r"C:\Users\hanis\OneDrive\Desktop\Team Tubelight\Local-Artisian_AI\Local-Artisian_AI\flask-server\frontend\src\Artisans.csv")
    try:
        data = pd.read_csv(csv_path)
        data = data.dropna(subset=['name', 'craft_type', 'state', 'district'])
        data['languages_spoken'] = data['languages_spoken'].fillna('')
        data['contact_phone'] = data['contact_phone'].astype(str)
        print(f"Loaded {len(data)} artisan records")
    except Exception as e:
        print(f"Error loading data: {e}")
        data = pd.DataFrame()

load_data()

@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Kala-Kaart Flask API is running!"})

@app.route("/health", methods=["GET"])
def health():
    if data is None or data.empty:
        return jsonify({"status": "unhealthy", "message": "Data not loaded"}), 503
    return jsonify({
        "status": "healthy",
        "total_artists": len(data),
        "database_loaded": True
    })

@app.route("/stats", methods=["GET"])
def stats():
    if data is None or data.empty:
        return jsonify({"message": "No data loaded"}), 503

    return jsonify({
        'total_artists': len(data),
        'unique_states': len(data['state'].unique()),
        'unique_districts': len(data['district'].unique()),
        'unique_crafts': len(data['craft_type'].unique()),
        'states': sorted(data['state'].unique().tolist()),
        'crafts': sorted(data['craft_type'].unique().tolist()),
        'age_distribution': {
            'min': int(data['age'].min()),
            'max': int(data['age'].max()),
            'mean': float(data['age'].mean())
        }
    })

@app.route("/search", methods=["POST"])
def search():
    filters = request.json
    filtered_df = data.copy()

    if 'state' in filters:
        filtered_df = filtered_df[filtered_df['state'].str.contains(filters['state'], case=False, na=False)]
    if 'district' in filters:
        filtered_df = filtered_df[filtered_df['district'].str.contains(filters['district'], case=False, na=False)]
    if 'craft_type' in filters:
        filtered_df = filtered_df[filtered_df['craft_type'].str.contains(filters['craft_type'], case=False, na=False)]
    if 'name' in filters:
        filtered_df = filtered_df[filtered_df['name'].str.contains(filters['name'], case=False, na=False)]
    if 'age_min' in filters:
        filtered_df = filtered_df[filtered_df['age'] >= filters['age_min']]
    if 'age_max' in filters:
        filtered_df = filtered_df[filtered_df['age'] <= filters['age_max']]

    limit = filters.get('limit', 20)
    artists = filtered_df.head(limit).to_dict('records')

    return jsonify({
        "artists": artists,
        "total_count": len(filtered_df),
        "filters_applied": {k: v for k, v in filters.items() if v is not None}
    })

@app.route("/chat", methods=["POST"])
def chat():
    message = request.json.get("message", "")
    
    # TODO: Integrate RAG chatbot logic here
    response = {
        "intent": "general_query",
        "entities": {},
        "message": "Flask API mode: Chat functionality not yet connected to RAG.",
        "artists": [],
        "suggestions": ["Try searching by state", "Try searching by craft", "Browse all artists"]
    }
    
    return jsonify(response)

