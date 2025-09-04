"""
Hindi NLP Model with Tokenization, Embedding, Encoder-Decoder Architecture
Complete pipeline for Hindi to English translation and query processing
"""

import re
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import pickle
import os

@dataclass
class ProcessedQuery:
    original_hindi: str
    translated_english: str
    tokens: List[str]
    embeddings: np.ndarray
    intent: str
    entities: Dict[str, str]
    confidence: float

class HindiTokenizer:
    """Advanced Hindi tokenizer with preprocessing"""
    
    def __init__(self):
        # Hindi-specific patterns and rules
        self.hindi_stopwords = {
            'का', 'की', 'के', 'में', 'से', 'को', 'और', 'या', 'है', 'हैं', 'था', 'थे', 
            'होगा', 'होंगे', 'यह', 'वह', 'जो', 'कि', 'पर', 'तक', 'लिए', 'साथ',
            'बाद', 'पहले', 'अब', 'फिर', 'यहाँ', 'वहाँ', 'कैसे', 'क्यों', 'कब', 'कहाँ'
        }
        
        # Hindi numerals to English
        self.hindi_numerals = {
            '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
            '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
        }
        
        # Craft types in Hindi
        self.craft_translations = {
            'कुम्हारी': 'pottery', 'मिट्टी के बर्तन': 'pottery',
            'कढ़ाई': 'embroidery', 'चिकनकारी': 'chikankari',
            'कालीन': 'carpet', 'दरी': 'carpet weaving',
            'बुनाई': 'weaving', 'हथकरघा': 'handloom',
            'लकड़ी का काम': 'wood craft', 'नक्काशी': 'carving',
            'आभूषण': 'jewelry', 'गहने': 'jewelry',
            'पेंटिंग': 'painting', 'चित्रकारी': 'painting'
        }
        
        # Location names in Hindi
        self.location_translations = {
            'राजस्थान': 'rajasthan', 'उत्तर प्रदेश': 'uttar pradesh',
            'बिहार': 'bihar', 'गुजरात': 'gujarat', 'महाराष्ट्र': 'maharashtra',
            'तमिलनाडु': 'tamil nadu', 'केरल': 'kerala', 'कर्नाटक': 'karnataka',
            'पंजाब': 'punjab', 'हरियाणा': 'haryana', 'दिल्ली': 'delhi',
            'मुंबई': 'mumbai', 'कोलकाता': 'kolkata', 'चेन्नई': 'chennai',
            'बंगलोर': 'bangalore', 'हैदराबाद': 'hyderabad', 'पुणे': 'pune'
        }
    
    def normalize_hindi_text(self, text: str) -> str:
        """Normalize Hindi text for processing"""
        # Convert Hindi numerals to English
        for hindi_num, eng_num in self.hindi_numerals.items():
            text = text.replace(hindi_num, eng_num)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation but keep Hindi characters
        text = re.sub(r'[^\u0900-\u097F\s\w]', ' ', text)
        
        return text.strip().lower()
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize Hindi text into meaningful units"""
        normalized_text = self.normalize_hindi_text(text)
        
        # Split by whitespace and filter out empty strings
        tokens = [token for token in normalized_text.split() if token]
        
        # Remove stopwords
        tokens = [token for token in tokens if token not in self.hindi_stopwords]
        
        return tokens
    
    def extract_entities(self, tokens: List[str]) -> Dict[str, str]:
        """Extract entities like craft types and locations from Hindi tokens"""
        entities = {}
        
        for token in tokens:
            # Check for craft types
            if token in self.craft_translations:
                entities['craft_type'] = self.craft_translations[token]
            
            # Check for locations
            if token in self.location_translations:
                entities['location'] = self.location_translations[token]
        
        return entities

class HindiEmbedding:
    """Vector embedding system for Hindi words"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.vocab = {}
        self.embeddings = {}
        self.vocab_size = 0
        
        # Pre-trained word vectors for common Hindi words
        self.initialize_base_embeddings()
    
    def initialize_base_embeddings(self):
        """Initialize embeddings for common Hindi words and craft terms"""
        base_vocab = [
            # Question words
            'क्या', 'कौन', 'कब', 'कहाँ', 'कैसे', 'किसको', 'किसने',
            # Action words
            'दिखाओ', 'बताओ', 'खोजो', 'चाहिए', 'मिल', 'देखना', 'जानना',
            # Craft related
            'कारीगर', 'शिल्पकार', 'काम', 'बनाना', 'हस्तशिल्प', 'कला',
            # Common words
            'अच्छा', 'बुरा', 'नया', 'पुराना', 'बड़ा', 'छोटा', 'सुंदर'
        ]
        
        for i, word in enumerate(base_vocab):
            self.vocab[word] = i
            # Initialize with random embeddings (in production, use pre-trained)
            self.embeddings[word] = np.random.randn(self.embedding_dim) * 0.1
        
        self.vocab_size = len(base_vocab)
    
    def get_embedding(self, word: str) -> np.ndarray:
        """Get embedding for a word, create new if not exists"""
        if word in self.embeddings:
            return self.embeddings[word]
        else:
            # Create new embedding for unknown word
            embedding = np.random.randn(self.embedding_dim) * 0.1
            self.embeddings[word] = embedding
            self.vocab[word] = self.vocab_size
            self.vocab_size += 1
            return embedding
    
    def encode_tokens(self, tokens: List[str]) -> np.ndarray:
        """Convert tokens to embeddings matrix"""
        if not tokens:
            return np.zeros((1, self.embedding_dim))
        
        embeddings = []
        for token in tokens:
            embeddings.append(self.get_embedding(token))
        
        return np.array(embeddings)

