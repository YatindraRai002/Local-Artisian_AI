"""
Lightweight Enhanced Chatbot for Kala-Kaart
No heavy dependencies, pure Python implementation with smart NLP
"""

import os
import re
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightweightDataProcessor:
    """Lightweight data processor without pandas dependency"""
    
    def __init__(self, csv_path: str, max_artists: Optional[int] = None):
        self.csv_path = csv_path
        self.artists_data = []
        self.max_artists = max_artists
        self.load_data()
    
    def load_data(self):
        """Load CSV data with optional limit for serverless deployment"""
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                for row in reader:
                    if row.get('name') and row.get('craft_type') and row.get('state'):
                        # Convert age to int if possible
                        try:
                            row['age'] = int(row['age'])
                        except:
                            row['age'] = 0
                        self.artists_data.append(row)
                        count += 1
                        
                        # Stop if max_artists limit reached
                        if self.max_artists and count >= self.max_artists:
                            break
            
            logger.info(f"Loaded {len(self.artists_data)} artist records (limit: {self.max_artists or 'none'})")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.artists_data = []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the dataset"""
        if not self.artists_data:
            return {}
        
        states = set()
        districts = set()
        crafts = set()
        ages = []
        
        for artist in self.artists_data:
            if artist.get('state'):
                states.add(artist['state'])
            if artist.get('district'):
                districts.add(artist['district'])
            if artist.get('craft_type'):
                crafts.add(artist['craft_type'])
            if isinstance(artist.get('age'), int):
                ages.append(artist['age'])
        
        age_stats = {}
        if ages:
            age_stats = {
                'min': min(ages),
                'max': max(ages),
                'mean': sum(ages) / len(ages)
            }
        
        return {
            'total_artists': len(self.artists_data),
            'unique_states': len(states),
            'unique_districts': len(districts),
            'unique_crafts': len(crafts),
            'states': sorted(list(states)),
            'crafts': sorted(list(crafts)),
            'age_distribution': age_stats
        }
    
    def search_artists(self, filters: Dict[str, Any]) -> List[Dict]:
        """Search artists with filters"""
        results = []
        
        for artist in self.artists_data:
            # Apply filters
            if 'state' in filters and filters['state']:
                if filters['state'].lower() not in artist.get('state', '').lower():
                    continue
            
            if 'district' in filters and filters['district']:
                if filters['district'].lower() not in artist.get('district', '').lower():
                    continue
            
            if 'craft_type' in filters and filters['craft_type']:
                if filters['craft_type'].lower() not in artist.get('craft_type', '').lower():
                    continue
            
            if 'name' in filters and filters['name']:
                if filters['name'].lower() not in artist.get('name', '').lower():
                    continue
            
            if 'age_min' in filters:
                if artist.get('age', 0) < filters['age_min']:
                    continue
            
            if 'age_max' in filters:
                if artist.get('age', 0) > filters['age_max']:
                    continue
            
            results.append(artist)
        
        return results
    
    def find_similar_artists(self, query: str, top_k: int = 5) -> List[Dict]:
        """Find similar artists using simple text matching"""
        query_lower = query.lower()
        scored_artists = []
        
        for artist in self.artists_data:
            score = 0
            
            # Score based on craft type match
            if query_lower in artist.get('craft_type', '').lower():
                score += 10
            
            # Score based on state match
            if any(word in artist.get('state', '').lower() for word in query_lower.split()):
                score += 5
            
            # Score based on name match
            if any(word in artist.get('name', '').lower() for word in query_lower.split()):
                score += 3
            
            # Score based on village/district match
            if any(word in artist.get('district', '').lower() for word in query_lower.split()):
                score += 2
            
            if score > 0:
                artist_copy = artist.copy()
                artist_copy['similarity_score'] = score
                scored_artists.append(artist_copy)
        
        # Sort by score and return top k
        scored_artists.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_artists[:top_k]


class LightweightEnhancedChatbot:
    """
    Enhanced chatbot with advanced NLP capabilities but no heavy dependencies
    """
    
    def __init__(self, csv_path: str, max_artists: Optional[int] = None):
        logger.info("Initializing Lightweight Enhanced Chatbot...")
        
        # Initialize data processor with real CSV path
        if not csv_path:
            # Default to the clustered artisan data
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public', 'Artisans.csv')
        
        self.data_processor = LightweightDataProcessor(csv_path, max_artists)
        
        if not self.data_processor.artists_data:
            logger.error("Failed to load artist data - check CSV path")
        else:
            logger.info(f"Successfully loaded {len(self.data_processor.artists_data)} artists from clustering model")
        
        # Initialize knowledge base
        self._build_knowledge_base()
        
        # Enhanced intent patterns with multilingual support
        self.intent_patterns = {
            'find_by_craft': [
                r'\b(find|show|get|search|display|list)\b.*\b(artist|artisan|craftsman|craftspeople|maker)\b.*\b(pottery|weaving|painting|carving|textile|metal|wood|stone|jewelry|embroidery|carpet|handicraft|bamboo|cane|banarasi|bandhani|bidriware|chikankari|kalamkari|madhubani|pattachitra|phulkari|tanjore|terracotta|warli|zardozi|zari|dokra|handloom|kutch|lac|leather|metalwork|rogan|sandalwood|shell|sikki|silver|filigree|blue pottery|black pottery|block printing|channapatna|coir|durrie|jute|kundan|paper mache|thanjavur)\b',
                r'\b(pottery|weaving|painting|carving|textile|metal|wood|stone|jewelry|embroidery|carpet|handicraft|bamboo|cane|banarasi|bandhani|bidriware|chikankari|kalamkari|madhubani|pattachitra|phulkari|tanjore|terracotta|warli|zardozi|zari|dokra|handloom|kutch|lac|leather|metalwork|rogan|sandalwood|shell|sikki|silver|filigree|blue pottery|black pottery|block printing|channapatna|coir|durrie|jute|kundan|paper mache|thanjavur)\b.*\b(artist|artisan|craftsman|craftspeople|maker)\b',
                r'\b(कुम्हार|बुनकर|चित्रकार|मूर्तिकार|कारीगर|शिल्पकार)\b',  # Hindi
                r'\b(குயவன்|நெசவாளர்|ஓவியர்|சிற்பி|கைவினைஞர்)\b'  # Tamil
            ],
            'find_by_location': [
                r'\b(find|show|get|search|display|list)\b.*\b(artist|artisan|craftsman|craftspeople|maker)\b.*\b(in|from|at|of)\b.*\b(andhra pradesh|assam|bihar|chhattisgarh|goa|gujarat|haryana|himachal pradesh|jammu|kashmir|jharkhand|karnataka|kerala|ladakh|madhya pradesh|maharashtra|manipur|meghalaya|mizoram|odisha|punjab|rajasthan|sikkim|tamil nadu|telangana|tripura|uttar pradesh|uttarakhand|west bengal|delhi|mumbai|chennai|bangalore|hyderabad|pune|ahmedabad|surat|jaipur|lucknow|kanpur|nagpur|visakhapatnam|bhopal|patna|vadodara|ludhiana|agra|nashik|faridabad|meerut|rajkot)\b',
                r'\b(artist|artisan|craftsman|craftspeople|maker)\b.*\b(in|from|at|of)\b.*\b(andhra pradesh|assam|bihar|chhattisgarh|goa|gujarat|haryana|himachal pradesh|jammu|kashmir|jharkhand|karnataka|kerala|ladakh|madhya pradesh|maharashtra|manipur|meghalaya|mizoram|odisha|punjab|rajasthan|sikkim|tamil nadu|telangana|tripura|uttar pradesh|uttarakhand|west bengal|delhi|mumbai|chennai|bangalore|hyderabad|pune|ahmedabad|surat|jaipur|lucknow|kanpur|nagpur|visakhapatnam|bhopal|patna|vadodara|ludhiana|agra|nashik|faridabad|meerut|rajkot)\b',
                r'\b(andhra pradesh|assam|bihar|chhattisgarh|goa|gujarat|haryana|himachal pradesh|jammu|kashmir|jharkhand|karnataka|kerala|ladakh|madhya pradesh|maharashtra|manipur|meghalaya|mizoram|odisha|punjab|rajasthan|sikkim|tamil nadu|telangana|tripura|uttar pradesh|uttarakhand|west bengal|delhi|mumbai|chennai|bangalore|hyderabad|pune|ahmedabad|surat|jaipur|lucknow|kanpur|nagpur|visakhapatnam|bhopal|patna|vadodara|ludhiana|agra|nashik|faridabad|meerut|rajkot)\b.*\b(artist|artisan|craftsman|craftspeople|maker)\b'
            ],
            'get_statistics': [
                r'\b(how many|count|total|number|statistics|stats|data|database|overview|information)\b',
                r'\b(कितने|संख्या|आंकड़े|जानकारी)\b',  # Hindi
                r'\b(எத்தனை|எண்ணிக்கை|தகவல்)\b'  # Tamil
            ],
            'get_contact': [
                r'\b(contact|phone|call|reach|email|address|number|telephone|mobile)\b.*\b(information|details|info)\b',
                r'\b(how to contact|how to reach|contact details|phone number)\b',
                r'\b(संपर्क|फोन|नंबर|पता)\b',  # Hindi
                r'\b(தொடர்பு|फோन|எண்|முகவரி)\b'  # Tamil
            ],
            'greeting': [
                r'\b(hello|hi|hey|greetings|good morning|good afternoon|good evening|namaste|namaskar)\b',
                r'\b(नमस्ते|हैलो|प्रणाम|नमस्कार)\b',  # Hindi
                r'\b(வணக்கம்|ஹலோ|நமஸ்காரம்)\b'  # Tamil
            ],
            'help': [
                r'\b(help|assist|guide|support|how to|what can you|capabilities)\b',
                r'\b(मदद|सहायता|गाइड)\b',  # Hindi
                r'\b(உதவி|வழிகாட்டுதல்)\b'  # Tamil
            ]
        }
        
        # Enhanced entity extraction patterns
        self.entity_patterns = {
            'states': [
                'andhra pradesh', 'assam', 'bihar', 'chhattisgarh', 'goa', 'gujarat', 
                'haryana', 'himachal pradesh', 'jammu kashmir', 'jammu & kashmir', 'jharkhand', 'karnataka', 
                'kerala', 'ladakh', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 
                'mizoram', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu', 
                'telangana', 'tripura', 'uttar pradesh', 'uttarakhand', 'west bengal', 'west bengal','kerela','tamil naidu','karnataka'
            ],
            'crafts': [
                'pottery', 'weaving', 'painting', 'carving', 'textile', 'metal', 'wood', 
                'stone', 'jewelry', 'embroidery', 'carpet', 'handicraft', 'bamboo', 
                'cane', 'banarasi', 'bandhani', 'bidriware', 'block printing', 'blue pottery',
                'black pottery', 'channapatna toys', 'chikankari', 'coir craft', 'dokra', 'bell metal',
                'durrie weaving', 'handloom weaving', 'handloom', 'jute craft', 'kalamkari',
                'kundan jewellery', 'kundan', 'kutch embroidery', 'lac work', 'leather craft',
                'madhubani painting', 'madhubani', 'metalwork', 'paper mache', 'pattachitra', 'phulkari', 
                'rogan art', 'sandalwood carving', 'shell craft', 'sikki grass',
                'silver filigree', 'stone carving', 'tanjore painting', 'terracotta',
                'thanjavur dolls', 'warli painting', 'wood carving', 'zari', 'zardozi'
            ],
            'age_descriptors': {
                'young': ('young', 'youth', 'junior', 'new'),
                'senior': ('old', 'senior', 'elderly', 'experienced', 'veteran', 'master')
            }
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
        
        logger.info("Lightweight enhanced chatbot initialized successfully!")
    
    def _build_knowledge_base(self):
        """Build a comprehensive knowledge base"""
        self.knowledge_base = {
            'craft_descriptions': {
                'pottery': 'Traditional pottery involves shaping clay into beautiful vessels, bowls, and decorative items using techniques passed down through generations. Blue pottery from Rajasthan and black pottery from Manipur are famous varieties.',
                'weaving': 'Handloom weaving creates intricate textiles using traditional looms. Banarasi silk weaves, Assamese silk, and cotton handlooms produce everything from sarees to carpets.',
                'painting': 'Traditional Indian painting includes Madhubani from Bihar, Warli from Maharashtra, Pattachitra from Odisha, and Tanjore painting from Tamil Nadu, each with unique cultural significance.',
                'carving': 'Wood and stone carving creates intricate sculptures, decorative items, and architectural elements. Sandalwood carving from Karnataka is particularly renowned.',
                'embroidery': 'Traditional embroidery like Chikankari from Uttar Pradesh, Phulkari from Punjab, and Kutch embroidery from Gujarat adds beautiful patterns to fabrics.',
                'metalwork': 'Includes Bidriware from Karnataka, Dokra bell metal work, and silver filigree work, creating decorative and functional items.',
                'carpet weaving': 'Hand-knotted carpets and durries are woven using traditional techniques, particularly famous in Kashmir, Rajasthan, and Uttar Pradesh.',
                'jewelry': 'Traditional jewelry making includes Kundan work, silver jewelry, and tribal ornaments crafted with intricate designs.',
                'leather craft': 'Traditional leather work creates bags, shoes, and decorative items using age-old tanning and crafting techniques.',
                'bamboo': 'Bamboo and cane craft creates baskets, furniture, and decorative items, particularly prevalent in northeastern states.'
            },
            'regional_specialties': {
                'gujarat': ['bandhani tie-dye', 'block printing', 'pottery', 'embroidery', 'metalwork'],
                'rajasthan': ['blue pottery', 'stone carving', 'carpet weaving', 'painting', 'jewelry'],
                'west bengal': ['handloom weaving', 'dokra bell metal', 'terracotta', 'silk weaving'],
                'uttar pradesh': ['chikankari embroidery', 'carpet weaving', 'brass work', 'zardozi'],
                'tamil nadu': ['tanjore painting', 'bronze work', 'silk weaving', 'stone carving'],
                'karnataka': ['sandalwood carving', 'bidriware', 'silk weaving', 'channapatna toys'],
                'odisha': ['pattachitra painting', 'silver filigree', 'handloom weaving', 'stone carving'],
                'bihar': ['madhubani painting', 'sikki grass work', 'handloom weaving'],
                'punjab': ['phulkari embroidery', 'punjabi juttis', 'handicrafts'],
                'kerala': ['coir craft', 'metal work', 'handloom weaving', 'wood carving'],
                'maharashtra': ['warli painting', 'handloom weaving', 'metalwork'],
                'assam': ['silk weaving', 'bamboo craft', 'handloom weaving'],
                'himachal pradesh': ['wood carving', 'metalwork', 'handloom weaving'],
                'haryana': ['handloom weaving', 'pottery', 'metalwork'],
                'madhya pradesh': ['handloom weaving', 'metalwork', 'stone carving']
            }
        }
    
    def _load_response_templates(self):
        """Load response templates for different scenarios"""
        return {
            'greeting': [
                "🙏 **Welcome to Kala-Kaart!** I'm your AI assistant for discovering India's traditional artisans and their beautiful crafts.",
                "**Namaste!** I'm here to help you find skilled artisans and learn about India's rich craft heritage.",
                "**Hello!** Welcome to the world of traditional Indian crafts. How can I help you connect with talented artisans today?"
            ],
            'craft_found': [
                "🎨 **Found {count} talented {craft} artists!** Here are some skilled artisans who specialize in this beautiful craft:",
                "✨ **Excellent! I located {count} {craft} experts** from our database. These artisans carry forward ancient traditions:",
                "🎯 **Perfect match! Here are {count} skilled {craft} artists** who create stunning traditional pieces:"
            ],
            'location_found': [
                "📍 **Discovered {count} talented artists in {location}!** This region has a rich craft tradition:",
                "🌟 **{location} has {count} skilled artisans** in our database. Here are some featured artists:",
                "🎨 **Found {count} creative artists from {location}** who practice various traditional crafts:"
            ],
            'combined_found': [
                "🎯 **Perfect combination! Found {count} {craft} artists in {location}.** This region is known for exceptional {craft} work:",
                "✨ **Excellent match! Here are {count} skilled {craft} artisans from {location}** who continue this beautiful tradition:",
                "🏆 **Outstanding! Located {count} {craft} masters in {location}** - a region renowned for this craft:"
            ],
            'no_results': [
                "❌ **No artists found** matching your specific criteria. Let me suggest some alternatives or try broadening your search.",
                "🔍 **No exact matches** found. Would you like me to suggest similar crafts or artists from nearby regions?",
                "❌ **No results** with those specifications. Let me help you explore related crafts or locations."
            ],
            'statistics': [
                "📊 **Kala-Kaart Database Overview:**\n\n🎨 **Total Artists:** {total:,} verified artisans\n🏛️ **Geographic Coverage:** {states} states across India\n🎭 **Craft Diversity:** {crafts} traditional craft forms\n👥 **Age Demographic:** {age_min}-{age_max} years (average: {age_mean:.1f} years)",
                "📈 **Database Statistics:**\n\n• **{total:,} talented artists** preserving India's craft heritage\n• **{states} states** represented in our network\n• **{crafts} unique craft forms** from ancient to contemporary\n• **Age range:** {age_min}-{age_max} years",
                "🌟 **Our Artisan Network:**\n\n✨ **{total:,} verified craftspeople** across India\n🗺️ **{states} states** with active artisan communities\n🎨 **{crafts} traditional crafts** being practiced today\n📊 **Artisan ages:** {age_min} to {age_max} years"
            ],
            'contact_info': [
                "📞 **Contact Information Available!** \n\nAll our verified artisans have complete contact details including:\n• 📱 Phone numbers\n• 📧 Email addresses\n• 📍 Location details\n\nSimply search for specific artists to access their contact information!",
                "💬 **Get in Touch with Artisans!**\n\nOur database includes verified contact details for all artists:\n• Direct phone numbers\n• Email addresses\n• Physical addresses\n\nSearch by craft or location to find and contact artisans directly!",
                "🤝 **Connect with Traditional Artists!**\n\nEvery artist profile includes:\n• Verified phone numbers\n• Professional email addresses\n• Location and workshop details\n\nUse our search to find artists and get their contact information instantly!"
            ],
            'help': [
                "🆘 **How I Can Help You:**\n\n🎨 **Find Artists:** Search by craft type (e.g., 'pottery artists')\n📍 **By Location:** Find artisans by state or city\n🔍 **Combined Search:** 'Pottery artists in Gujarat'\n📊 **Statistics:** Get database overview and insights\n📞 **Contact Info:** Access verified artisan contact details\n\n**Try asking:** 'Show me Madhubani painters' or 'Artists in Rajasthan'",
                "💡 **I'm here to help you discover traditional Indian artisans!**\n\n**You can ask me about:**\n• Specific crafts (pottery, weaving, painting, etc.)\n• Artists by location (state, city, region)\n• Contact information for artisans\n• Database statistics and insights\n• Traditional craft knowledge\n\n**Example queries:** 'Find wood carvers in Kerala' or 'Show me embroidery artists'",
                "🌟 **Your Guide to Traditional Indian Crafts!**\n\n**I can help you:**\n• Search {total} verified artisans across India\n• Find specialists in {crafts}+ traditional crafts\n• Connect you with artists in {states} states\n• Provide contact details and craft knowledge\n• Share insights about regional specialties\n\n**Just ask naturally!** Try 'pottery artists in Rajasthan' or 'contact information for weavers'"
            ]
        }
    
    def detect_language(self, text: str) -> str:
        """Enhanced language detection using character patterns and common words"""
        # Check for Devanagari script (Hindi)
        if re.search(r'[\u0900-\u097F]', text):
            return 'hindi'
        # Check for Tamil script
        elif re.search(r'[\u0B80-\u0BFF]', text):
            return 'tamil'
        # Check for Telugu script
        elif re.search(r'[\u0C00-\u0C7F]', text):
            return 'telugu'
        # Check for common Hindi words in Roman script
        elif any(word in text.lower() for word in ['namaste', 'namaskar', 'kaise', 'kaun', 'kya', 'kahan']):
            return 'hindi'
        else:
            return 'english'
    
    def classify_intent(self, user_message: str) -> str:
        """Enhanced intent classification using pattern matching with confidence scoring"""
        user_message_lower = user_message.lower()
        intent_scores = {}
        
        # Score each intent based on pattern matches
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, user_message_lower, re.IGNORECASE)
                if matches:
                    score += len(matches) + (1 if re.search(pattern, user_message_lower, re.IGNORECASE) else 0)
            
            if score > 0:
                intent_scores[intent] = score
        
        # Return highest scoring intent, or general_query if no matches
        if intent_scores:
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        
        return 'general_query'
    
    def extract_entities(self, user_message: str) -> Dict[str, Any]:
        """Enhanced entity extraction with fuzzy matching"""
        entities = {}
        user_message_lower = user_message.lower()
        
        # Extract states with fuzzy matching
        for state in self.entity_patterns['states']:
            if state in user_message_lower:
                entities['state'] = state.title()
                break
            # Fuzzy matching for common abbreviations
            elif state == 'uttar pradesh' and ('up' in user_message_lower.split() or 'u.p.' in user_message_lower):
                entities['state'] = 'Uttar Pradesh'
                break
            elif state == 'himachal pradesh' and ('hp' in user_message_lower.split() or 'h.p.' in user_message_lower):
                entities['state'] = 'Himachal Pradesh'
                break
            elif state == 'madhya pradesh' and ('mp' in user_message_lower.split() or 'm.p.' in user_message_lower):
                entities['state'] = 'Madhya Pradesh'
                break
        
        # Extract crafts with fuzzy matching
        craft_found = False
        for craft in self.entity_patterns['crafts']:
            if craft in user_message_lower:
                entities['craft'] = craft.title()
                craft_found = True
                break
            # Handle variations
            elif craft == 'pottery' and any(word in user_message_lower for word in ['potter', 'clay', 'ceramic']):
                entities['craft'] = 'Pottery'
                craft_found = True
                break
            elif craft == 'weaving' and any(word in user_message_lower for word in ['weaver', 'loom', 'textile']):
                entities['craft'] = 'Weaving'
                craft_found = True
                break
            elif craft == 'painting' and any(word in user_message_lower for word in ['painter', 'paint']):
                entities['craft'] = 'Painting'
                craft_found = True
                break
        
        # Extract age-related entities
        for age_type, keywords in self.entity_patterns['age_descriptors'].items():
            if any(keyword in user_message_lower for keyword in keywords):
                if age_type == 'young':
                    entities['age_max'] = 35
                    entities['age_description'] = 'young'
                elif age_type == 'senior':
                    entities['age_min'] = 50
                    entities['age_description'] = 'senior'
                break
        
        # Extract gender
        if any(word in user_message_lower for word in ['male', 'men', 'man']):
            entities['gender'] = 'Male'
        elif any(word in user_message_lower for word in ['female', 'women', 'woman']):
            entities['gender'] = 'Female'
        
        # Extract numbers for specific queries
        numbers = re.findall(r'\b(\d+)\b', user_message)
        if numbers:
            entities['numbers'] = [int(n) for n in numbers]
        
        return entities
    
    def semantic_search(self, query: str, entities: Dict[str, Any], limit: int = 5) -> List[Dict]:
        """Enhanced semantic search with scoring"""
        search_filters = {}
        
        # Map entities to search filters
        if 'state' in entities:
            search_filters['state'] = entities['state']
        if 'craft' in entities:
            # Handle craft variations
            craft = entities['craft'].lower()
            # Map common variations
            craft_mappings = {
                'pottery': ['pottery', 'blue pottery', 'black pottery'],
                'weaving': ['weaving', 'handloom weaving', 'banarasi weaving', 'durrie weaving'],
                'painting': ['painting', 'madhubani painting', 'warli painting', 'tanjore painting', 'pattachitra'],
                'embroidery': ['embroidery', 'chikankari', 'phulkari', 'kutch embroidery'],
                'carving': ['carving', 'wood carving', 'stone carving', 'sandalwood carving'],
                'metalwork': ['metalwork', 'bidriware', 'dokra', 'silver filigree'],
                'jewelry': ['jewelry', 'kundan jewellery'],
                'textile': ['textile', 'handloom weaving', 'weaving'],
                'handicraft': ['handicraft', 'bamboo', 'cane', 'jute craft', 'coir craft']
            }
            
            # Use exact match first, then try variations
            search_filters['craft_type'] = entities['craft']
        
        if 'age_min' in entities:
            search_filters['age_min'] = entities['age_min']
        if 'age_max' in entities:
            search_filters['age_max'] = entities['age_max']
        
        # Perform search
        if search_filters:
            results = self.data_processor.search_artists(search_filters)
            return results[:limit]
        
        # Fallback to similarity search
        results = self.data_processor.find_similar_artists(query, limit)
        return results
    
    def generate_contextual_response(self, intent: str, entities: Dict[str, Any], 
                                   artists: List[Dict], stats: Dict) -> Dict[str, Any]:
        """Generate comprehensive contextual response"""
        
        if intent == 'greeting':
            import random
            message = random.choice(self.response_templates['greeting'])
            message += f"\n\n📊 **Current Database:** {stats.get('total_artists', 0):,} verified artisans across India!"
            
            # Add personalized suggestions based on time or random selection
            suggestions = [
                "Show me pottery artists",
                "Find artists in Gujarat", 
                "Tell me about Rajasthani crafts",
                "Database statistics",
                "Popular traditional crafts",
                "Artists practicing Madhubani painting"
            ]
        
        elif intent == 'help':
            import random
            template = random.choice(self.response_templates['help'])
            message = template.format(
                total=stats.get('total_artists', 0),
                crafts=stats.get('unique_crafts', 0),
                states=stats.get('unique_states', 0)
            )
            
            suggestions = [
                "Show me pottery artists",
                "Find artists in Rajasthan",
                "Database statistics",
                "Artists practicing weaving",
                "Traditional crafts by region"
            ]
        
        elif intent == 'get_statistics':
            import random
            template = random.choice(self.response_templates['statistics'])
            age_dist = stats.get('age_distribution', {})
            message = template.format(
                total=stats.get('total_artists', 0),
                states=stats.get('unique_states', 0),
                crafts=stats.get('unique_crafts', 0),
                age_min=age_dist.get('min', 18),
                age_max=age_dist.get('max', 70),
                age_mean=age_dist.get('mean', 37.5)
            )
            
            # Add popular crafts and states
            popular_crafts = stats.get('crafts', [])[:8]
            popular_states = stats.get('states', [])[:10]
            
            message += f"\n\n🎨 **Popular Crafts:** {', '.join(popular_crafts)}"
            message += f"\n🏛️ **Active States:** {', '.join(popular_states)}"
            
            suggestions = ["Find pottery artists", "Show artists by state", "Explore craft types", "Regional specialties"]
        
        elif intent == 'get_contact':
            import random
            message = random.choice(self.response_templates['contact_info'])
            
            suggestions = ["Find pottery artists", "Search by location", "Browse featured artists", "Show popular crafts"]
        
        elif artists:
            # Determine response type based on entities
            import random
            
            if 'state' in entities and 'craft' in entities:
                template = random.choice(self.response_templates['combined_found'])
                message = template.format(
                    count=len(artists),
                    craft=entities['craft'],
                    location=entities['state']
                )
                
                # Add regional knowledge
                state_lower = entities['state'].lower()
                if state_lower in self.knowledge_base['regional_specialties']:
                    specialties = self.knowledge_base['regional_specialties'][state_lower]
                    message += f"\n\n🌟 **{entities['state']} is renowned for:** {', '.join(specialties[:4])}"
                
            elif 'craft' in entities:
                template = random.choice(self.response_templates['craft_found'])
                message = template.format(count=len(artists), craft=entities['craft'])
                
                # Add craft knowledge
                craft_lower = entities['craft'].lower()
                if craft_lower in self.knowledge_base['craft_descriptions']:
                    message += f"\n\n💡 **About {entities['craft']}:** {self.knowledge_base['craft_descriptions'][craft_lower]}"
                
            elif 'state' in entities:
                template = random.choice(self.response_templates['location_found'])
                message = template.format(count=len(artists), location=entities['state'])
                
                # Add regional information
                state_lower = entities['state'].lower()
                if state_lower in self.knowledge_base['regional_specialties']:
                    specialties = self.knowledge_base['regional_specialties'][state_lower]
                    message += f"\n\n🎨 **Traditional crafts of {entities['state']}:** {', '.join(specialties)}"
            
            else:
                message = f"🎨 **Found {len(artists)} talented artists** matching your query! Here are some skilled artisans:"
            
            # Generate contextual suggestions
            suggestions = []
            if 'craft' in entities:
                suggestions.extend([
                    f"More {entities['craft']} artists",
                    f"Contact {entities['craft']} artists",
                    f"{entities['craft']} in different states"
                ])
            if 'state' in entities:
                suggestions.extend([
                    f"All crafts in {entities['state']}",
                    f"Contact artists in {entities['state']}"
                ])
            
            # Add general suggestions
            suggestions.extend(["Get contact information", "Find similar artists", "Browse more artists"])
        
        else:
            import random
            message = random.choice(self.response_templates['no_results'])
            
            # Suggest alternatives based on entities
            alternatives = []
            if 'craft' in entities:
                # Suggest similar crafts
                craft_lower = entities['craft'].lower()
                similar_crafts = {
                    'pottery': ['blue pottery', 'black pottery', 'terracotta'],
                    'weaving': ['handloom weaving', 'banarasi weaving', 'durrie weaving'],
                    'painting': ['madhubani painting', 'warli painting', 'pattachitra'],
                    'embroidery': ['chikankari', 'phulkari', 'kutch embroidery']
                }
                if craft_lower in similar_crafts:
                    alternatives.extend(similar_crafts[craft_lower][:2])
                alternatives.append(f"All {entities['craft']} artists")
            
            if 'state' in entities:
                alternatives.append(f"All crafts in {entities['state']}")
                alternatives.append("Browse nearby states")
            
            if not alternatives:
                alternatives = ["Browse all crafts", "Find by popular locations", "Explore featured artists"]
            
            message += f"\n\n💡 **Try instead:**\n" + "\n".join([f"• {alt}" for alt in alternatives[:3]])
            
            suggestions = alternatives + ["Browse popular artists", "Database overview"]
        
        return {
            "message": message,
            "artists": self.transform_artists_for_frontend(artists),
            "suggestions": suggestions[:6],  # Limit to 6 suggestions
            "context": {
                "intent": intent,
                "entities": entities,
                "language": self.detect_language(entities.get('original_query', ''))
            }
        }
    
    def transform_artists_for_frontend(self, artists: List[Dict]) -> List[Dict]:
        """Transform artist data to match frontend expectations"""
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
                        "phone_available": str(artist.get("contact_phone_boolean", "")).lower() == "yes"
                    },
                    "languages": artist.get("languages_spoken", "").split(", ") if artist.get("languages_spoken") else [],
                    "age": artist.get("age", 0),
                    "gender": artist.get("gender", ""),
                    "government_id": artist.get("govt_artisan_id", ""),
                    "cluster_code": artist.get("artisan_cluster_code", "")
                }
                
                # Add similarity score if available
                if 'similarity_score' in artist:
                    transformed_artist['similarity_score'] = artist['similarity_score']
                
                transformed_artists.append(transformed_artist)
        
        return transformed_artists
    
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
    
    def get_contextual_suggestions(self) -> List[str]:
        """Generate contextual suggestions based on conversation history"""
        suggestions = []
        
        last_intent = self.conversation_context.get('last_intent')
        last_entities = self.conversation_context.get('last_entities', {})
        
        if last_intent == 'find_by_craft' and 'craft' in last_entities:
            craft = last_entities['craft']
            suggestions.extend([
                f"More {craft} artists",
                f"Contact {craft} artists",
                f"{craft} artists in different states"
            ])
        elif last_intent == 'find_by_location' and 'state' in last_entities:
            state = last_entities['state']
            suggestions.extend([
                f"All crafts in {state}",
                f"Traditional specialties of {state}",
                f"Contact artists in {state}"
            ])
        
        # Add general suggestions
        base_suggestions = [
            "Show me pottery artists",
            "Find artists in Rajasthan",
            "Database statistics",
            "Popular traditional crafts",
            "Artists practicing Madhubani painting",
            "Wood carvers in Kerala"
        ]
        
        suggestions.extend(base_suggestions)
        return suggestions[:8]  # Return top 8 suggestions
    
    def process_query(self, user_message: str, conversation_history: List[str] = None) -> Dict[str, Any]:
        """Main query processing pipeline with comprehensive AI capabilities"""
        try:
            logger.info(f"Processing query: {user_message}")
            
            # Detect language
            language = self.detect_language(user_message)
            
            # Classify intent with confidence
            intent = self.classify_intent(user_message)
            
            # Extract entities with enhanced matching
            entities = self.extract_entities(user_message)
            entities['original_query'] = user_message
            entities['language'] = language
            
            # Get database statistics
            stats = self.data_processor.get_stats()
            
            # Perform semantic search if needed
            artists = []
            if intent in ['find_by_craft', 'find_by_location', 'general_query'] and (entities or 'find' in user_message.lower() or 'show' in user_message.lower()):
                artists = self.semantic_search(user_message, entities, limit=5)
            
            # Generate comprehensive response
            response = self.generate_contextual_response(intent, entities, artists, stats)
            
            # Update conversation context
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
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                "intent": "error",
                "entities": {},
                "message": "❌ I encountered an error processing your request. Please try rephrasing your question or try a different query.",
                "llm_message": None,
                "artists": [],
                "suggestions": self.get_contextual_suggestions(),
                "stats": self.data_processor.get_stats() if self.data_processor else {},
                "context": {"error": str(e), "language": "english"}
            }


# Alias for compatibility
EnhancedKalaKaartChatbot = LightweightEnhancedChatbot