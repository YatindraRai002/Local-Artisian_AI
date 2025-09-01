import os
import re
from typing import List, Dict, Any, Optional
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from sentence_transformers import SentenceTransformer
import openai
from data_processor import ArtisanDataProcessor
from rag_nlp_model import MultilingualRAGModel
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedMultilingualArtisanChatbot:
    def __init__(self, csv_path: str, model_data_path: str = None, use_rag: bool = True):
        self.data_processor = ArtisanDataProcessor(csv_path)
        self.use_rag = use_rag
        
        # Load or generate model data
        if model_data_path and self.data_processor.load_model_data(model_data_path):
            logger.info("Loaded existing model data")
        else:
            logger.info("Processing data from scratch")
            if model_data_path:
                self.data_processor.save_model_data(model_data_path)
        
        # Initialize multilingual RAG model
        if self.use_rag:
            self.rag_model = MultilingualRAGModel()
            self._initialize_rag_system()
        
        # Initialize NLP models
        self.sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Initialize text classification pipeline
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
        # Enhanced intent categories
        self.intent_labels = [
            "find artist by name",
            "find artist by craft", 
            "find artist by location",
            "find artist by state and craft",
            "get contact information",
            "get statistics",
            "general greeting",
            "compare artists",
            "multilingual query",
            "help request"
        ]
        
        # Supported languages
        self.supported_languages = ['english', 'hindi', 'tamil', 'telugu']
        
        # Load OpenAI API key if available
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if self.openai_key:
            openai.api_key = self.openai_key
        
        # Conversation history for context
        self.conversation_history = []
        
    def _initialize_rag_system(self):
        """Initialize RAG system with training data"""
        try:
            # Check if training data exists
            if os.path.exists('multilingual_training_data.json'):
                logger.info("Training RAG model with existing data...")
                self.rag_model.train_from_conversations('multilingual_training_data.json')
            else:
                logger.info("Generating training data for RAG system...")
                from multilingual_training_data import MultilingualTrainingDataGenerator
                
                generator = MultilingualTrainingDataGenerator()
                conversations = generator.generate_training_conversations(1000)
                knowledge_base = generator.generate_craft_knowledge_base()
                generator.save_training_data(conversations, knowledge_base)
                
                # Train RAG model
                self.rag_model.train_from_conversations('multilingual_training_data.json')
                
            logger.info("RAG system initialized successfully")
            
        except Exception as e:
            logger.error(f"RAG system initialization failed: {e}")
            self.use_rag = False
    
    def classify_intent(self, user_message: str) -> str:
        """Classify user intent using BART model"""
        result = self.classifier(user_message, self.intent_labels)
        return result['labels'][0]
    
    def extract_entities(self, user_message: str) -> Dict[str, Any]:
        """Extract entities from user message using pattern matching and NLP"""
        entities = {
            'state': None,
            'district': None,
            'craft': None,
            'name': None,
            'age_range': None
        }
        
        # Get available options from data
        stats = self.data_processor.get_stats()
        states = [s.lower() for s in stats.get('states', [])]
        crafts = [c.lower() for c in stats.get('crafts', [])]
        
        message_lower = user_message.lower()
        
        # Extract state
        for state in states:
            if state in message_lower:
                entities['state'] = state.title()
                break
        
        # Extract craft
        for craft in crafts:
            if craft.lower() in message_lower:
                entities['craft'] = craft.title()
                break
        
        # Extract name (if quoted or proper noun patterns)
        name_patterns = [
            r'"([^"]+)"',  # Quoted names
            r"named\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # "named John Doe"
            r"artist\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # "artist John Doe"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_message)
            if match:
                entities['name'] = match.group(1)
                break
        
        # Extract age range
        age_pattern = r"age\s+(\d+)(?:\s*[-to]\s*(\d+))?"
        age_match = re.search(age_pattern, message_lower)
        if age_match:
            if age_match.group(2):
                entities['age_range'] = (int(age_match.group(1)), int(age_match.group(2)))
            else:
                entities['age_range'] = (int(age_match.group(1)), int(age_match.group(1)))
        
        return entities
    
    def generate_response_with_llm(self, user_message: str, context: Dict[str, Any]) -> str:
        """Generate response using OpenAI GPT if available"""
        if not self.openai_key:
            return None
        
        try:
            system_prompt = f"""
            You are an AI assistant for Kala-Kaart, a platform connecting people with traditional Indian artisans.
            
            Context:
            - Total artists in database: {context.get('total_artists', 0)}
            - Available states: {', '.join(context.get('states', [])[:10])}
            - Available crafts: {', '.join(context.get('crafts', [])[:10])}
            
            User's message: {user_message}
            
            Provide a helpful, informative response about finding artisans. Be conversational but professional.
            If specific artist data is provided in the context, include it in your response.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def process_query_enhanced(self, user_message: str, conversation_context: List[str] = None) -> Dict[str, Any]:
        """Enhanced query processing with RAG and multilingual support"""
        
        # Update conversation history
        if conversation_context:
            self.conversation_history = conversation_context[-10:]  # Keep last 10 messages
        
        self.conversation_history.append(user_message)
        
        # Use RAG model if available
        if self.use_rag and self.rag_model:
            try:
                rag_result = self.rag_model.query(user_message, {'history': self.conversation_history})
                
                # Extract information from RAG response
                detected_language = rag_result.get('detected_language', 'english')
                rag_response = rag_result.get('response', '')
                retrieved_docs = rag_result.get('retrieved_docs', [])
                confidence = rag_result.get('confidence', False)
                
                # If RAG provides a confident response, use it
                if confidence and rag_response:
                    # Get relevant artists from database
                    artists = self._get_artists_from_rag_docs(retrieved_docs)
                    
                    return {
                        'intent': 'rag_response',
                        'entities': self._extract_entities_from_rag(retrieved_docs),
                        'message': rag_response,
                        'artists': artists,
                        'suggestions': self._generate_contextual_suggestions(detected_language, user_message),
                        'stats': self.data_processor.get_stats(),
                        'detected_language': detected_language,
                        'confidence_score': 0.9,
                        'source': 'RAG'
                    }
                    
            except Exception as e:
                logger.error(f"RAG query failed: {e}")
        
        # Fallback to original processing
        return self.process_query_fallback(user_message)
    
    def _get_artists_from_rag_docs(self, retrieved_docs: List[Dict]) -> List[Dict]:
        """Extract artist information from retrieved documents"""
        artists = []
        
        for doc in retrieved_docs:
            # If document contains artist information
            if 'craft' in doc.get('metadata', {}):
                craft = doc['metadata']['craft']
                
                # Search for artists with this craft
                craft_artists = self.data_processor.search_artists({'craft_type': craft})
                artists.extend(craft_artists[:3])  # Add top 3
                
            # Look for location information
            if 'location' in doc.get('metadata', {}):
                location = doc['metadata']['location'] 
                location_artists = self.data_processor.search_artists({'state': location})
                artists.extend(location_artists[:2])  # Add top 2
        
        # Remove duplicates and limit results
        unique_artists = []
        seen_ids = set()
        
        for artist in artists:
            if artist.get('id') not in seen_ids:
                unique_artists.append(artist)
                seen_ids.add(artist.get('id'))
                
            if len(unique_artists) >= 10:  # Limit to 10 artists
                break
        
        return unique_artists
    
    def _extract_entities_from_rag(self, retrieved_docs: List[Dict]) -> Dict[str, Any]:
        """Extract entities from RAG retrieved documents"""
        entities = {}
        
        for doc in retrieved_docs:
            metadata = doc.get('metadata', {})
            
            if 'craft' in metadata:
                entities['craft'] = metadata['craft']
            if 'location' in metadata:
                entities['location'] = metadata['location']
            if 'language' in metadata:
                entities['language'] = metadata['language']
        
        return entities
    
    def _generate_contextual_suggestions(self, language: str, user_message: str) -> List[str]:
        """Generate contextual suggestions based on language and message"""
        
        suggestions_map = {
            'english': [
                "Show more artists",
                "Find similar crafts", 
                "Search by location",
                "Get contact details",
                "Learn about techniques"
            ],
            'hindi': [
                "और कलाकार दिखाएं",
                "समान शिल्प खोजें",
                "स्थान के आधार पर खोजें", 
                "संपर्क विवरण प्राप्त करें",
                "तकनीकों के बारे में जानें"
            ],
            'tamil': [
                "மேலும் கலைஞர்களை காட்டுங்கள்",
                "ஒத்த கைவினைகளைக் கண்டுபிடியுங்கள்",
                "இடத்தின் அடிப்படையில் தேடுங்கள்",
                "தொடர்பு விவரங்களைப் பெறுங்கள்",
                "நுட்பங்களைப் பற்றி அறிந்து கொள்ளுங்கள்"
            ],
            'telugu': [
                "మరిన్ని కళాకారులను చూపించండి",
                "సారూప్య చేతిపనులను కనుగొనండి",
                "స్థానం ఆధారంగా వెతకండి",
                "సంప్రదింపు వివరాలను పొందండి", 
                "పద్ధతుల గురించి తెలుసుకోండి"
            ]
        }
        
        base_suggestions = suggestions_map.get(language, suggestions_map['english'])
        
        # Add context-specific suggestions
        message_lower = user_message.lower()
        
        if any(craft in message_lower for craft in ['pottery', 'मिट्टी', 'களிமண்', 'మట్టి']):
            if language == 'english':
                base_suggestions.append("Find pottery workshops")
            elif language == 'hindi':
                base_suggestions.append("मिट्टी के बर्तन की कार्यशालाएं खोजें")
        
        return base_suggestions[:5]  # Return top 5
    
    def process_query_fallback(self, user_message: str) -> Dict[str, Any]:
        """Process user query and return appropriate response"""
        # Classify intent
        intent = self.classify_intent(user_message)
        
        # Extract entities
        entities = self.extract_entities(user_message)
        
        # Get context stats
        stats = self.data_processor.get_stats()
        
        response = {
            'intent': intent,
            'entities': entities,
            'message': '',
            'artists': [],
            'suggestions': [],
            'stats': stats
        }
        
        try:
            if intent == "find artist by name" and entities['name']:
                artists = self.data_processor.search_artists({'name': entities['name']})
                response['artists'] = artists[:10]
                response['message'] = f"Found {len(artists)} artist(s) matching '{entities['name']}':"
                
            elif intent == "find artist by craft" and entities['craft']:
                artists = self.data_processor.search_artists({'craft_type': entities['craft']})
                response['artists'] = artists[:10]
                response['message'] = f"Found {len(artists)} {entities['craft']} artists:"
                
            elif intent == "find artist by location":
                filters = {}
                if entities['state']:
                    filters['state'] = entities['state']
                if entities['district']:
                    filters['district'] = entities['district']
                
                artists = self.data_processor.search_artists(filters)
                location = entities['state'] or entities['district'] or "specified location"
                response['artists'] = artists[:10]
                response['message'] = f"Found {len(artists)} artists in {location}:"
                
            elif intent == "find artist by state and craft":
                filters = {}
                if entities['state']:
                    filters['state'] = entities['state']
                if entities['craft']:
                    filters['craft_type'] = entities['craft']
                
                artists = self.data_processor.search_artists(filters)
                response['artists'] = artists[:10]
                craft_text = entities['craft'] or "various crafts"
                state_text = entities['state'] or "specified state"
                response['message'] = f"Found {len(artists)} {craft_text} artists in {state_text}:"
                
            elif intent == "get statistics":
                response['message'] = f"""
                Here are some statistics about our artisan database:
                - Total Artists: {stats['total_artists']}
                - States Covered: {stats['unique_states']}
                - Districts: {stats['unique_districts']}
                - Craft Types: {stats['unique_crafts']}
                - Age Range: {stats['age_distribution']['min']}-{stats['age_distribution']['max']} years
                """
                
            elif intent == "general greeting":
                response['message'] = """
                Hello! I'm your Kala-Kaart AI assistant. I can help you find traditional Indian artisans.
                
                You can ask me to:
                - Find artists by name, craft, or location
                - Get contact information
                - Compare different crafts or regions
                - Get statistics about our database
                
                Try asking: "Show me pottery artists in Rajasthan" or "Find artists named Raj"
                """
                response['suggestions'] = [
                    "Show pottery artists",
                    "Find artists in Maharashtra",
                    "Tell me about textile craftsmen",
                    "Get database statistics"
                ]
                
            else:
                # Use semantic similarity search as fallback
                similar_artists = self.data_processor.find_similar_artists(user_message, 5)
                response['artists'] = similar_artists
                response['message'] = f"Here are some artists that might interest you based on your query:"
            
            # Generate LLM response if available
            llm_response = self.generate_response_with_llm(user_message, stats)
            if llm_response:
                response['llm_message'] = llm_response
            
            # Add suggestions based on found artists
            if response['artists']:
                states_found = list(set([a.get('state') for a in response['artists'][:3]]))
                crafts_found = list(set([a.get('craft_type') for a in response['artists'][:3]]))
                
                response['suggestions'] = [
                    f"More artists in {states_found[0]}" if states_found else "Show all states",
                    f"Other {crafts_found[0]} artists" if crafts_found else "Show all crafts",
                    "Get contact details",
                    "Search by different criteria"
                ]
        
        except Exception as e:
            print(f"Error processing query: {e}")
            response['message'] = "I apologize, but I encountered an error processing your request. Please try again."
            response['suggestions'] = ["Try a different search", "Get help", "View all artists"]
        
        return response
    
    def get_conversation_suggestions(self, conversation_history: List[str]) -> List[str]:
        """Generate contextual suggestions based on conversation history"""
        if not conversation_history:
            return [
                "Show me pottery artists",
                "Find artists in Kerala", 
                "Tell me about textile crafts",
                "Get database statistics"
            ]
        
        # Analyze recent queries to suggest related searches
        recent_query = conversation_history[-1].lower()
        stats = self.data_processor.get_stats()
        
        suggestions = []
        
        # If they searched for a state, suggest crafts in that state
        for state in stats.get('states', [])[:5]:
            if state.lower() in recent_query:
                suggestions.extend([
                    f"Popular crafts in {state}",
                    f"Contact artists in {state}",
                    f"Compare {state} with other states"
                ])
                break
        
        # If they searched for a craft, suggest states with that craft
        for craft in stats.get('crafts', [])[:5]:
            if craft.lower() in recent_query:
                suggestions.extend([
                    f"States with {craft} artists",
                    f"Best {craft} artists",
                    f"Learn about {craft} techniques"
                ])
                break
        
        # Default suggestions
        if not suggestions:
            suggestions = [
                "Show different craft types",
                "Find artists by location",
                "Get contact information",
                "Compare artist profiles"
            ]
        
        return suggestions[:4]

# Alias for backward compatibility
ArtisanChatbot = EnhancedMultilingualArtisanChatbot