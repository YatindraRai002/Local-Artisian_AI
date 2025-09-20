# Path: /Users/abhi/Desktop/Local-Artisian_AI/flask-server/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pandas as pd
import logging
import traceback
from typing import Dict, List, Any
import numpy as np # Import numpy for integer conversion

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Initialize Gemini AI
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)
try:
    model = genai.GenerativeModel("gemini-1.5-pro")
except Exception as e:
    logger.warning(f"Failed to initialize gemini-1.5-pro, trying gemini-pro: {e}")
    model = genai.GenerativeModel("gemini-pro")

# Load CSV data
df = pd.DataFrame()
try:
    csv_paths = [
        os.path.join(os.getcwd(), 'public', 'Artisans.csv'),
        os.path.join(os.path.dirname(__file__), '..', 'public', 'Artisans.csv'),
        os.path.join(os.path.dirname(__file__), 'Artisans.csv')
    ]
    
    csv_loaded = False
    for csv_path in csv_paths:
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            logger.info(f"✅ Successfully loaded {len(df)} records from {csv_path}")
            csv_loaded = True
            break
    
    if not csv_loaded:
        logger.error("❌ Could not find Artisans.csv file in any of the expected locations.")
        df = pd.DataFrame()
    else:
        if 'age' in df.columns:
            df['age'] = pd.to_numeric(df['age'], errors='coerce')
        phone_columns = [col for col in df.columns if 'phone' in col.lower()]
        for col in phone_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'\.\d+', '', regex=True)
                df[col] = df[col].apply(lambda x: f"{int(float(x))}" if pd.notna(x) and x.replace('.', '', 1).isdigit() else '')
        
        searchable_cols = [col for col in ['name', 'craft_type', 'state', 'district', 'village', 'languages_spoken', 'languages'] if col in df.columns]
        if searchable_cols:
            df['search_text'] = df[searchable_cols].fillna('').astype(str).agg(' '.join, axis=1).str.lower()
        else:
            df['search_text'] = ''

except Exception as e:
    logger.error(f"❌ Error loading and processing CSV: {e}")
    logger.error(traceback.format_exc())
    df = pd.DataFrame()

# Helper Functions
def classify_intent(query: str) -> str:
    query_lower = query.lower()
    if any(word in query_lower for word in ['statistics', 'stats', 'count', 'how many', 'total', 'number', 'unique']):
        return 'statistics'
    elif any(word in query_lower for word in ['find', 'search', 'show', 'list', 'get', 'display']):
        return 'search'
    elif any(word in query_lower for word in ['help', 'what can you do', 'commands', 'options']):
        return 'help'
    return 'general'

def extract_entities_from_query(query: str) -> Dict[str, Any]:
    entities = {}
    query_lower = query.lower()
    craft_keywords = ['pottery', 'textile', 'weaving', 'embroidery', 'woodwork', 'metalwork']
    for craft in craft_keywords:
        if craft in query_lower:
            entities['craft_type'] = craft
            break
    return entities

def search_artisans(query: str, max_results: int = 10) -> List[Dict]:
    if df.empty: return []
    query_lower = query.lower()
    search_terms = [word for word in query_lower.split() if len(word) > 2]
    
    # Handle broad search gracefully
    if not search_terms and not query:
        matching_rows = df.head(max_results)
    else:
        combined_mask = pd.Series([False] * len(df))
        if 'search_text' in df.columns:
            for term in search_terms:
                combined_mask |= df['search_text'].str.contains(term, na=False, regex=False)
        
        matching_rows = df[combined_mask].head(max_results)
    
    results = []
    for _, row in matching_rows.iterrows():
        artist_data = {
            'artisan_id': str(row.get('artisan_id', row.get('govt_artisan_id', row.get('id', 'N/A')))),
            'name': row.get('name', 'Unknown'),
            'gender': row.get('gender', 'N/A'),
            'age': int(row.get('age')) if pd.notna(row.get('age')) else 'N/A', # Convert age to int
            'craft_type': row.get('craft_type', 'Traditional Craft'),
            'state': row.get('state', 'Unknown'),
            'district': row.get('district', 'Unknown'),
            'village': row.get('village', 'Unknown'),
            'languages': row.get('languages_spoken', row.get('languages', 'Hindi')),
            'email': row.get('contact_email', 'Not available'),
            'phone': row.get('contact_phone', 'Not available'),
            'phone_available': row.get('contact_phone_boolean', True),
            'govt_id': row.get('govt_artisan_id', 'N/A'),
            'cluster_code': row.get('artisan_cluster_code', 'N/A')
        }
        results.append(artist_data)
    return results

