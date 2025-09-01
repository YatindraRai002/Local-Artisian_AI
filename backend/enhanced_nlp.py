"""
Enhanced NLP capabilities for better chatbot performance
Includes advanced entity extraction, sentiment analysis, and query understanding
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class AdvancedNLPProcessor:
    """Advanced NLP processing for better query understanding"""
    
    def __init__(self):
        self.synonyms = self._load_synonyms()
        self.craft_aliases = self._load_craft_aliases()
        self.location_aliases = self._load_location_aliases()
        self.sentiment_words = self._load_sentiment_words()
        
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """Load synonyms for better entity matching"""
        return {
            'find': ['search', 'locate', 'discover', 'show', 'get', 'list', 'display', 'browse'],
            'artist': ['artisan', 'craftsman', 'craftspeople', 'maker', 'creator', 'craftsperson'],
            'contact': ['phone', 'call', 'reach', 'number', 'telephone', 'mobile', 'email'],
            'good': ['excellent', 'great', 'amazing', 'wonderful', 'fantastic', 'outstanding'],
            'bad': ['poor', 'terrible', 'awful', 'horrible', 'disappointing']
        }
    
    def _load_craft_aliases(self) -> Dict[str, List[str]]:
        """Load craft type aliases and variations"""
        return {
            'pottery': ['potter', 'ceramic', 'clay work', 'earthenware', 'blue pottery', 'black pottery'],
            'weaving': ['weaver', 'loom', 'textile', 'fabric', 'handloom', 'banarasi', 'silk'],
            'painting': ['painter', 'art', 'madhubani', 'warli', 'pattachitra', 'tanjore', 'miniature'],
            'embroidery': ['chikankari', 'phulkari', 'kutch work', 'zardozi', 'needlework'],
            'carving': ['sculptor', 'wood carving', 'stone carving', 'sandalwood', 'ivory'],
            'metalwork': ['blacksmith', 'bidriware', 'dokra', 'brass work', 'copper work'],
            'jewelry': ['jeweller', 'kundan', 'silver work', 'gold work', 'ornaments'],
            'leather': ['leather craft', 'tanning', 'footwear', 'bags'],
            'bamboo': ['bamboo craft', 'cane work', 'basket making', 'furniture']
        }
    
    def _load_location_aliases(self) -> Dict[str, List[str]]:
        """Load location aliases and common abbreviations"""
        return {
            'uttar pradesh': ['up', 'u.p.', 'uttar', 'pradesh'],
            'madhya pradesh': ['mp', 'm.p.', 'madhya', 'central india'],
            'himachal pradesh': ['hp', 'h.p.', 'himachal'],
            'andhra pradesh': ['ap', 'a.p.', 'andhra'],
            'tamil nadu': ['tn', 't.n.', 'tamil', 'tamilnadu'],
            'west bengal': ['wb', 'w.b.', 'bengal', 'paschim banga'],
            'rajasthan': ['rajasthan', 'desert state', 'royal state'],
            'gujarat': ['gujarat', 'gujrat', 'land of gandhi'],
            'maharashtra': ['maharashtra', 'maha', 'bombay state'],
            'karnataka': ['karnataka', 'mysore state', 'kannada state'],
            'kerala': ['kerala', 'gods own country', 'spice coast'],
            'punjab': ['punjab', 'land of five rivers', 'sikh state']
        }
    
    def _load_sentiment_words(self) -> Dict[str, List[str]]:
        """Load sentiment analysis words"""
        return {
            'positive': ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like', 'best'],
            'negative': ['bad', 'terrible', 'awful', 'hate', 'dislike', 'worst', 'poor', 'disappointing'],
            'neutral': ['okay', 'fine', 'normal', 'average', 'standard']
        }
    
    def expand_query(self, query: str) -> str:
        """Expand query with synonyms for better matching"""
        expanded_terms = []
        words = query.lower().split()
        
        for word in words:
            expanded_terms.append(word)
            # Add synonyms
            for key, synonyms in self.synonyms.items():
                if word == key or word in synonyms:
                    expanded_terms.extend([s for s in synonyms if s != word])
        
        return ' '.join(set(expanded_terms))
    
    def extract_advanced_entities(self, query: str) -> Dict[str, Any]:
        """Advanced entity extraction with fuzzy matching"""
        entities = {}
        query_lower = query.lower()
        
        # Extract craft types with aliases
        for craft, aliases in self.craft_aliases.items():
            if craft in query_lower or any(alias in query_lower for alias in aliases):
                entities['craft'] = craft.title()
                entities['craft_confidence'] = 0.9 if craft in query_lower else 0.7
                break
        
        # Extract locations with aliases
        for location, aliases in self.location_aliases.items():
            if location in query_lower or any(alias in query_lower for alias in aliases):
                entities['state'] = location.title()
                entities['state_confidence'] = 0.9 if location in query_lower else 0.7
                break
        
        # Extract sentiment
        sentiment_scores = {'positive': 0, 'negative': 0, 'neutral': 0}
        for sentiment, words in self.sentiment_words.items():
            for word in words:
                if word in query_lower:
                    sentiment_scores[sentiment] += 1
        
        if max(sentiment_scores.values()) > 0:
            entities['sentiment'] = max(sentiment_scores, key=sentiment_scores.get)
        
        # Extract numbers and quantities
        numbers = re.findall(r'\b(\d+)\b', query)
        if numbers:
            entities['quantities'] = [int(n) for n in numbers]
        
        # Extract quality descriptors
        quality_words = {
            'high_quality': ['best', 'top', 'premium', 'high quality', 'excellent', 'master'],
            'affordable': ['cheap', 'affordable', 'budget', 'low cost', 'inexpensive'],
            'traditional': ['traditional', 'authentic', 'classic', 'ancient', 'heritage'],
            'modern': ['modern', 'contemporary', 'new', 'innovative', 'latest']
        }
        
        for quality, words in quality_words.items():
            if any(word in query_lower for word in words):
                entities['quality_preference'] = quality
                break
        
        return entities
    
    def get_query_intent_confidence(self, query: str, intent_patterns: Dict[str, List[str]]) -> Dict[str, float]:
        """Get confidence scores for different intents"""
        query_lower = query.lower()
        expanded_query = self.expand_query(query)
        
        confidence_scores = {}
        
        for intent, patterns in intent_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                # Direct pattern match
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += 2.0
                    matches += 1
                
                # Expanded query match
                if re.search(pattern, expanded_query, re.IGNORECASE):
                    score += 1.0
                    matches += 1
            
            # Normalize score
            if matches > 0:
                confidence_scores[intent] = min(score / len(patterns), 1.0)
        
        return confidence_scores
    
    def suggest_query_improvements(self, query: str, results_count: int = 0) -> List[str]:
        """Suggest improvements for queries that don't return good results"""
        suggestions = []
        query_lower = query.lower()
        
        if results_count == 0:
            # Suggest broader searches
            if any(craft in query_lower for craft in self.craft_aliases.keys()):
                suggestions.append("Try searching without location filters")
                suggestions.append("Search for similar crafts")
            
            if any(location in query_lower for location in self.location_aliases.keys()):
                suggestions.append("Try searching in nearby states")
                suggestions.append("Search for all crafts in this region")
            
            suggestions.extend([
                "Use more general terms",
                "Check spelling of craft or location names",
                "Try asking for popular artists or crafts"
            ])
        
        elif results_count < 3:
            suggestions.extend([
                "Broaden your search criteria",
                "Try related craft types",
                "Search in nearby regions"
            ])
        
        return suggestions[:3]
    
    def analyze_user_preferences(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Analyze user preferences from conversation history"""
        preferences = {
            'preferred_crafts': [],
            'preferred_locations': [],
            'interaction_style': 'neutral',
            'detail_level': 'medium'
        }
        
        if not conversation_history:
            return preferences
        
        # Extract frequently mentioned crafts
        craft_mentions = Counter()
        location_mentions = Counter()
        
        for interaction in conversation_history[-5:]:  # Last 5 interactions
            entities = interaction.get('entities', {})
            if 'craft' in entities:
                craft_mentions[entities['craft'].lower()] += 1
            if 'state' in entities:
                location_mentions[entities['state'].lower()] += 1
        
        preferences['preferred_crafts'] = [craft for craft, count in craft_mentions.most_common(3)]
        preferences['preferred_locations'] = [loc for loc, count in location_mentions.most_common(3)]
        
        return preferences


class SmartResponseGenerator:
    """Generate contextually appropriate responses"""
    
    def __init__(self):
        self.response_styles = {
            'formal': {
                'greeting': "Good day! I'm here to assist you with finding traditional Indian artisans.",
                'closing': "I hope this information is helpful. Please let me know if you need anything else."
            },
            'friendly': {
                'greeting': "Hey there! 👋 Ready to discover some amazing traditional artists?",
                'closing': "Hope that helps! Feel free to ask me anything else about our artisans! 😊"
            },
            'professional': {
                'greeting': "Welcome to Kala-Kaart. I can help you connect with skilled traditional artisans.",
                'closing': "Thank you for using our platform. Don't hesitate to reach out for more information."
            }
        }
    
    def personalize_response(self, base_response: str, user_preferences: Dict[str, Any], 
                           conversation_context: Dict[str, Any]) -> str:
        """Personalize response based on user preferences and context"""
        
        # Adjust formality based on conversation style
        style = user_preferences.get('interaction_style', 'friendly')
        
        if style == 'formal':
            # Make response more formal
            base_response = base_response.replace("Hey!", "Hello")
            base_response = base_response.replace("😊", "")
            base_response = base_response.replace("🎨", "")
        
        # Add personal touches based on preferences
        if user_preferences.get('preferred_crafts'):
            preferred_craft = user_preferences['preferred_crafts'][0]
            if f"interested in {preferred_craft}" not in base_response:
                base_response += f"\n\n💡 Since you seem interested in {preferred_craft}, you might also like similar traditional crafts!"
        
        return base_response
    
    def generate_contextual_suggestions(self, current_entities: Dict[str, Any], 
                                      user_preferences: Dict[str, Any],
                                      database_stats: Dict[str, Any]) -> List[str]:
        """Generate smart, contextual suggestions"""
        suggestions = []
        
        # Based on current query
        if 'craft' in current_entities:
            craft = current_entities['craft'].lower()
            suggestions.append(f"Find {craft} artists in different states")
            suggestions.append(f"Learn about {craft} techniques")
            suggestions.append(f"Contact information for {craft} artists")
        
        if 'state' in current_entities:
            state = current_entities['state']
            suggestions.append(f"All traditional crafts in {state}")
            suggestions.append(f"Master artisans in {state}")
        
        # Based on user preferences
        for craft in user_preferences.get('preferred_crafts', [])[:2]:
            suggestions.append(f"More {craft} artists")
        
        for location in user_preferences.get('preferred_locations', [])[:2]:
            suggestions.append(f"Artisans in {location}")
        
        # General popular suggestions
        popular_crafts = ['pottery', 'weaving', 'painting', 'jewelry']
        popular_states = ['rajasthan', 'gujarat', 'uttar pradesh', 'karnataka']
        
        for craft in popular_crafts[:2]:
            suggestions.append(f"Find {craft} artists")
        
        for state in popular_states[:2]:
            suggestions.append(f"Artists in {state.title()}")
        
        # Remove duplicates and return top suggestions
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:6]


class QueryOptimizer:
    """Optimize queries for better search results"""
    
    def __init__(self):
        self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
    
    def optimize_search_query(self, original_query: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize search parameters based on query analysis"""
        optimized_filters = {}
        
        # Use extracted entities for precise filtering
        if 'craft' in entities:
            optimized_filters['craft_type'] = entities['craft']
        
        if 'state' in entities:
            optimized_filters['state'] = entities['state']
        
        # Handle quality preferences
        if 'quality_preference' in entities:
            quality = entities['quality_preference']
            if quality == 'traditional':
                # Prefer older artists or specific traditional crafts
                optimized_filters['traditional_focus'] = True
            elif quality == 'modern':
                # Prefer younger artists or contemporary approaches
                optimized_filters['age_max'] = 40
        
        # Handle sentiment-based filtering
        if 'sentiment' in entities:
            if entities['sentiment'] == 'positive':
                # User seems enthusiastic, show featured or top-rated artists
                optimized_filters['featured'] = True
        
        return optimized_filters
    
    def suggest_alternative_searches(self, failed_query: str, entities: Dict[str, Any]) -> List[str]:
        """Suggest alternative search strategies when original query fails"""
        alternatives = []
        
        if 'craft' in entities and 'state' in entities:
            # If specific craft + location failed, try broader approaches
            alternatives.append(f"All {entities['craft']} artists (any location)")
            alternatives.append(f"All crafts in {entities['state']}")
            alternatives.append("Popular artists nationwide")
        
        elif 'craft' in entities:
            alternatives.append(f"Artists practicing similar crafts to {entities['craft']}")
            alternatives.append("Browse all craft types")
        
        elif 'state' in entities:
            alternatives.append(f"Artists in states near {entities['state']}")
            alternatives.append("Browse by popular craft types")
        
        alternatives.append("Featured artists across India")
        alternatives.append("Recently added artists")
        
        return alternatives[:4]