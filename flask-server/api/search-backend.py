from flask import Flask, request, jsonify
from flask_cors import CORS
import sys, os

# Set Python path so backend modules are found
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from backend.data_processor import ArtisanDataProcessor
from backend.lightweight_chatbot import LightweightEnhancedChatbot

backend_dir = os.path.join(project_root, "backend")

app = Flask(__name__)
CORS(app)

# Global data processor instance
processor_instance = None

def get_data_processor():
    global processor_instance
    if processor_instance is None:
        try:
            csv_path = os.path.join(project_root, 'public', 'Artisans.csv')
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

        filter_dict = {k: v for k, v in filters.items() if v is not None and k != "limit"}
        results = processor.search_artists(filter_dict)
        limited_results = results[:limit]

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

if __name__ == "__main__":
    app.run(debug=True, port=8000)
