from flask import Flask, request, jsonify
import logging
import os

# Import helpers
from helpers.chat_utils import handle_chat
from helpers.search_utils import apply_filters
from helpers.stats_utils import get_stats
from helpers.similar_utils import find_similar

# Import RAG model
from backend.rag_nlp_model import MultilingualRAGModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize RAG model
model_path = "trained_rag_model"
use_gpu = False  # Change to True if GPU is available
rag_model = MultilingualRAGModel(use_gpu=use_gpu)

# Load trained model if exists
if os.path.exists(model_path):
    rag_model.load_model(model_path)
    logger.info("Loaded trained RAG model")
else:
    logger.warning("Trained RAG model not found. Please train first.")

# -----------------------
# RAG model routes
# -----------------------
@app.route("/")
def home():
    return jsonify({"message": "Kala-Kaart AI Chatbot API is running."})

@app.route("/query", methods=["POST"])
def query():
    data = request.json
    user_input = data.get("query", "")

    if not user_input:
        return jsonify({"error": "Query not provided"}), 400

    try:
        result = rag_model.query(user_input)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({"error": "Failed to process query"}), 500

@app.route("/train", methods=["POST"])
def train():
    """
    Endpoint to retrain the model from multilingual_training_data.json
    """
    data_file = "multilingual_training_data.json"
    if not os.path.exists(data_file):
        return jsonify({"error": f"Training data file {data_file} not found"}), 404

    try:
        rag_model.train_from_conversations(data_file)
        rag_model.save_model(model_path)
        return jsonify({"message": "Training completed and model saved successfully."})
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return jsonify({"error": "Training failed"}), 500

# -----------------------
# Helper routes
# -----------------------
@app.route("/chat", methods=["POST"])
def chat_route():
    body = request.json or {}
    return handle_chat(body)

@app.route("/search", methods=["POST"])
def search_route():
    filters = request.json or {}
    return apply_filters(filters)

@app.route("/stats", methods=["GET"])
def stats_route():
    return get_stats()

@app.route("/similar", methods=["GET"])
def similar_route():
    args = request.args
    return find_similar(args)

# -----------------------
# Run app
# -----------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