class HindiToEnglishTranslator:
    """Encoder-Decoder model for Hindi to English translation"""
    
    def __init__(self):
        # Translation dictionary for common phrases and words
        self.translation_dict = {
            # Greetings and basic phrases
            'नमस्ते': 'hello', 'नमस्कार': 'hello',
            'धन्यवाद': 'thank you', 'शुक्रिया': 'thank you',
            'कृपया': 'please', 'माफ करिये': 'excuse me',
            
            # Question words
            'क्या': 'what', 'कौन': 'who', 'कब': 'when', 
            'कहाँ': 'where', 'कैसे': 'how', 'क्यों': 'why',
            'किसको': 'whom', 'किसने': 'who',
            
            # Action verbs
            'दिखाओ': 'show', 'बताओ': 'tell', 'खोजो': 'search',
            'चाहिए': 'want', 'मिल': 'get', 'देखना': 'see',
            'जानना': 'know', 'पूछना': 'ask',
            
            # Craft and artisan related
            'कारीगर': 'artisan', 'शिल्पकार': 'craftsman',
            'हस्तशिल्प': 'handicraft', 'कला': 'art', 'काम': 'work',
            'बनाना': 'make', 'तैयार': 'prepare',
            
            # Adjectives
            'अच्छा': 'good', 'बुरा': 'bad', 'सुंदर': 'beautiful',
            'नया': 'new', 'पुराना': 'old', 'बड़ा': 'big', 'छोटा': 'small',
            
            # Numbers
            'एक': 'one', 'दो': 'two', 'तीन': 'three', 'चार': 'four', 'पांच': 'five'
        }
        
        # Pattern-based translation rules
        self.translation_patterns = [
            # "X कारीगर दिखाओ" -> "show X artisans"
            (r'(.+)\s*कारीगर\s*दिखाओ', r'show \1 artisans'),
            # "X में कारीगर" -> "artisans in X"
            (r'(.+)\s*में\s*कारीगर', r'artisans in \1'),
            # "क्या आपके पास X है" -> "do you have X"
            (r'क्या\s*आपके\s*पास\s*(.+)\s*है', r'do you have \1'),
        ]
    
    def translate_word(self, hindi_word: str) -> str:
        """Translate single Hindi word to English"""
        return self.translation_dict.get(hindi_word, hindi_word)
    
    def translate_sentence(self, hindi_sentence: str) -> str:
        """Translate complete Hindi sentence to English"""
        # First try pattern matching
        for hindi_pattern, english_pattern in self.translation_patterns:
            match = re.search(hindi_pattern, hindi_sentence)
            if match:
                # Apply pattern transformation
                result = re.sub(hindi_pattern, english_pattern, hindi_sentence)
                # Translate individual words in the result
                words = result.split()
                translated_words = [self.translate_word(word) for word in words]
                return ' '.join(translated_words)
        
        # Word-by-word translation as fallback
        words = hindi_sentence.split()
        translated_words = [self.translate_word(word) for word in words]
        return ' '.join(translated_words)

