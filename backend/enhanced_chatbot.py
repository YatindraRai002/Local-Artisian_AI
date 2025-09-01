"""
Enhanced Multilingual Chatbot for Kala-Kaart
Integrates data processing, NLP, and RAG capabilities with lightweight dependencies
"""

import os
import re
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from data_processor import ArtisanDataProcessor
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedKalaKaartChatbot:
    """
    Advanced chatbot that integrates multiple AI capabilities:
    - Natural Language Understanding
    - Semantic Search
    - Context-aware responses
    - Multilingual support (basic)
    - RAG-like knowledge retrieval
    """
    
    def __init__(self, csv_path: str, model_data_path: str = None):
        logger.info("Initializing Enhanced Kala-Kaart Chatbot...")
        
        # Initialize data processor
        self.data_processor = ArtisanDataProcessor(csv_path)
        
        # Load or generate model data
        if model_data_path and self.data_processor.load_model_data(model_data_path):
            logger.info("Loaded existing model data")
        else:
            logger.info("Processing data from scratch")
            if model_data_path:
                self.data_processor.save_model_data(model_data_path)
        
        # Initialize knowledge base
        self._build_knowledge_base()
        
        # Enhanced intent patterns with multilingual support
        self.intent_patterns = {
            'find_by_craft': [
                r'\b(find|show|get|search)\b.*\b(artist|artisan|craftsman|craftspeople)\b.*\b(pottery|weaving|painting|carving|textile|metal|wood|stone|jewelry|embroidery|carpet|handicraft)\b',
                r'\b(pottery|weaving|painting|carving|textile|metal|wood|stone|jewelry|embroidery|carpet|handicraft)\b.*\b(artist|artisan|craftsman|craftspeople)\b',
                r'\b(कुम्हार|बुनकर|चित्रकार|मूर्तिकार|कारीगर)\b',  # Hindi
                r'\b(குயவன்|நெசவாளர்|ஓவியர்|சிற்பி)\b'  # Tamil
            ],
            'find_by_location': [
                r'\b(find|show|get|search)\b.*\b(artist|artisan|craftsman|craftspeople)\b.*\b(in|from|at)\b.*\b([A-Z][a-zA-Z\s]+)\b',
                r'\b(artist|artisan|craftsman|craftspeople)\b.*\b(in|from|at)\b.*\b([A-Z][a-zA-Z\s]+)\b',
                r'\b([A-Z][a-zA-Z\s]+)\b.*\b(artist|artisan|craftsman|craftspeople)\b'
            ],
            'get_statistics': [
                r'\b(how many|count|total|number|statistics|stats|data)\b',
                r'\b(database|information|overview)\b',
                r'\b(कितने|संख्या|आंकड़े)\b',  # Hindi
                r'\b(எத்தனை|எண்ணிக்கை)\b'  # Tamil
            ],
            'get_contact': [
                r'\b(contact|phone|call|reach|email|address|number)\b',
                r'\b(संपर्क|फोन|नंबर)\b',  # Hindi
                r'\b(தொடர்பு|फোन|எண்)\b'  # Tamil
            ],
            'greeting': [
                r'\b(hello|hi|hey|greetings|good morning|good afternoon|good evening)\b',
                r'\b(नमस्ते|हैलो|प्रणाम)\b',  # Hindi
                r'\b(வணக்கம்|ஹலோ)\b'  # Tamil
            ]
        }
        
        # Enhanced entity extraction patterns
        self.entity_patterns = {
            'states': [
                'andhra pradesh', 'assam', 'bihar', 'chhattisgarh', 'goa', 'gujarat', 
                'haryana', 'himachal pradesh', 'jammu kashmir', 'jharkhand', 'karnataka', 
                'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 
                'mizoram', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu', 
                'telangana', 'tripura', 'uttar pradesh', 'uttarakhand', 'west bengal'
            ],
            'crafts': [
                'pottery', 'weaving', 'painting', 'carving', 'textile', 'metal', 'wood', 
                'stone', 'jewelry', 'embroidery', 'carpet', 'handicraft', 'bamboo', 
                'cane', 'banarasi', 'bandhani', 'bidriware', 'block printing', 'blue pottery',
                'channapatna toys', 'chikankari', 'dokra', 'handloom', 'kalamkari',
                'kutch embroidery', 'madhubani', 'pattachitra', 'phulkari', 'tanjore',
                'terracotta', 'warli', 'zardozi', 'zari'
            ]
        }
        
        # Conversation context
        self.conversation_context = {
            'last_intent': None,
            'last_entities': {},
            'conversation_history': [],
            'user_preferences': {}
        }
        
        # Response templates
        self.response_templates = self._load_response_templates()
        
        logger.info("Enhanced chatbot initialized successfully!")
    
    def _build_knowledge_base(self):
        """Build a knowledge base from the artist data"""
        self.knowledge_base = {
            'craft_descriptions': {
                'pottery': 'Traditional pottery involves shaping clay into beautiful vessels, bowls, and decorative items using techniques passed down through generations.',
                'weaving': 'Handloom weaving creates intricate textiles using traditional looms, producing everything from sarees to carpets.',
                'painting': 'Traditional Indian painting includes styles like Madhubani, Warli, and Pattachitra, each with unique cultural significance.',
                'carving': 'Wood and stone carving creates intricate sculptures, decorative items, and architectural elements.',
                'embroidery': 'Traditional embroidery like Chikankari and Phulkari adds beautiful patterns to fabrics using colorful threads.',
            },
            'regional_specialties': {
                'gujarat': ['bandhani', 'block printing', 'pottery', 'embroidery'],
                'rajasthan': ['blue pottery', 'stone carving', 'carpet weaving', 'painting'],
                'west bengal': ['handloom weaving', 'dokra', 'terracotta'],
                'uttar pradesh': ['chikankari', 'carpet weaving', 'brass work'],
                'tamil nadu': ['tanjore painting', 'bronze work', 'silk weaving'],
            },
            'craft_centers': {}
        }
        
        # Build craft centers from data
        if hasattr(self.data_processor, 'df') and not self.data_processor.df.empty:
            for _, row in self.data_processor.df.iterrows():
                state = row.get('state', '').lower()
                craft = row.get('craft_type', '').lower()
                district = row.get('district', '')
                
                if state not in self.knowledge_base['craft_centers']:
                    self.knowledge_base['craft_centers'][state] = {}
                if craft not in self.knowledge_base['craft_centers'][state]:
                    self.knowledge_base['craft_centers'][state][craft] = []
                if district not in self.knowledge_base['craft_centers'][state][craft]:
                    self.knowledge_base['craft_centers'][state][craft].append(district)
    
    def _load_response_templates(self):
        """Load response templates for different scenarios"""
        return {
            'greeting': [
                "🙏 Welcome to Kala-Kaart! I'm your AI assistant for discovering India's traditional artisans.",
                "Hello! I'm here to help you find skilled artisans and learn about traditional Indian crafts.",
                "Namaste! How can I help you connect with traditional artists today?"
            ],
            'craft_found': [
                "🎨 I found {count} talented {craft} artists for you!",
                "✨ Here are {count} skilled {craft} artisans from our database:",
                "🎯 Perfect! I located {count} {craft} experts:"
            ],
            'location_found': [
                "📍 I found {count} artists in {location}:",
                "🌟 Here are {count} talented artisans from {location}:",
                "🎨 {location} has {count} skilled artists in our database:"
            ],
            'combined_found': [
                "🎯 Excellent! I found {count} {craft} artists in {location}:",
                "✨ Perfect match! Here are {count} {craft} artisans from {location}:",
                "🎨 I located {count} skilled {craft} artists in {location}:"
            ],
            'no_results': [
                "❌ I couldn't find artists matching your criteria. Try broadening your search or check the spelling.",
                "🔍 No matches found. Would you like me to suggest similar crafts or nearby locations?",
                "❌ No artists found with those specifications. Let me suggest some alternatives."
            ],
            'statistics': [
                "📊 Our Kala-Kaart database contains {total} verified artisans from {states} states, practicing {crafts} traditional crafts.",
                "🎨 We have {total} talented artists across {states} states, specializing in {crafts} different craft forms.",
                "📈 Database overview: {total} artists • {states} states • {crafts} craft types • Age range: {age_min}-{age_max} years"
            ]
        }
    
    def detect_language(self, text: str) -> str:
        """Basic language detection using character patterns"""
        # Check for Devanagari script (Hindi)
        if re.search(r'[\u0900-\u097F]', text):
            return 'hindi'
        # Check for Tamil script
        elif re.search(r'[\u0B80-\u0BFF]', text):
            return 'tamil'
        # Check for Telugu script
        elif re.search(r'[\u0C00-\u0C7F]', text):
            return 'telugu'
        else:
            return 'english'
    
    def classify_intent(self, user_message: str) -> str:
        """Classify user intent using pattern matching"""
        user_message_lower = user_message.lower()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_message_lower, re.IGNORECASE):
                    return intent
        
        return 'general_query'
    
    def extract_entities(self, user_message: str) -> Dict[str, Any]:
        """Extract entities from user message using enhanced pattern matching"""
        entities = {}
        user_message_lower = user_message.lower()
        
        # Extract states
        for state in self.entity_patterns['states']:
            if state in user_message_lower:
                entities['state'] = state.title()
                break
        
        # Extract crafts
        for craft in self.entity_patterns['crafts']:
            if craft in user_message_lower:
                entities['craft'] = craft.title()
                break
        
        # Extract age-related entities
        if any(word in user_message_lower for word in ['young', 'youth']):
            entities['age_max'] = 35
        elif any(word in user_message_lower for word in ['old', 'senior', 'elderly']):
            entities['age_min'] = 50
        
        # Extract gender
        if any(word in user_message_lower for word in ['male', 'men', 'man']):
            entities['gender'] = 'Male'
        elif any(word in user_message_lower for word in ['female', 'women', 'woman']):
            entities['gender'] = 'Female'
        
        return entities
    
    def semantic_search(self, query: str, entities: Dict[str, Any], limit: int = 5) -> List[Dict]:
        """Perform semantic search using the data processor"""
        search_filters = {}
        
        # Map entities to search filters
        if 'state' in entities:
            search_filters['state'] = entities['state']
        if 'craft' in entities:
            search_filters['craft_type'] = entities['craft']
        if 'age_min' in entities:
            search_filters['age_min'] = entities['age_min']
        if 'age_max' in entities:
            search_filters['age_max'] = entities['age_max']
        if 'gender' in entities:
            # This would need to be implemented in data_processor
            pass
        
        # Use data processor's search functionality
        if search_filters:
            results = self.data_processor.search_artists(search_filters)
            return results[:limit]
        
        # If no specific filters, try similarity search
        if hasattr(self.data_processor, 'find_similar_artists') and self.data_processor.embeddings is not None:
            results = self.data_processor.find_similar_artists(query, limit)
            return results
        
        return []
    
    def generate_contextual_response(self, intent: str, entities: Dict[str, Any], 
                                   artists: List[Dict], stats: Dict) -> Dict[str, Any]:
        """Generate contextual response based on intent, entities, and results"""
        
        if intent == 'greeting':
            import random
            message = random.choice(self.response_templates['greeting'])
            message += f"\n\n📊 I have access to {stats.get('total_artists', 0):,} verified artisans across India!"
            
            suggestions = [
                "Show me pottery artists",
                "Find artists in Gujarat", 
                "Tell me about Rajasthani crafts",
                "Database statistics"
            ]
        
        elif intent == 'get_statistics':
            import random
            template = random.choice(self.response_templates['statistics'])
            message = template.format(
                total=f"{stats.get('total_artists', 0):,}",
                states=stats.get('unique_states', 0),
                crafts=stats.get('unique_crafts', 0),
                age_min=stats.get('age_distribution', {}).get('min', 18),
                age_max=stats.get('age_distribution', {}).get('max', 70)
            )
            
            # Add detailed breakdown
            message += f"\n\n🏛️ **States:** {', '.join(stats.get('states', [])[:10])}{'...' if len(stats.get('states', [])) > 10 else ''}"
            message += f"\n🎨 **Popular Crafts:** {', '.join(stats.get('crafts', [])[:8])}"
            
            suggestions = ["Find pottery artists", "Show artists by state", "Explore craft types"]
        
        elif artists:
            # Determine response type based on entities
            if 'state' in entities and 'craft' in entities:
                template = self.response_templates['combined_found'][0]
                message = template.format(
                    count=len(artists),
                    craft=entities['craft'],
                    location=entities['state']
                )
            elif 'craft' in entities:
                template = self.response_templates['craft_found'][0]
                message = template.format(count=len(artists), craft=entities['craft'])
            elif 'state' in entities:
                template = self.response_templates['location_found'][0]
                message = template.format(count=len(artists), location=entities['state'])
            else:
                message = f"🎨 I found {len(artists)} artists matching your query:"
            
            # Add knowledge base information
            if 'craft' in entities:
                craft_lower = entities['craft'].lower()
                if craft_lower in self.knowledge_base['craft_descriptions']:
                    message += f"\n\n💡 **About {entities['craft']}:** {self.knowledge_base['craft_descriptions'][craft_lower]}"
            
            suggestions = [
                "Get contact information",
                "Find similar artists", 
                "Show more results"
            ]
        
        else:
            import random
            message = random.choice(self.response_templates['no_results'])
            
            # Suggest alternatives based on entities
            alternatives = []
            if 'craft' in entities:
                alternatives.append(f"Try '{entities['craft']} artists in other states'")
            if 'state' in entities:
                alternatives.append(f"Browse all crafts in {entities['state']}")
            
            if alternatives:
                message += f"\n\n🔍 **Try instead:** {', '.join(alternatives)}"
            
            suggestions = ["Browse all crafts", "Find by location", "Popular artists"]
        
        return {
            "message": message,
            "artists": artists,
            "suggestions": suggestions,
            "context": {
                "intent": intent,
                "entities": entities,
                "language": self.detect_language(entities.get('original_query', ''))
            }
        }
    
    def update_conversation_context(self, intent: str, entities: Dict[str, Any], user_message: str):
        """Update conversation context for better continuity"""
        self.conversation_context['last_intent'] = intent
        self.conversation_context['last_entities'] = entities
        self.conversation_context['conversation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'intent': intent,
            'entities': entities
        })
        
        # Keep only last 10 interactions
        if len(self.conversation_context['conversation_history']) > 10:
            self.conversation_context['conversation_history'] = \
                self.conversation_context['conversation_history'][-10:]
    
    def process_query(self, user_message: str, conversation_history: List[str] = None) -> Dict[str, Any]:
        """Main query processing pipeline"""
        try:
            logger.info(f"Processing query: {user_message}")
            
            # Detect language
            language = self.detect_language(user_message)
            
            # Classify intent
            intent = self.classify_intent(user_message)
            
            # Extract entities
            entities = self.extract_entities(user_message)
            entities['original_query'] = user_message
            entities['language'] = language
            
            # Get database statistics
            stats = self.data_processor.get_stats()
            
            # Perform search if needed
            artists = []
            if intent in ['find_by_craft', 'find_by_location', 'general_query'] and entities:
                artists = self.semantic_search(user_message, entities, limit=5)
                
                # Transform artists to match frontend expectations
                transformed_artists = []
                for artist in artists:
                    if isinstance(artist, dict):
                        transformed_artist = {
                            "id": artist.get("artisan_id", ""),
                            "name": artist.get("name", ""),
                            "craft_type": artist.get("craft_type", ""),
                            "location": {
                                "state": artist.get("state", ""),
                                "district": artist.get("district", ""),
                                "village": artist.get("village", "")
                            },
                            "contact": {
                                "email": artist.get("contact_email", ""),
                                "phone": str(artist.get("contact_phone", "")),
                                "phone_available": artist.get("contact_phone_boolean", "").lower() == "yes"
                            },
                            "languages": artist.get("languages_spoken", "").split(", ") if artist.get("languages_spoken") else [],
                            "age": artist.get("age", 0),
                            "gender": artist.get("gender", ""),
                            "government_id": artist.get("govt_artisan_id", ""),
                            "cluster_code": artist.get("artisan_cluster_code", "")
                        }
                        transformed_artists.append(transformed_artist)
                
                artists = transformed_artists
            
            # Generate response
            response = self.generate_contextual_response(intent, entities, artists, stats)
            
            # Update context
            self.update_conversation_context(intent, entities, user_message)
            
            return {
                "intent": intent,
                "entities": entities,
                "message": response["message"],
                "llm_message": None,
                "artists": response["artists"],
                "suggestions": response["suggestions"],
                "stats": stats,
                "context": response["context"]
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "intent": "error",
                "entities": {},
                "message": "❌ I encountered an error processing your request. Please try rephrasing your question.",
                "llm_message": None,
                "artists": [],
                "suggestions": ["Try a different query", "Browse by craft", "Database statistics"],
                "stats": self.data_processor.get_stats(),
                "context": {"error": str(e)}
            }


# Alias for backward compatibility
ArtisanChatbot = EnhancedKalaKaartChatbot