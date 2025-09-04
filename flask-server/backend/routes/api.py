"""
Kala-Kaart AI Chatbot API
Flask backend for querying the Multilingual RAG model.
"""

from flask import Flask, request, jsonify
import logging
import os
from backend.rag_nlp_model import MultilingualRAGModel  # Adjust path as needed

# -------------------------
# Logging Configuration
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# Flask App Initialization
# -------------------------
app = Flask(__name__)

# -------------------------
# Initialize RAG Model
# -------------------------
MODEL_PATH = "trained_rag_model"
USE_GPU = False  # Set to True if a GPU is available

rag_model = MultilingualRAGModel(use_gpu=USE_GPU)

# Load existing trained model if available
if os.path.exists(MODEL_PATH):
    rag_model.load_model(MODEL_PATH)
    logger.info("Loaded trained RAG model.")
else:
    logger.warning("Trained RAG model not found. Please train the model first.")

# -------------------------
# API Endpoints
# -------------------------

@app.route("/", methods=["GET"])
def home():
    """Test endpoint to check if API is running."""
    return jsonify({"message": "Kala-Kaart AI Chatbot API is running."})


@app.route("/query", methods=["POST"])
def query():
    """
    Endpoint to process a user query.
    JSON body: {"query": "Your question here"}
    """
    data = request.json
    user_input = data.get("query", "").strip()

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
    Endpoint to retrain the RAG model from training data.
    Expects 'multilingual_training_data.json' in project root.
    """
    training_data_file = "multilingual_training_data.json"

    if not os.path.exists(training_data_file):
        return jsonify({"error": f"Training data file {training_data_file} not found."}), 404

    try:
        rag_model.train_from_conversations(training_data_file)
        rag_model.save_model(MODEL_PATH)
        return jsonify({"message": "Training completed and model saved successfully."})
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return jsonify({"error": "Training failed"}), 500


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
