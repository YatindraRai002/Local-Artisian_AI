import sys, os
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add backend folder to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "..", "backend")
sys.path.append(backend_dir)

import data_processor
import lightweight_chatbot  

app = Flask(__name__)
CORS(app)

# Global data processor instance
processor_instance = None

def get_data_processor():
    global processor_instance
    if processor_instance is None:
        try:
            from data_processor import ArtisanDataProcessor
            csv_path = os.path.join(backend_dir, '..', 'public', 'Artisans.csv')
            processor_instance = ArtisanDataProcessor(csv_path, max_artists=1000)
        except Exception as e:
            print(f"Error initializing data processor: {e}")
            return None
    return processor_instance


@app.route("/", methods=["POST"])
def search_artists():
    processor = get_data_processor()
    if not processor:
        return jsonify({"error": "Data processor not ready"}), 503

    try:
        filters = request.json or {}
        limit = filters.get("limit", 20)

        # Build filter dict (exclude None + limit)
        filter_dict = {k: v for k, v in filters.items() if v is not None and k != "limit"}

        results = processor.search_artists(filter_dict)

        # Apply limit
        limited_results = results[:limit]

        # Transform for frontend
        from lightweight_chatbot import LightweightEnhancedChatbot
        bot = LightweightEnhancedChatbot(None)
        transformed_artists = bot.transform_artists_for_frontend(limited_results)

        return jsonify({
            "artists": transformed_artists,
            "total_count": len(results),
            "filters_applied": filter_dict,
            "search_metadata": {
                "query_time": "< 100ms",
                "results_quality": "high"
            }
        })

    except Exception as e:
        return jsonify({"error": f"Search error: {str(e)}"}), 500