def get_statistics_from_df() -> Dict:
    if df.empty: return {"error": "No CSV data loaded"}
    stats = {'total_artisans': len(df)}
    for col in ['craft_type', 'state', 'district', 'gender']:
        if col in df.columns:
            stats[col + 's'] = {str(k): int(v) for k, v in df[col].value_counts().head(10).items()}
    if 'age' in df.columns and pd.api.types.is_numeric_dtype(df['age']):
        stats['age_statistics'] = {
            'average_age': round(float(df['age'].mean()), 1),
            'median_age': float(df['age'].median()),
            'min_age': int(df['age'].min()),
            'max_age': int(df['age'].max())
        }
    return stats

def filter_artisans_from_df(filters: Dict) -> List[Dict]:
    if df.empty: return []
    filtered_df = df.copy()
    for key, value in filters.items():
        if key in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[key].astype(str).str.lower() == str(value).lower()]
    
    results = []
    for _, row in filtered_df.head(20).iterrows():
        results.append({
            'artisan_id': str(row.get('artisan_id', row.get('govt_artisan_id', row.get('id', 'N/A')))),
            'name': row.get('name', 'Unknown'),
            'craft_type': row.get('craft_type', 'Traditional Craft'),
            'state': row.get('state', 'Unknown'),
            'district': row.get('district', 'Unknown'),
            'age': int(row.get('age')) if pd.notna(row.get('age')) else 'N/A',
            'gender': row.get('gender', 'N/A')
        })
    return results

def get_similar_artisans_from_df(artisan_id: str, limit: int) -> Dict:
    if df.empty: return {}
    target = df[df['artisan_id'].astype(str) == artisan_id].iloc[0] if 'artisan_id' in df.columns else None
    if target is None: return {}

    similar_df = df[
        (df['craft_type'] == target['craft_type']) &
        (df['state'] == target['state']) &
        (df['artisan_id'].astype(str) != artisan_id)
    ].head(limit)
    
    similar_artists = []
    for _, row in similar_df.iterrows():
        similar_artists.append({
            'artisan_id': str(row.get('artisan_id', 'N/A')),
            'name': row.get('name', 'Unknown'),
            'craft_type': row.get('craft_type', 'Traditional Craft'),
            'state': row.get('state', 'Unknown'),
            'district': row.get('district', 'Unknown')
        })
        
    return {
        'similar_artists': similar_artists,
        'reference_artisan': {
            'artisan_id': str(target.get('artisan_id', 'N/A')),
            'name': target.get('name', 'Unknown'),
            'craft_type': target.get('craft_type', 'Traditional Craft')
        }
    }

# --- API Routes ---

