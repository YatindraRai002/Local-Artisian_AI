"""
Chatbot Engine for Kala-Kaart
Handles RAG model initialization, training, and user query processing.
"""

import os
import logging
from typing import Dict, Any, List
from rag_nlp_model import MultilingualRAGModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatbotEngine:
    def __init__(self, model_dir: str = "trained_rag_model", use_gpu: bool = True):
        self.model_dir = model_dir
        self.use_gpu = use_gpu

        # Initialize the RAG NLP model
        self.rag_model = MultilingualRAGModel(use_gpu=self.use_gpu)
        if os.path.exists(self.model_dir):
            logger.info(f"Loading existing model from {self.model_dir}...")
            self.rag_model.load_model(self.model_dir)
        else:
            logger.info("No existing model found. You need to train the model first.")

    # -------------------------
    # Training
    # -------------------------
    def train(self, training_data_path: str):
        """
        Train the RAG model from conversation data and knowledge base.
        :param training_data_path: Path to JSON training data
        """
        if not os.path.exists(training_data_path):
            logger.error(f"Training data file not found: {training_data_path}")
            return

        logger.info(f"Training model with data: {training_data_path}")
        self.rag_model.train_from_conversations(training_data_path)
        # Save the model after training
        self.rag_model.save_model(self.model_dir)
        logger.info("Training completed and model saved.")

    # -------------------------
    # Query Handling
    # -------------------------
    def ask(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user query and return the chatbot response.
        :param user_input: Input text from user
        :param context: Optional user/session context
        :return: Dictionary with response, detected language, and retrieved docs
        """
        if not user_input:
            return {"response": "Please enter a query.", "detected_language": "english", "retrieved_docs": [], "confidence": False}

        result = self.rag_model.query(user_input, context)
        return result

    # -------------------------
    # Utilities
    # -------------------------
    def available_languages(self) -> List[str]:
        """Return list of supported languages"""
        return self.rag_model.supported_languages