class HindiNLPModel:
    """Complete Hindi NLP processing pipeline"""
    
    def __init__(self):
        self.tokenizer = HindiTokenizer()
        self.embedding = HindiEmbedding()
        self.translator = HindiToEnglishTranslator()
        
        # Intent classification patterns
        self.intent_patterns = {
            'search_artisan': [
                r'कारीगर.*दिखाओ', r'शिल्पकार.*चाहिए', r'.*कारीगर.*खोज',
                r'artisan.*show', r'find.*craftsman'
            ],
            'search_craft': [
                r'.*कुम्हारी.*दिखाओ', r'.*कढ़ाई.*चाहिए', r'.*बुनाई.*खोज',
                r'pottery.*show', r'embroidery.*find'
            ],
            'search_location': [
                r'.*में.*कारीगर', r'.*राज्य.*शिल्पकार', r'.*जिला.*कारीगर',
                r'artisans.*in', r'craftsmen.*from'
            ],
            'get_info': [
                r'क्या.*है', r'बताओ.*के.*बारे.*में', r'जानकारी.*चाहिए',
                r'what.*is', r'tell.*about', r'information.*about'
            ]
        }
    
    def detect_language(self, text: str) -> str:
        """Detect if text is primarily Hindi or English"""
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
        total_chars = len(re.findall(r'[a-zA-Z\u0900-\u097F]', text))
        
        if total_chars == 0:
            return 'unknown'
        
        hindi_ratio = hindi_chars / total_chars
        return 'hindi' if hindi_ratio > 0.3 else 'english'
    
    def classify_intent(self, text: str) -> str:
        """Classify user intent from Hindi or English text"""
        text_lower = text.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent
        
        return 'general_query'
    
    def process_query(self, query: str) -> ProcessedQuery:
        """Complete processing pipeline for Hindi query"""
        # Step 1: Language detection
        language = self.detect_language(query)
        
        if language == 'hindi':
            # Step 2: Tokenization for Hindi
            tokens = self.tokenizer.tokenize(query)
            
            # Step 3: Vector embeddings
            embeddings = self.embedding.encode_tokens(tokens)
            
            # Step 4: Entity extraction
            entities = self.tokenizer.extract_entities(tokens)
            
            # Step 5: Translation (Encoder-Decoder)
            translated_query = self.translator.translate_sentence(query)
        else:
            # Handle English queries directly
            tokens = query.lower().split()
            embeddings = self.embedding.encode_tokens(tokens)
            entities = {}
            translated_query = query
        
        # Step 6: Intent classification
        intent = self.classify_intent(translated_query)
        
        return ProcessedQuery(
            original_hindi=query,
            translated_english=translated_query,
            tokens=tokens,
            embeddings=embeddings,
            intent=intent,
            entities=entities,
            confidence=0.85  # Placeholder confidence score
        )
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        model_data = {
            'vocab': self.embedding.vocab,
            'embeddings': self.embedding.embeddings,
            'vocab_size': self.embedding.vocab_size
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """Load a pre-trained model"""
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
                self.embedding.vocab = model_data['vocab']
                self.embedding.embeddings = model_data['embeddings']
                self.embedding.vocab_size = model_data['vocab_size']

# Test the model
if __name__ == "__main__":
    model = HindiNLPModel()
    
    # Test queries
    test_queries = [
        "कुम्हारी कारीगर दिखाओ",
        "राजस्थान में शिल्पकार चाहिए",
        "कढ़ाई का काम कौन करता है",
        "show me pottery artists",
        "मुझे चिकनकारी के बारे में बताओ"
    ]
    
    print("Hindi NLP Model Test Results:")
    print("=" * 50)
    
    for query in test_queries:
        result = model.process_query(query)
        print(f"\nOriginal: {result.original_hindi}")
        print(f"Translated: {result.translated_english}")
        print(f"Intent: {result.intent}")
        print(f"Entities: {result.entities}")
        print(f"Tokens: {result.tokens}")
        print(f"Confidence: {result.confidence}")
        print("-" * 30)