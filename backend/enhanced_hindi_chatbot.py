"""
Enhanced Chatbot with Hindi NLP Support
Integrates the Hindi NLP model with existing artisan search functionality
"""

import json
import csv
import os
from typing import List, Dict, Any, Optional
from hindi_nlp_model import HindiNLPModel, ProcessedQuery

class EnhancedHindiChatbot:
    """Advanced chatbot with Hindi language support"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.artisans_data = []
        self.hindi_nlp = HindiNLPModel()
        self.conversation_history = []
        
        # Load artisan data
        self.load_artisans_data()
        
        # Hindi response templates
        self.hindi_responses = {
            'greeting': [
                "नमस्ते! मैं आपकी पारंपरिक कारीगरों की खोज में मदद कर सकूं हूँ।",
                "नमस्कार! आप किस प्रकार के शिल्पकार की तलाश में हैं?",
                "आपका स्वागत है! मैं भारतीय हस्तशिल्प कारीगरों के बारे में जानकारी दे सकता हूँ।"
            ],
            'found_artisans': "मुझे {count} {craft_type} कारीगर मिले हैं {location} में।",
            'no_artisans': "क्षमा करें, {criteria} के लिए कोई कारीगर नहीं मिला।",
            'craft_info': "{craft_type} एक पारंपरिक भारतीय कला है जो {region} में प्रसिद्ध है।",
            'help': "आप मुझसे कारीगरों के बारे में हिंदी या अंग्रेजी में पूछ सकते हैं। जैसे: 'कुम्हारी कारीगर दिखाओ' या 'राजस्थान में शिल्पकार'",
            'error': "क्षमा करें, मुझे आपका प्रश्न समझने में कोई समस्या हुई है। कृपया दोबारा पूछें।"
        }
        
        # Enhanced craft information in Hindi
        self.craft_info_hindi = {
            'pottery': {
                'name': 'कुम्हारी/मिट्टी के बर्तन',
                'description': 'मिट्टी से बने पारंपरिक बर्तन और कलाकृतियाँ',
                'regions': ['राजस्थान', 'गुजरात', 'उत्तर प्रदेश', 'हरियाणा']
            },
            'embroidery': {
                'name': 'कढ़ाई',
                'description': 'सुंदर सुई-धागे से किया गया काम',
                'regions': ['कश्मीर', 'राजस्थान', 'गुजरात', 'पंजाब']
            },
            'chikankari': {
                'name': 'चिकनकारी',
                'description': 'लखनऊ की प्रसिद्ध सफेद कढ़ाई',
                'regions': ['उत्तर प्रदेश', 'लखनऊ']
            },
            'carpet weaving': {
                'name': 'कालीन बुनाई',
                'description': 'हाथ से बुने गए सुंदर कालीन',
                'regions': ['कश्मीर', 'राजस्थान', 'उत्तर प्रदेश']
            },
            'handloom': {
                'name': 'हथकरघा',
                'description': 'पारंपरिक करघे पर बुने गए कपड़े',
                'regions': ['पश्चिम बंगाल', 'तमिलनाडु', 'केरल', 'असम']
            },
            'jewelry': {
                'name': 'आभूषण',
                'description': 'हाथ से बने पारंपरिक गहने',
                'regions': ['राजस्थान', 'गुजरात', 'आंध्र प्रदेश']
            }
        }
    
    def load_artisans_data(self):
        """Load artisan data from CSV file"""
        if not os.path.exists(self.csv_path):
            print(f"CSV file not found: {self.csv_path}")
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    artisan = {
                        'id': row.get('artisan_id', ''),
                        'name': row.get('name', ''),
                        'gender': row.get('gender', ''),
                        'age': int(row.get('age', 0)) if row.get('age', '').isdigit() else 0,
                        'craft_type': row.get('craft_type', '').lower(),
                        'location': {
                            'state': row.get('state', ''),
                            'district': row.get('district', ''),
                            'village': row.get('village', '')
                        },
                        'languages': row.get('languages_spoken', '').split(', ') if row.get('languages_spoken') else [],
                        'contact': {
                            'email': row.get('contact_email', ''),
                            'phone': row.get('contact_phone', ''),
                            'phone_available': row.get('contact_phone_boolean', '').lower() == 'yes'
                        },
                        'government_id': row.get('govt_artisan_id', ''),
                        'cluster_code': row.get('artisan_cluster_code', '')
                    }
                    self.artisans_data.append(artisan)
            
            print(f"Loaded {len(self.artisans_data)} artisans from CSV")
        except Exception as e:
            print(f"Error loading CSV: {e}")
    
    def search_artisans(self, filters: Dict[str, Any]) -> List[Dict]:
        """Search artisans based on filters"""
        filtered_artisans = self.artisans_data.copy()
        
        if 'craft_type' in filters and filters['craft_type']:
            craft_filter = filters['craft_type'].lower()
            filtered_artisans = [a for a in filtered_artisans 
                               if craft_filter in a['craft_type'].lower()]
        
        if 'state' in filters and filters['state']:
            state_filter = filters['state'].lower()
            filtered_artisans = [a for a in filtered_artisans 
                               if state_filter in a['location']['state'].lower()]
        
        if 'district' in filters and filters['district']:
            district_filter = filters['district'].lower()
            filtered_artisans = [a for a in filtered_artisans 
                               if district_filter in a['location']['district'].lower()]
        
        if 'language' in filters and filters['language']:
            lang_filter = filters['language'].lower()
            filtered_artisans = [a for a in filtered_artisans 
                               if any(lang_filter in lang.lower() for lang in a['languages'])]
        
        # Limit results
        limit = filters.get('limit', 10)
        return filtered_artisans[:limit]
    
    def generate_hindi_response(self, processed_query: ProcessedQuery, artisans: List[Dict]) -> Dict[str, Any]:
        """Generate response in Hindi based on processed query"""
        intent = processed_query.intent
        entities = processed_query.entities
        
        if intent == 'search_artisan' or intent == 'search_craft':
            if artisans:
                craft_type = entities.get('craft_type', 'कारीगर')
                location = entities.get('location', '')
                location_text = f" {location} में" if location else ""
                
                if craft_type in self.craft_info_hindi:
                    craft_name = self.craft_info_hindi[craft_type]['name']
                else:
                    craft_name = craft_type
                
                message = self.hindi_responses['found_artisans'].format(
                    count=len(artisans),
                    craft_type=craft_name,
                    location=location_text
                )
                
                # Add craft information if available
                if craft_type in self.craft_info_hindi:
                    craft_info = self.craft_info_hindi[craft_type]
                    additional_info = f"\n\n{craft_info['description']} - यह मुख्यतः {', '.join(craft_info['regions'])} में प्रसिद्ध है।"
                    message += additional_info
                
            else:
                criteria = entities.get('craft_type', 'इस मापदंड')
                message = self.hindi_responses['no_artisans'].format(criteria=criteria)
        
        elif intent == 'get_info':
            craft_type = entities.get('craft_type', '')
            if craft_type in self.craft_info_hindi:
                craft_info = self.craft_info_hindi[craft_type]
                message = self.hindi_responses['craft_info'].format(
                    craft_type=craft_info['name'],
                    region=', '.join(craft_info['regions'][:2])
                )
                message += f"\n\n{craft_info['description']}"
            else:
                message = self.hindi_responses['help']
        
        else:  # general_query
            if any(word in processed_query.original_hindi.lower() for word in ['नमस्ते', 'हैलो', 'नमस्कार']):
                message = self.hindi_responses['greeting'][0]
            else:
                message = self.hindi_responses['help']
        
        return {
            'message': message,
            'artisans': artisans,
            'intent': intent,
            'entities': entities,
            'language': 'hindi',
            'confidence': processed_query.confidence
        }
    
    def generate_english_response(self, processed_query: ProcessedQuery, artisans: List[Dict]) -> Dict[str, Any]:
        """Generate response in English"""
        intent = processed_query.intent
        entities = processed_query.entities
        
        if intent == 'search_artisan' or intent == 'search_craft':
            if artisans:
                craft_type = entities.get('craft_type', 'artisan')
                location = entities.get('location', '')
                location_text = f" in {location}" if location else ""
                
                message = f"I found {len(artisans)} {craft_type} artisans{location_text}."
                
                # Add craft information
                if craft_type in self.craft_info_hindi:
                    craft_info = self.craft_info_hindi[craft_type]
                    message += f"\n\n{craft_type.title()} is a traditional Indian craft, popular in {', '.join(craft_info['regions'][:2])}."
            else:
                criteria = entities.get('craft_type', 'the specified criteria')
                message = f"Sorry, I couldn't find any artisans matching {criteria}."
        
        elif intent == 'get_info':
            craft_type = entities.get('craft_type', '')
            if craft_type in self.craft_info_hindi:
                craft_info = self.craft_info_hindi[craft_type]
                message = f"{craft_type.title()} is a traditional Indian craft popular in {', '.join(craft_info['regions'])}."
            else:
                message = "I can help you find information about traditional Indian artisans and crafts. Try asking about pottery, embroidery, or specific regions."
        
        else:  # general_query
            message = "Hello! I can help you find traditional Indian artisans and crafts. You can ask in Hindi or English about specific crafts, locations, or artisan information."
        
        return {
            'message': message,
            'artisans': artisans,
            'intent': intent,
            'entities': entities,
            'language': 'english',
            'confidence': processed_query.confidence
        }
    
    def chat(self, user_message: str) -> Dict[str, Any]:
        """Main chat function with Hindi NLP support"""
        try:
            # Process the query using Hindi NLP model
            processed_query = self.hindi_nlp.process_query(user_message)
            
            # Extract search filters from entities
            filters = {}
            if processed_query.entities:
                if 'craft_type' in processed_query.entities:
                    filters['craft_type'] = processed_query.entities['craft_type']
                if 'location' in processed_query.entities:
                    filters['state'] = processed_query.entities['location']
            
            # Search for artisans
            artisans = []
            if processed_query.intent in ['search_artisan', 'search_craft', 'search_location']:
                artisans = self.search_artisans(filters)
            
            # Detect language and generate appropriate response
            language = self.hindi_nlp.detect_language(user_message)
            
            if language == 'hindi':
                response = self.generate_hindi_response(processed_query, artisans)
            else:
                response = self.generate_english_response(processed_query, artisans)
            
            # Add conversation to history
            self.conversation_history.append({
                'user': user_message,
                'bot': response['message'],
                'language': language,
                'intent': processed_query.intent
            })
            
            # Add suggestions
            if language == 'hindi':
                response['suggestions'] = [
                    'कुम्हारी कारीगर दिखाओ',
                    'राजस्थान में शिल्पकार',
                    'चिकनकारी के बारे में बताओ',
                    'आंकड़े दिखाओ'
                ]
            else:
                response['suggestions'] = [
                    'Show pottery artisans',
                    'Find crafts in Rajasthan',
                    'Tell me about Chikankari',
                    'Show statistics'
                ]
            
            # Add processed query information
            response.update({
                'original_query': processed_query.original_hindi,
                'translated_query': processed_query.translated_english,
                'tokens': processed_query.tokens,
                'status': 'success'
            })
            
            return response
            
        except Exception as e:
            return {
                'message': self.hindi_responses['error'] if self.hindi_nlp.detect_language(user_message) == 'hindi' 
                          else "Sorry, I encountered an error processing your request. Please try again.",
                'error': str(e),
                'status': 'error',
                'language': 'hindi' if self.hindi_nlp.detect_language(user_message) == 'hindi' else 'english'
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics in both Hindi and English"""
        total_artisans = len(self.artisans_data)
        craft_types = list(set(a['craft_type'] for a in self.artisans_data))
        states = list(set(a['location']['state'] for a in self.artisans_data))
        hindi_speakers = len([a for a in self.artisans_data if 'hindi' in [lang.lower() for lang in a['languages']]])
        
        return {
            'total_artisans': total_artisans,
            'unique_crafts': len(craft_types),
            'unique_states': len(states),
            'hindi_speakers': hindi_speakers,
            'hindi_percentage': round((hindi_speakers / total_artisans) * 100, 1) if total_artisans > 0 else 0,
            'popular_crafts': craft_types[:10],
            'message_hindi': f"हमारे डेटाबेस में {total_artisans} कारीगर हैं, जिनमें से {hindi_speakers} हिंदी बोलते हैं।",
            'message_english': f"Our database contains {total_artisans} artisans, with {hindi_speakers} Hindi speakers."
        }

# Test the enhanced chatbot
if __name__ == "__main__":
    # Test with sample CSV path (adjust as needed)
    csv_path = "../public/Artisans.csv"
    chatbot = EnhancedHindiChatbot(csv_path)
    
    test_messages = [
        "नमस्ते",
        "कुम्हारी कारीगर दिखाओ",
        "राजस्थान में शिल्पकार चाहिए",
        "चिकनकारी के बारे में बताओ",
        "show me pottery artists",
        "tell me about artisans in Gujarat"
    ]
    
    print("Enhanced Hindi Chatbot Test:")
    print("=" * 50)
    
    for message in test_messages:
        print(f"\nUser: {message}")
        response = chatbot.chat(message)
        print(f"Bot ({response.get('language', 'unknown')}): {response.get('message', 'No response')}")
        if response.get('artisans'):
            print(f"Found {len(response['artisans'])} artisans")
        print("-" * 30)