@app.route('/', methods=['GET'])
def health_check():
    try:
        data_status = "loaded" if not df.empty else "not loaded"
        return jsonify({
            'status': 'healthy',
            'message': 'Kala-Kaart AI Assistant API is running',
            'data_status': data_status,
            'total_artisans': len(df) if not df.empty else 0,
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        query = data.get('message', '')
        
        if df.empty:
            raise ValueError("CSV data not loaded on the server.")

        intent = classify_intent(query)
        entities = extract_entities_from_query(query)
        
        artists = []
        stats = {}
        llm_message = ""
        suggestions = []

        if intent == 'statistics':
            stats = get_statistics_from_df()
            llm_message = "Here are the database statistics you requested."
            suggestions = ["Show craft types", "Artists by state", "Gender distribution"]
        elif intent == 'search' or intent == 'general':
            artists = search_artisans(query, max_results=5)
            if artists:
                llm_message = f"Found {len(artists)} artisan(s) matching your query."
                suggestions = ["Find similar artists", "Search by location", "Browse other crafts"]
            else:
                llm_message = "I couldn't find any artisans matching that query. Please try another one."
                suggestions = ["Browse craft types", "Find artists in a specific state", "Get general statistics"]
        else: # help or unknown intent
            llm_message = "Hello! I am a RAG AI assistant. I can help you search for artisans by craft, location, or name. You can also ask for database statistics."
            suggestions = ["Show me pottery artists", "Find artists in Rajasthan", "Get database statistics"]

        response = {
            'intent': intent,
            'entities': entities,
            'message': llm_message,
            'artists': artists,
            'suggestions': suggestions,
            'stats': stats,
            'status': 'success'
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'Failed to process your request. Please try again.',
            'llm_message': '🔴 Error: Backend server encountered an internal error. Check logs for details.',
            'artists': [], 'suggestions': [], 'stats': {}
        }), 500

@app.route('/api/search', methods=['POST'])
def search_artisans_endpoint():
    try:
        data = request.get_json()
        query = data.get('query', '')
        max_results = data.get('max_results', 10)
        
        # Pass a default query to handle empty post requests
        artists = search_artisans(query, max_results)
        
        return jsonify({
            'artists': artists,
            'total': len(artists),
            'query': query
        })
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        return jsonify({'error': 'Search failed'}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics_endpoint():
    try:
        stats = get_statistics_from_df()
        return jsonify({
            'stats': stats,
            'message': 'Database statistics retrieved successfully'
        })
    except Exception as e:
        logger.error(f"Statistics endpoint error: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@app.route('/api/filter', methods=['POST'])
def filter_artisans_endpoint():
    try:
        data = request.get_json()
        filters = data or {}
        artists = filter_artisans_from_df(filters)
        return jsonify({
            'artists': artists,
            'total': len(artists),
            'filters_applied': filters
        })
    except Exception as e:
        logger.error(f"Filter endpoint error: {e}")
        return jsonify({'error': 'Filter failed'}), 500

def get_statistics_from_df() -> Dict:
    if df.empty: return {"error": "No CSV data loaded"}
    stats = {'total_artisans': len(df)}
    for col in ['craft_type', 'state', 'district', 'gender']:
        if col in df.columns:
            stats[col + 's'] = {str(k): int(v) for k, v in df[col].value_counts().head(10).items()}
    if 'age' in df.columns and pd.api.types.is_numeric_dtype(df['age']):
        stats['age_statistics'] = {
            'average_age': round(float(df['age'].mean()), 1),
            'median_age': float(df['age'].median()),
            'min_age': int(df['age'].min()),
            'max_age': int(df['age'].max())
        }
    
    # --- ADDED LINES TO FIX THE 0+ COUNTS ---
    if 'craft_type' in df.columns:
        stats['unique_crafts'] = int(df['craft_type'].nunique())

    if 'state' in df.columns:
        stats['unique_states'] = int(df['state'].nunique())
    # --- END OF ADDED LINES ---
    
    return stats

@app.route('/api/similar/<artisan_id>', methods=['GET'])
def get_similar_artists_endpoint(artisan_id):
    try:
        limit = request.args.get('limit', 5, type=int)
        similar_data = get_similar_artisans_from_df(artisan_id, limit)
        if not similar_data:
            return jsonify({'error': 'Artisan or similar artists not found'}), 404
        return jsonify(similar_data)
    except Exception as e:
        logger.error(f"Similar artists endpoint error: {e}")
        return jsonify({'error': 'Failed to find similar artisans'}), 500

@app.route('/api/unique-values/<column>', methods=['GET'])
def get_unique_values_endpoint(column):
    try:
        if df.empty or column not in df.columns:
            return jsonify({'column': column, 'values': [], 'count': 0}), 404
        
        unique_values = df[column].dropna().unique().tolist()
        return jsonify({
            'column': column,
            'values': unique_values,
            'count': len(unique_values)
        })
    except Exception as e:
        logger.error(f"Unique values endpoint error: {e}")
        return jsonify({'error': 'Failed to get unique values'}), 500

if __name__ == '__main__':
    try:
        logger.info("\n🚀 Kala-Kaart AI Assistant API Starting...")
        logger.info("📡 Server will run on http://localhost:8000")
        logger.info("🔧 Debug mode: True")
        app.run(port=8000, debug=True, threaded=True)
    except Exception as e:
        logger.error(f"\n❌ Server startup failed: {e}")
        logger.error(traceback.format_exc())