"""
Kala-Kaart AI Chatbot API
Flask backend for querying the Multilingual RAG model.
"""

from flask import Flask, request, jsonify
import logging
from backend.rag_nlp_model import MultilingualRAGModel  # Your model file
import json
import os



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
MODEL_PATH = "trained_rag_model"  # Folder where your model vector stores will be saved
USE_GPU = False  # Set to True if you have a GPU

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
            "retrieved_docs": docs
        })
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({"error": "Failed to process query"}), 500


@app.route("/train", methods=["POST"])
def train():
    """
    Endpoint to retrain the RAG model from training data.
    Expects 'multilingual_training_data.json' in backend folder.
    """
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
