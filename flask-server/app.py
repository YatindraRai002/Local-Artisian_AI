from flask import Flask, request, jsonify
import logging
from backend.rag_nlp_model import MultilingualRAGModel  # make sure this file is in backend/
import os

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

if __name__ == "__main__":
    # Start Flask app
    app.run(host="0.0.0.0", port=8000, debug=True)
