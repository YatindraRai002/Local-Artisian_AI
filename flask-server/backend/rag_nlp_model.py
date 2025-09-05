"""
Multilingual RAG Model for Kala-Kaart Chatbot
Supports Hindi, English, Tamil, and Telugu.
"""
from typing import List, Dict, Any
import os
import json
import logging
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any
from transformers import (
    AutoTokenizer, AutoModel, pipeline,
    MarianMTModel, MarianTokenizer
)
import torch
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from backend.training.vector_store_utils import load_vector_store


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultilingualRAGModel:
    def __init__(self, model_path: str = "models/", use_gpu: bool = True):
        self.model_path = model_path
        self.device = 'cuda' if use_gpu and torch.cuda.is_available() else 'cpu'
        self.supported_languages = ['english', 'hindi', 'tamil', 'telugu']
        self.lang_codes = {'english': 'en', 'hindi': 'hi', 'tamil': 'ta', 'telugu': 'te'}

        self.translation_models = {}
        self.vector_stores = {}
        self.chroma_client = None

        self._initialize_models()
        self._initialize_chroma()
        self._load_vectorstores()

    # -------------------------
    # Training from conversations
    # -------------------------
    def train_from_conversations(self, training_data_file: str):
        """Build vector stores from training data JSON"""
        if not os.path.exists(training_data_file):
            logger.error(f"Training data file not found: {training_data_file}")
            return

        with open(training_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'conversations' not in data:
            logger.error("Training data does not contain 'conversations' key")
            return

        for lang in self.supported_languages:
            lang_docs = [item for item in data['conversations'] if item.get('language') == lang]
            if lang_docs:
                logger.info(f"Building vector store for {lang} with {len(lang_docs)} documents")
                self.build_vector_store(lang_docs, lang)
            else:
                logger.warning(f"No documents found for language {lang}")

    # -------------------------
    # Model Initialization
    # -------------------------
    def _initialize_models(self):
        """Initialize embeddings, translation, intent, and context models"""
        logger.info("Initializing multilingual models...")
        self.multilingual_encoder = SentenceTransformer(
            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        )

        self.language_detector = pipeline(
            "text-classification",
            model="papluca/xlm-roberta-base-language-detection",
            device=0 if self.device == 'cuda' else -1
        )

        self._load_available_translation_models()

        self.intent_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=0 if self.device == 'cuda' else -1
        )

        self.context_model_name = "bert-base-multilingual-cased"
        self.context_tokenizer = AutoTokenizer.from_pretrained(self.context_model_name)
        self.context_model = AutoModel.from_pretrained(self.context_model_name).to(self.device)
        logger.info("Models initialized successfully")

    def _load_available_translation_models(self):
        """Load only translation models that are actually available"""
        available_pairs = ['hi-en', 'en-hi']  # Only supported models
        for pair in available_pairs:
            try:
                src, tgt = pair.split('-')
                model_name = f'Helsinki-NLP/opus-mt-{src}-{tgt}'
                tokenizer = MarianTokenizer.from_pretrained(model_name)
                model = MarianMTModel.from_pretrained(model_name).to(self.device)
                self.translation_models[pair] = {'tokenizer': tokenizer, 'model': model}
                logger.info(f"Loaded translation model {pair}")
            except Exception as e:
                logger.warning(f"Could not load translation model {pair}: {e}")

    def _initialize_chroma(self):
        """Initialize ChromaDB safely"""
        try:
            self.chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="backend/chroma_db/multilingual_chroma"
            ))
            logger.info("✅ ChromaDB initialized successfully")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}")
            self.chroma_client = None

    def _load_vectorstores(self):
        """Try to load existing vector stores (Chroma → FAISS)"""
        # Chroma
        if self.chroma_client:
            try:
                for lang in self.supported_languages:
                    collection_name = f"kala_kaart_{lang}"
                    try:
                        self.chroma_client.get_or_create_collection(name=collection_name)
                        logger.info(f"✅ Using Chroma collection for {lang}")
                    except Exception as e:
                        logger.warning(f"Chroma collection for {lang} unavailable: {e}")
            except Exception as e:
                logger.warning(f"Chroma loading failed: {e}")

        # FAISS pickle fallback
        for lang in self.supported_languages:
            file = os.path.join("backend/vector_stores", f"{lang}_vector_store.pkl")
            if os.path.exists(file):
                try:
                    with open(file, 'rb') as f:
                        self.vector_stores[lang] = pickle.load(f)
                    logger.info(f"✅ Loaded FAISS backup for {lang}")
                except Exception as e:
                    logger.warning(f"Failed to load FAISS backup for {lang}: {e}")

        if not self.chroma_client and not self.vector_stores:
            logger.error("❌ No vector stores found! Please run build_vector_store.py")

       
        vectorstore = load_vector_store()
        if vectorstore:
            self.vector_stores["default"] = vectorstore
            logger.info("✅ Vector store loaded successfully.")
        else:
            logger.error("❌ No usable vector store found. Please run build_vector_store.py first.")

    # -------------------------
    # Language Detection & Translation
    # -------------------------
    def detect_language(self, text: str) -> str:
        try:
            result = self.language_detector(text)
            detected_lang = result[0]['label'].lower()
            mapping = {'en': 'english', 'hi': 'hindi', 'ta': 'tamil', 'te': 'telugu'}
            return mapping.get(detected_lang[:2], 'english')
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return 'english'

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        if source_lang == target_lang:
            return text

        src_code = self.lang_codes.get(source_lang, source_lang)
        tgt_code = self.lang_codes.get(target_lang, target_lang)
        model_key = f"{src_code}-{tgt_code}"

        if model_key in self.translation_models:
            try:
                model_info = self.translation_models[model_key]
                tokenizer = model_info['tokenizer']
                model = model_info['model']

                inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self.device)
                with torch.no_grad():
                    outputs = model.generate(**inputs, max_length=512, num_beams=4)
                return tokenizer.decode(outputs[0], skip_special_tokens=True)
            except Exception as e:
                logger.error(f"Translation failed for {model_key}: {e}")
                return text
        else:
            logger.warning(f"Translation model {model_key} not available")
            return text

    # -------------------------
    # Embeddings & Vector Store
    # -------------------------
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        try:
            return self.multilingual_encoder.encode(
                texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True
            )
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            return np.array([])

    def build_vector_store(self, documents: List[Dict[str, Any]], language: str):
        logger.info(f"Building vector store for {language}")
        texts = [doc.get('text', str(doc)) for doc in documents]
        metadatas = [{k: v for k, v in doc.items() if k != 'text'} for doc in documents]

        embeddings = self.create_embeddings(texts)
        if len(embeddings) == 0:
            return

        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings.astype('float32'))
        self.vector_stores[language] = {'index': index, 'texts': texts, 'metadatas': metadatas, 'embeddings': embeddings}

        # Add to ChromaDB if available
        if self.chroma_client:
            try:
                collection = self.chroma_client.get_or_create_collection(name=f"kala_kaart_{language}")
                collection.add(
                    embeddings=embeddings.tolist(),
                    documents=texts,
                    metadatas=metadatas,
                    ids=[f"{language}_{i}" for i in range(len(texts))]
                )
                logger.info(f"Added {len(texts)} documents to ChromaDB for {language}")
            except Exception as e:
                logger.warning(f"ChromaDB addition failed for {language}: {e}")

    # -------------------------
    # Semantic Search
    # -------------------------
    def semantic_search(self, query: str, language: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search using Chroma DB (preferred) or FAISS (fallback).
        """
        results = []
        query_emb = self.create_embeddings([query])

        if len(query_emb) == 0:
            logger.warning("⚠️ No embedding created for query")
            return results

        # --- Try Chroma ---
        try:
            vectorstore = load_vector_store()
            if vectorstore:
                res = vectorstore.similarity_search_with_score(query, k=top_k)
                for doc, score in res:
                    results.append({
                        'text': doc.page_content,
                        'metadata': doc.metadata,
                        'score': float(score),
                        'distance': float(1 / (1 + score))  # normalized
                    })
                return results
        except Exception as e:
            logger.warning(f"⚠️ Chroma search failed: {e}")

        # --- Fallback: FAISS pickle ---
        if language in self.vector_stores:
            vs = self.vector_stores[language]
            distances, indices = vs['index'].search(query_emb.astype('float32'), top_k)
            for i, idx in enumerate(indices[0]):
                if idx != -1:
                    results.append({
                        'text': vs['texts'][idx],
                        'metadata': vs['metadatas'][idx],
                        'score': float(distances[0][i]),
                        'distance': float(1 / (1 + distances[0][i]))
                    })

        return results

    # -------------------------
    # Response Generation
    # -------------------------
    def generate_response(self, query: str, retrieved_docs: List[Dict[str, Any]], language: str) -> str:
        context = " ".join([doc['text'] for doc in retrieved_docs[:3]]) if retrieved_docs else ""
        return f"Response in {language}: {context[:500] if context else 'No info found.'}"

    # -------------------------
    # Save / Load Model
    # -------------------------
    def save_model(self, path: str):
        os.makedirs(path, exist_ok=True)
        for lang, store in self.vector_stores.items():
            with open(os.path.join(path, f"{lang}_vector_store.pkl"), 'wb') as f:
                pickle.dump(store, f)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        for lang in self.supported_languages:
            file = os.path.join(path, f"{lang}_vector_store.pkl")
            if os.path.exists(file):
                with open(file, 'rb') as f:
                    self.vector_stores[lang] = pickle.load(f)
                logger.info(f"Loaded vector store for {lang}")
