"""
RAG-Based Multilingual NLP Model for Kala-Kaart Chatbot
Implements Retrieval-Augmented Generation with multilingual support
"""

import os
import json
import numpy as np
import pickle
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import faiss
from transformers import (
    AutoTokenizer, AutoModel, pipeline,
    MarianMTModel, MarianTokenizer,
    AutoModelForSequenceClassification
)
import torch
import torch.nn.functional as F
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultilingualRAGModel:
    """
    Advanced RAG model supporting Hindi, English, Tamil, and Telugu
    """
    
    def __init__(self, model_path: str = "models/", use_gpu: bool = True):
        self.model_path = model_path
        self.device = 'cuda' if use_gpu and torch.cuda.is_available() else 'cpu'
        self.supported_languages = ['english', 'hindi', 'tamil', 'telugu']
        
        # Language code mapping
        self.lang_codes = {
            'english': 'en',
            'hindi': 'hi', 
            'tamil': 'ta',
            'telugu': 'te'
        }
        
        # Initialize models
        self._initialize_models()
        
        # Vector stores for different languages
        self.vector_stores = {}
        self.knowledge_base = {}
        
        # ChromaDB client for advanced vector operations
        self.chroma_client = None
        self._initialize_chroma()

    def _initialize_models(self):
        """Initialize all required models"""
        logger.info("Initializing multilingual models...")
        
        # Multilingual sentence transformer for embeddings
        self.multilingual_encoder = SentenceTransformer(
            'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        )
        
        # Language detection model
        self.language_detector = pipeline(
            "text-classification",
            model="papluca/xlm-roberta-base-language-detection",
            device=0 if self.device == 'cuda' else -1
        )
        
        # Translation models for different language pairs
        self._initialize_translation_models()
        
        # Text classification for intent recognition
        self.intent_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=0 if self.device == 'cuda' else -1
        )
        
        # Initialize multilingual BERT for contextual understanding
        self.context_model_name = "bert-base-multilingual-cased"
        self.context_tokenizer = AutoTokenizer.from_pretrained(self.context_model_name)
        self.context_model = AutoModel.from_pretrained(self.context_model_name).to(self.device)
        
        logger.info("Models initialized successfully")

    def _initialize_translation_models(self):
        """Initialize translation models for multilingual support"""
        self.translation_models = {}
        
        # Translation model mappings
        translation_pairs = [
            ('hi', 'en'),  # Hindi to English
            ('en', 'hi'),  # English to Hindi
            ('ta', 'en'),  # Tamil to English
            ('en', 'ta'),  # English to Tamil
            ('te', 'en'),  # Telugu to English
            ('en', 'te'),  # English to Telugu
        ]
        
        for src, tgt in translation_pairs:
            model_name = f'Helsinki-NLP/opus-mt-{src}-{tgt}'
            try:
                tokenizer = MarianTokenizer.from_pretrained(model_name)
                model = MarianMTModel.from_pretrained(model_name).to(self.device)
                self.translation_models[f'{src}-{tgt}'] = {
                    'tokenizer': tokenizer,
                    'model': model
                }
                logger.info(f"Loaded translation model: {src}-{tgt}")
            except Exception as e:
                logger.warning(f"Could not load translation model {src}-{tgt}: {e}")

    def _initialize_chroma(self):
        """Initialize ChromaDB for advanced vector operations"""
        try:
            self.chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="./chroma_db"
            ))
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}")

    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        try:
            result = self.language_detector(text)
            detected_lang = result[0]['label'].lower()
            
            # Map detected language to supported languages
            lang_mapping = {
                'en': 'english',
                'hi': 'hindi', 
                'ta': 'tamil',
                'te': 'telugu'
            }
            
            return lang_mapping.get(detected_lang[:2], 'english')
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return 'english'

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text between supported languages"""
        if source_lang == target_lang:
            return text
            
        src_code = self.lang_codes.get(source_lang, source_lang)
        tgt_code = self.lang_codes.get(target_lang, target_lang)
        
        model_key = f'{src_code}-{tgt_code}'
        
        if model_key in self.translation_models:
            try:
                model_info = self.translation_models[model_key]
                tokenizer = model_info['tokenizer']
                model = model_info['model']
                
                # Tokenize and translate
                inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self.device)
                with torch.no_grad():
                    outputs = model.generate(**inputs, max_length=512, num_beams=4)
                
                translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
                return translated
            except Exception as e:
                logger.error(f"Translation failed for {model_key}: {e}")
                return text
        else:
            logger.warning(f"Translation model {model_key} not available")
            return text

    def create_embeddings(self, texts: List[str], language: str = None) -> np.ndarray:
        """Create multilingual embeddings for texts"""
        try:
            # Use multilingual sentence transformer
            embeddings = self.multilingual_encoder.encode(
                texts, 
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            return np.array([])

    def get_contextual_embeddings(self, text: str, language: str) -> np.ndarray:
        """Get contextual embeddings using multilingual BERT"""
        try:
            inputs = self.context_tokenizer(
                text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.context_model(**inputs)
                # Use CLS token embedding
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            return embeddings.flatten()
        except Exception as e:
            logger.error(f"Contextual embedding failed: {e}")
            return np.array([])

    def build_vector_store(self, documents: List[Dict[str, Any]], language: str):
        """Build vector store for specific language"""
        logger.info(f"Building vector store for {language}")
        
        # Prepare documents
        texts = []
        metadatas = []
        
        for doc in documents:
            if isinstance(doc, dict):
                text = doc.get('text', '') or doc.get('content', '') or str(doc)
                metadata = {k: v for k, v in doc.items() if k != 'text' and k != 'content'}
                metadata['language'] = language
            else:
                text = str(doc)
                metadata = {'language': language}
            
            texts.append(text)
            metadatas.append(metadata)
        
        # Create embeddings
        embeddings = self.create_embeddings(texts, language)
        
        # Build FAISS vector store
        if len(embeddings) > 0:
            # Create FAISS index
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings.astype('float32'))
            
            # Store vector store data
            self.vector_stores[language] = {
                'index': index,
                'texts': texts,
                'metadatas': metadatas,
                'embeddings': embeddings
            }
            
            # Also add to ChromaDB if available
            if self.chroma_client:
                try:
                    collection = self.chroma_client.create_collection(
                        name=f"kala_kaart_{language}",
                        get_or_create=True
                    )
                    
                    collection.add(
                        embeddings=embeddings.tolist(),
                        documents=texts,
                        metadatas=metadatas,
                        ids=[f"{language}_{i}" for i in range(len(texts))]
                    )
                    logger.info(f"Added {len(texts)} documents to ChromaDB for {language}")
                except Exception as e:
                    logger.warning(f"ChromaDB addition failed for {language}: {e}")
        
        logger.info(f"Vector store built for {language} with {len(texts)} documents")

    def semantic_search(self, query: str, language: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search in vector store"""
        if language not in self.vector_stores:
            logger.warning(f"Vector store not found for {language}")
            return []
        
        # Create query embedding
        query_embedding = self.create_embeddings([query], language)
        if len(query_embedding) == 0:
            return []
        
        vector_store = self.vector_stores[language]
        index = vector_store['index']
        texts = vector_store['texts']
        metadatas = vector_store['metadatas']
        
        # Search in FAISS index
        distances, indices = index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # Valid result
                result = {
                    'text': texts[idx],
                    'metadata': metadatas[idx],
                    'score': float(1 / (1 + distances[0][i])),  # Convert distance to similarity score
                    'distance': float(distances[0][i])
                }
                results.append(result)
        
        return results

    def generate_response(self, query: str, retrieved_docs: List[Dict[str, Any]], 
                         language: str, context: Dict[str, Any] = None) -> str:
        """Generate response using retrieved documents"""
        
        # Classify intent
        intent_labels = [
            "find_artist", "craft_search", "location_search", 
            "contact_info", "greeting", "help_request", "general_query"
        ]
        
        try:
            intent_result = self.intent_classifier(query, intent_labels)
            intent = intent_result['labels'][0]
            confidence = intent_result['scores'][0]
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            intent = "general_query"
            confidence = 0.5
        
        # Extract relevant information from retrieved documents
        relevant_info = []
        for doc in retrieved_docs[:3]:  # Use top 3 documents
            relevant_info.append(doc['text'])
        
        context_text = " ".join(relevant_info) if relevant_info else ""
        
        # Generate response based on intent and language
        response = self._generate_language_specific_response(
            query, intent, context_text, language, context
        )
        
        return response

    def _generate_language_specific_response(self, query: str, intent: str, 
                                           context: str, language: str, 
                                           user_context: Dict[str, Any] = None) -> str:
        """Generate language-specific response"""
        
        # Response templates for different intents and languages
        templates = {
            'english': {
                'greeting': "Hello! I'm Kala-Kaart AI assistant. I can help you find traditional Indian artisans in multiple languages. How can I assist you today?",
                'find_artist': "Based on your query, here are some relevant artisans: {context}",
                'craft_search': "I found information about {craft} artisans: {context}",
                'location_search': "Here are artisans from {location}: {context}",
                'help_request': "I can help you find traditional Indian artisans by craft, location, or name. I support Hindi, English, Tamil, and Telugu languages.",
                'general_query': "Here's what I found: {context}"
            },
            'hindi': {
                'greeting': "नमस्ते! मैं कला-कार्त AI सहायक हूं। मैं आपको कई भाषाओं में पारंपरिक भारतीय कारीगर खोजने में मदद कर सकता हूं। आज मैं आपकी कैसे सहायता कर सकता हूं?",
                'find_artist': "आपकी खोज के आधार पर, यहां कुछ संबंधित कारीगर हैं: {context}",
                'craft_search': "मुझे {craft} कारीगरों के बारे में जानकारी मिली: {context}",
                'location_search': "यहां {location} के कारीगर हैं: {context}",
                'help_request': "मैं आपको शिल्प, स्थान या नाम के आधार पर पारंपरिक भारतीय कारीगर खोजने में मदद कर सकता हूं। मैं हिंदी, अंग्रेजी, तमिल और तेलुगु भाषाओं का समर्थन करता हूं।",
                'general_query': "यहां वह है जो मुझे मिला: {context}"
            },
            'tamil': {
                'greeting': "வணக்கம்! நான் கலா-கார்ட் AI உதவியாளர். பல மொழிகளில் பாரம்பரிய இந்திய கைவினைஞர்களைக் கண்டறிய உதவ முடியும். இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?",
                'find_artist': "உங்கள் தேடலின் அடிப்படையில், இங்கே சில தொடர்புடைய கைவினைஞர்கள்: {context}",
                'craft_search': "{craft} கைவினைஞர்களைப் பற்றிய தகவல் கிடைத்தது: {context}",
                'location_search': "இங்கே {location} இலிருந்து கைவினைஞர்கள்: {context}",
                'help_request': "கைவினை, இடம் அல்லது பெயரின் அடிப்படையில் பாரம்பரிய இந்திய கைவினைஞர்களைக் கண்டறிய உதவ முடியும். நான் இந்தி, ஆங்கிலம், தமிழ் மற்றும் தெலுங்கு மொழிகளை ஆதரிக்கிறேன்.",
                'general_query': "நான் கண்டுபிடித்தது இதுதான்: {context}"
            },
            'telugu': {
                'greeting': "నమస్కారం! నేను కలా-కార్ట్ AI సహాయకుడను. అనేక భాషలలో సాంప్రదాయ భారతీయ కళాకారులను కనుగొనడంలో సహాయపడగలను. ఈ రోజు నేను మీకు ఎలా సహాయపడగలను?",
                'find_artist': "మీ శోధన ఆధారంగా, ఇక్కడ కొంత సంబంధిత కళాకారులు ఉన్నారు: {context}",
                'craft_search': "{craft} కళాకారుల గురించి సమాచారం దొరికింది: {context}",
                'location_search': "ఇక్కడ {location} నుండి కళాకారులు ఉన్నారు: {context}",
                'help_request': "చేతిపని, ప్రాంతం లేదా పేరు ఆధారంగా సాంప్రదాయ భారతీయ కళాకారులను కనుగొనడంలో సహాయపడగలను. నేను హిందీ, ఇంగ్లీష్, తమిళం మరియు తెలుగు భాషలకు మద్దతు ఇస్తాను.",
                'general_query': "నేను కనుగొన్నది ఇదే: {context}"
            }
        }
        
        # Get template for language and intent
        lang_templates = templates.get(language, templates['english'])
        template = lang_templates.get(intent, lang_templates['general_query'])
        
        # Format response with context
        try:
            # Extract entities from query for better formatting
            entities = self._extract_entities(query, language)
            
            response = template.format(
                context=context[:500] if context else "No specific information found",
                craft=entities.get('craft', 'requested craft'),
                location=entities.get('location', 'specified location')
            )
        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            response = template.replace('{context}', context[:500] if context else "")
        
        return response

    def _extract_entities(self, text: str, language: str) -> Dict[str, str]:
        """Extract entities from text"""
        entities = {}
        
        # Simple pattern-based entity extraction
        # This can be enhanced with NER models
        
        # Common craft terms in different languages
        craft_patterns = {
            'english': ['pottery', 'weaving', 'painting', 'carving', 'embroidery', 'metalwork'],
            'hindi': ['मिट्टी के बर्तन', 'बुनाई', 'चित्रकारी', 'नक्काशी', 'कढ़ाई', 'धातु कार्य'],
            'tamil': ['களிமண் பாத்திரங்கள்', 'நெசவு', 'ஓவியம்', 'செதுக்குதல்', 'எம்பிராய்டரி', 'உலோக வேலை'],
            'telugu': ['మట్టి పాత్రలు', 'నేత', 'చిత్రకళ', 'చెక్కడం', 'ఎంబ్రాయిడరీ', 'లోహ పని']
        }
        
        # Location patterns (Indian states)
        location_patterns = {
            'english': ['maharashtra', 'karnataka', 'tamil nadu', 'kerala', 'rajasthan', 'gujarat'],
            'hindi': ['महाराष्ट्र', 'कर्नाटक', 'तमिल नाडु', 'केरल', 'राजस्थान', 'गुजरात'],
            'tamil': ['மகாராஷ்ட்டிரா', 'கர்நாடகா', 'தமிழ்நாடு', 'கேரளா', 'ராஜஸ்தான்', 'குஜராத்'],
            'telugu': ['మహారాష్ట్ర', 'కర్ణాటక', 'తమిళనాడు', 'కేరళ', 'రాజస్థాన్', 'గుజరాత్']
        }
        
        text_lower = text.lower()
        
        # Find crafts
        for craft in craft_patterns.get(language, []):
            if craft.lower() in text_lower:
                entities['craft'] = craft
                break
        
        # Find locations
        for location in location_patterns.get(language, []):
            if location.lower() in text_lower:
                entities['location'] = location
                break
        
        return entities

    def train_from_conversations(self, training_data_path: str):
        """Train the model using conversation data"""
        logger.info(f"Training from conversations: {training_data_path}")
        
        with open(training_data_path, 'r', encoding='utf-8') as f:
            training_data = json.load(f)
        
        conversations = training_data.get('conversations', [])
        knowledge_base = training_data.get('knowledge_base', {})
        
        # Build vector stores for each language
        for language in self.supported_languages:
            # Prepare documents for this language
            lang_documents = []
            
            # Add conversations
            lang_conversations = [conv for conv in conversations if conv['language'] == language]
            for conv in lang_conversations:
                doc = {
                    'text': f"User: {conv['user_message']}\nBot: {conv['bot_response']}",
                    'intent': conv['intent'],
                    'entities': conv['entities'],
                    'language': language,
                    'type': 'conversation'
                }
                lang_documents.append(doc)
            
            # Add knowledge base
            if language in knowledge_base:
                for knowledge in knowledge_base[language]:
                    doc = {
                        'text': f"Craft: {knowledge['craft_local']}\nDescription: {knowledge['description']}\nRegions: {', '.join(knowledge['regions'])}\nMaterials: {', '.join(knowledge['materials'])}",
                        'craft': knowledge['craft_english'],
                        'language': language,
                        'type': 'knowledge'
                    }
                    lang_documents.append(doc)
            
            # Build vector store
            if lang_documents:
                self.build_vector_store(lang_documents, language)
        
        logger.info("Training completed successfully")

    def query(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main query processing function"""
        
        # Detect language
        detected_language = self.detect_language(user_input)
        
        # Translate to English if needed for processing
        english_query = user_input
        if detected_language != 'english':
            english_query = self.translate_text(user_input, detected_language, 'english')
        
        # Perform semantic search
        retrieved_docs = []
        
        # Search in detected language first
        if detected_language in self.vector_stores:
            retrieved_docs.extend(
                self.semantic_search(user_input, detected_language, top_k=3)
            )
        
        # Also search in English for broader coverage
        if detected_language != 'english' and 'english' in self.vector_stores:
            english_docs = self.semantic_search(english_query, 'english', top_k=2)
            retrieved_docs.extend(english_docs)
        
        # Generate response
        response = self.generate_response(
            user_input, retrieved_docs, detected_language, context
        )
        
        return {
            'response': response,
            'detected_language': detected_language,
            'retrieved_docs': retrieved_docs,
            'confidence': len(retrieved_docs) > 0
        }

    def save_model(self, path: str):
        """Save the trained model"""
        os.makedirs(path, exist_ok=True)
        
        # Save vector stores
        for language, store in self.vector_stores.items():
            lang_path = os.path.join(path, f"{language}_vector_store.pkl")
            with open(lang_path, 'wb') as f:
                pickle.dump(store, f)
        
        # Save model configuration
        config = {
            'supported_languages': self.supported_languages,
            'model_path': self.model_path,
            'device': self.device
        }
        
        config_path = os.path.join(path, "model_config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load a trained model"""
        
        # Load vector stores
        for language in self.supported_languages:
            lang_path = os.path.join(path, f"{language}_vector_store.pkl")
            if os.path.exists(lang_path):
                with open(lang_path, 'rb') as f:
                    self.vector_stores[language] = pickle.load(f)
                logger.info(f"Loaded vector store for {language}")
        
        logger.info(f"Model loaded from {path}")

# Example usage and training
if __name__ == "__main__":
    # Initialize RAG model
    rag_model = MultilingualRAGModel()
    
    # Generate training data first
    from multilingual_training_data import MultilingualTrainingDataGenerator
    
    generator = MultilingualTrainingDataGenerator()
    conversations = generator.generate_training_conversations(1000)
    knowledge_base = generator.generate_craft_knowledge_base()
    generator.save_training_data(conversations, knowledge_base, 'multilingual_training_data.json')
    
    # Train the model
    rag_model.train_from_conversations('multilingual_training_data.json')
    
    # Save trained model
    rag_model.save_model("trained_rag_model")
    
    # Test queries in different languages
    test_queries = [
        "Hello, find me pottery artists",
        "नमस्ते, मुझे मिट्टी के बर्तन बनाने वाले कारीगर चाहिए",
        "வணக்கம், மட்பாண்ட கலைஞர்களை காட்டுங்கள்",
        "నమస్కారం, కుండల తయారీదారులను చూపించండి"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = rag_model.query(query)
        print(f"Language: {result['detected_language']}")
        print(f"Response: {result['response']}")
        print("-" * 50)