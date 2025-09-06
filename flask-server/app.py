"""
Kala-Kaart AI Chatbot API
Merged Flask backend combining CSV data handling and RAG model functionality.
"""

from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import os
import pandas as pd
import logging
import json
import re

# -------------------------
# Logging Configuration
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# Flask App Initialization
# -------------------------
app = Flask(__name__)
CORS(app, 
     resources={
         r"/*": {
             "origins": ["http://localhost:5173", "http://localhost:3000"],
             "methods": ["GET", "POST", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"]
         }
     })

# -------------------------
# Global Variables
# -------------------------
data = None
rag_model = None

# -------------------------
# Data Loading Functions
# -------------------------
def load_data():
    """Load CSV data for artisan database"""
    global data
    csv_path = os.getenv("CSV_PATH", r"C:\Users\hanis\OneDrive\Desktop\Team Tubelight\Local-Artisian_AI\Local-Artisian_AI\flask-server\frontend\src\Artisans.csv")
    try:
        data = pd.read_csv(csv_path)
        data = data.dropna(subset=['name', 'craft_type', 'state', 'district'])
        data['languages_spoken'] = data['languages_spoken'].fillna('')
        data['contact_phone'] = data['contact_phone'].astype(str)
        logger.info(f"Loaded {len(data)} artisan records")
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        data = pd.DataFrame()

def initialize_rag_model():
    """Initialize RAG model if available"""
    global rag_model
    try:
        from backend.rag_nlp_model import MultilingualRAGModel
        
        MODEL_PATH = "trained_rag_model"
        USE_GPU = False
        
        rag_model = MultilingualRAGModel(use_gpu=USE_GPU)
        
        if os.path.exists(MODEL_PATH):
            rag_model.load_model(MODEL_PATH)
            logger.info("Loaded trained RAG model.")
        else:
            logger.warning("Trained RAG model not found. Please train the model first.")
            
    except ImportError:
        logger.warning("RAG model not available. Install required dependencies or check backend.rag_nlp_model")
        rag_model = None
    except Exception as e:
        logger.error(f"Error initializing RAG model: {e}")
        rag_model = None

# -------------------------
# Helper Functions for Chat
# -------------------------
def normalize_text(text):
    """Normalize text for better matching"""
    return re.sub(r'[^\w\s]', '', text.lower().strip())

def find_state_match(message, available_states):
    """Find state mentioned in message with fuzzy matching"""
    message_normalized = normalize_text(message)
    message_words = message_normalized.split()
    
    for state in available_states:
        state_normalized = normalize_text(state)
        state_words = state_normalized.split()
        
        # Exact match
        if state_normalized in message_normalized:
            return state
        
        # Word-by-word match for multi-word states
        if all(word in message_words for word in state_words if len(word) > 2):
            return state
    
    return None

def find_craft_match(message, available_crafts):
    """Find craft mentioned in message with keyword matching"""
    message_normalized = normalize_text(message)
    
    # Direct craft matching
    for craft in available_crafts:
        craft_normalized = normalize_text(craft)
        if craft_normalized in message_normalized:
            return craft
    
    # Keyword-based matching
    craft_keywords = {
        'pottery': ['pottery', 'potter', 'ceramic', 'clay', 'pot'],
        'weaving': ['weaving', 'textile', 'fabric', 'cloth', 'weaver'],
        'wood': ['wood', 'carving', 'wooden', 'carpenter'],
        'metal': ['metal', 'iron', 'steel', 'brass', 'copper'],
        'leather': ['leather', 'hide', 'skin'],
        'embroidery': ['embroidery', 'stitch', 'needle'],
        'painting': ['painting', 'paint', 'artist', 'canvas'],
        'jewelry': ['jewelry', 'jewel', 'ornament', 'gold', 'silver'],
        'basket': ['basket', 'bamboo', 'cane'],
        'stone': ['stone', 'marble', 'sculpture']
    }
    
    for craft_type, keywords in craft_keywords.items():
        if any(keyword in message_normalized for keyword in keywords):
            # Find matching crafts in database
            matching_crafts = [c for c in available_crafts if craft_type in normalize_text(c)]
            if matching_crafts:
                return matching_crafts[0]
    
    return None

# -------------------------
# Initialize on startup
# -------------------------
load_data()
initialize_rag_model()

# -------------------------
# Basic API Endpoints
# -------------------------
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    
@app.route("/", methods=["GET"])
def root():
    """Test endpoint to check if API is running"""
    return jsonify({"message": "Kala-Kaart Flask API is running!"})

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    if data is None or data.empty:
        return jsonify({"status": "unhealthy", "message": "Data not loaded"}), 503
    
    return jsonify({
        "status": "healthy",
        "total_artists": len(data),
        "database_loaded": True,
        "rag_model_loaded": rag_model is not None
    })

# -------------------------
# Data API Endpoints
# -------------------------

@app.route("/stats", methods=["GET"])
def stats():
    """Get database statistics"""
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
    """Search artisans with filters"""
    if data is None or data.empty:
        return jsonify({"message": "No data loaded"}), 503
        
    filters = request.json or {}
    filtered_df = data.copy()

    # Apply filters
    if 'state' in filters and filters['state']:
        filtered_df = filtered_df[filtered_df['state'].str.contains(filters['state'], case=False, na=False)]
    if 'district' in filters and filters['district']:
        filtered_df = filtered_df[filtered_df['district'].str.contains(filters['district'], case=False, na=False)]
    if 'craft_type' in filters and filters['craft_type']:
        filtered_df = filtered_df[filtered_df['craft_type'].str.contains(filters['craft_type'], case=False, na=False)]
    if 'name' in filters and filters['name']:
        filtered_df = filtered_df[filtered_df['name'].str.contains(filters['name'], case=False, na=False)]
    if 'age_min' in filters and filters['age_min']:
        filtered_df = filtered_df[filtered_df['age'] >= filters['age_min']]
    if 'age_max' in filters and filters['age_max']:
        filtered_df = filtered_df[filtered_df['age'] <= filters['age_max']]

    limit = filters.get('limit', 20)
    artists = filtered_df.head(limit).to_dict('records')

    return jsonify({
        "artists": artists,
        "total_count": len(filtered_df),
        "filters_applied": {k: v for k, v in filters.items() if v is not None and v != ""}
    })

# -------------------------
# RAG Model API Endpoints
# -------------------------

@app.route("/query", methods=["POST"])
def query():
    """
    Process a user query using RAG model.
    JSON body: {"query": "Your question here"}
    """
    data_req = request.json or {}
    user_input = data_req.get("query", "").strip()

    if not user_input:
        return jsonify({"error": "Query not provided"}), 400

    # If RAG model is not available, fall back to basic response
    if rag_model is None:
        return jsonify({
            "query": user_input,
            "language": "en",
            "response": "RAG model not available. Please check the model configuration.",
            "retrieved_docs": [],
            "fallback": True
        })

    try:
        # Detect language
        lang = rag_model.detect_language(user_input)
        # Semantic search
        docs = rag_model.semantic_search(user_input, lang)
        # Generate response
        response_text = rag_model.generate_response(user_input, docs, lang)

        return jsonify({
            "query": user_input,
            "language": lang,
            "response": response_text,
            "retrieved_docs": docs,
            "fallback": False
        })
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({"error": "Failed to process query"}), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Enhanced chat endpoint with flexible state and craft search"""
    data_req = request.json or {}
    message = data_req.get("message", "").strip()
    
    if not message:
        return jsonify({"error": "Message not provided"}), 400
    
    # Check if data is available
    if data is None or data.empty:
        return jsonify({
            "intent": "error",
            "entities": {},
            "message": "Database temporarily unavailable. Please try again later.",
            "artists": [],
            "suggestions": ["Check server connection", "Try again later"],
            "mode": "error"
        })
    
    try:
        # Get available states and crafts
        available_states = data['state'].unique().tolist()
        available_crafts = data['craft_type'].unique().tolist()
        
        # Find state and craft matches
        mentioned_state = find_state_match(message, available_states)
        mentioned_craft = find_craft_match(message, available_crafts)
        
        # Handle statistics requests
        if any(word in message.lower() for word in ['stats', 'statistics', 'database stats', 'how many']):
            total_artists = len(data)
            total_states = len(available_states)
            total_crafts = len(available_crafts)
            
            return jsonify({
                "intent": "get_statistics",
                "entities": {},
                "message": f"Our database contains {total_artists:,} verified artisans from {total_states} states practicing {total_crafts} different traditional crafts.",
                "artists": [],
                "suggestions": ["Browse by state", "Browse by craft", "Search specific artists"],
                "mode": "statistics",
                "stats": {
                    "total_artists": total_artists,
                    "total_states": total_states,
                    "total_crafts": total_crafts
                }
            })
        
        # Handle state searches
        if mentioned_state:
            state_artists = data[data['state'].str.contains(mentioned_state, case=False, na=False)].head(10)
            return jsonify({
                "intent": "search_location",
                "entities": {"state": mentioned_state},
                "message": f"Found {len(state_artists)} artists in {mentioned_state}. Here are some featured artisans from this region.",
                "artists": state_artists.to_dict('records'),
                "suggestions": [f"Find specific crafts in {mentioned_state}", "Show contact details", "Browse other states"],
                "mode": "database_search"
            })
        
        # Handle craft searches
        if mentioned_craft:
            craft_artists = data[data['craft_type'].str.contains(mentioned_craft, case=False, na=False)].head(10)
            return jsonify({
                "intent": "search_craft",
                "entities": {"craft": mentioned_craft},
                "message": f"Found {len(craft_artists)} {mentioned_craft} artists in our database.",
                "artists": craft_artists.to_dict('records'),
                "suggestions": [f"Find {mentioned_craft} in specific states", "Show contact details", "Browse other crafts"],
                "mode": "database_search"
            })
        
        # Handle browsing requests
        if any(word in message.lower() for word in ['browse states', 'which states', 'list states', 'show states']):
            states_list = sorted(available_states)[:15]
            return jsonify({
                "intent": "browse_states",
                "entities": {},
                "message": f"We have artisans from {len(available_states)} states: {', '.join(states_list[:10])}{'...' if len(states_list) > 10 else ''}",
                "artists": [],
                "suggestions": states_list[:5],
                "mode": "database_browse"
            })
        
        if any(word in message.lower() for word in ['browse crafts', 'what crafts', 'list crafts', 'show crafts']):
            crafts_list = sorted(available_crafts)[:15]
            return jsonify({
                "intent": "browse_crafts",
                "entities": {},
                "message": f"We have {len(available_crafts)} types of traditional crafts: {', '.join(crafts_list[:8])}{'...' if len(crafts_list) > 8 else ''}",
                "artists": [],
                "suggestions": crafts_list[:5],
                "mode": "database_browse"
            })
        
        # Handle contact/help requests
        if any(word in message.lower() for word in ['contact', 'phone', 'email', 'reach']):
            return jsonify({
                "intent": "contact_info",
                "entities": {},
                "message": "All artist profiles include contact information including phone numbers and email addresses. Use the search function to find specific artists and their contact details.",
                "artists": [],
                "suggestions": ["Search by state", "Search by craft", "Browse all artists"],
                "mode": "help"
            })
        
        # Handle greetings
        if any(word in message.lower() for word in ['hello', 'hi', 'hey', 'namaste']):
            return jsonify({
                "intent": "greeting",
                "entities": {},
                "message": "Namaste! Welcome to Kala-Kaart. I can help you discover traditional Indian artisans and their crafts. You can search by state, craft type, or browse our comprehensive database.",
                "artists": [],
                "suggestions": ["Browse by state", "Browse by craft", "Get database statistics"],
                "mode": "greeting"
            })
        
        # Try RAG model if available
        if rag_model is not None:
            try:
                lang = rag_model.detect_language(message)
                docs = rag_model.semantic_search(message, lang)
                response_text = rag_model.generate_response(message, docs, lang)
                
                return jsonify({
                    "intent": "rag_query",
                    "entities": {},
                    "message": response_text,
                    "language": lang,
                    "artists": [],
                    "suggestions": ["Try searching by state", "Try searching by craft", "Browse all artists"],
                    "mode": "rag"
                })
            except Exception as e:
                logger.error(f"RAG model error: {e}")
        
        # Fallback response
        return jsonify({
            "intent": "general_query",
            "entities": {},
            "message": "I can help you find artisans and crafts. Try asking about specific states, crafts, or browse the database. For example: 'Show me pottery artists' or 'Find artists in Kerala'.",
            "artists": [],
            "suggestions": ["Browse by state", "Browse by craft", "Get database statistics"],
            "mode": "fallback"
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            "intent": "error",
            "entities": {},
            "message": "I encountered an error while processing your request. Please try again.",
            "artists": [],
            "suggestions": ["Try a different search", "Check your connection"],
            "mode": "error"
        })

@app.route("/train", methods=["POST"])
def train():
    """
    Endpoint to retrain the RAG model from training data.
    Expects 'multilingual_training_data.json' in current directory.
    """
    if rag_model is None:
        return jsonify({"error": "RAG model not available"}), 503
        
    training_data_file = "multilingual_training_data.json"

    if not os.path.exists(training_data_file):
        return jsonify({"error": f"Training data file {training_data_file} not found."}), 404

    try:
        # Load training data
        with open(training_data_file, "r", encoding="utf-8") as f:
            training_data = json.load(f)

        # Build vector stores for each supported language
        for lang in rag_model.supported_languages:
            docs = [item for item in training_data if item.get("language") == lang]
            if docs:
                rag_model.build_vector_store(docs, lang)

        # Save model
        MODEL_PATH = "trained_rag_model"
        rag_model.save_model(MODEL_PATH)

        return jsonify({"message": "Training completed and model saved successfully."})
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return jsonify({"error": "Training failed"}), 500

# -------------------------
# Error Handlers
# -------------------------

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)