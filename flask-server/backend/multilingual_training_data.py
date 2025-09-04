"""
Multilingual Training Data Generator for Kala-Kaart Chatbot
Supports: Hindi, English, Tamil, Telugu
"""

import json
import random
from typing import Dict, List, Any

class MultilingualTrainingDataGenerator:
    def __init__(self):
        self.languages = ['hindi', 'english', 'tamil', 'telugu']
        
        # Craft-related vocabulary in different languages
        self.craft_vocabulary = {
            'english': {
                'pottery': 'pottery', 'weaving': 'weaving', 'painting': 'painting',
                'carving': 'carving', 'embroidery': 'embroidery', 'metalwork': 'metalwork',
                'textiles': 'textiles', 'handicrafts': 'handicrafts', 'artisan': 'artisan',
                'traditional': 'traditional', 'craft': 'craft', 'artist': 'artist'
            },
            'hindi': {
                'pottery': 'मिट्टी के बर्तन', 'weaving': 'बुनाई', 'painting': 'चित्रकारी',
                'carving': 'नक्काशी', 'embroidery': 'कढ़ाई', 'metalwork': 'धातु कार्य',
                'textiles': 'वस्त्र', 'handicrafts': 'हस्तशिल्प', 'artisan': 'कारीगर',
                'traditional': 'पारंपरिक', 'craft': 'शिल्प', 'artist': 'कलाकार'
            },
            'tamil': {
                'pottery': 'களிமண் பாத்திரங்கள்', 'weaving': 'நெசவு', 'painting': 'ஓவியம்',
                'carving': 'செதுக்குதல்', 'embroidery': 'எம்பிராய்டரி', 'metalwork': 'உலோக வேலை',
                'textiles': 'ஜவுளி', 'handicrafts': 'கைவினைப்பொருட்கள்', 'artisan': 'கைவினைஞர்',
                'traditional': 'பாரம்பரிய', 'craft': 'கலை', 'artist': 'கலைஞர்'
            },
            'telugu': {
                'pottery': 'మట్టి పాత్రలు', 'weaving': 'నేత', 'painting': 'చిత్రకళ',
                'carving': 'చెక్కడం', 'embroidery': 'ఎంబ్రాయిడరీ', 'metalwork': 'లోహ పని',
                'textiles': 'వస్త్రాలు', 'handicrafts': 'చేతిపనులు', 'artisan': 'కళాకారుడు',
                'traditional': 'సాంప్రదాయ', 'craft': 'కళ', 'artist': 'కళాకారుడు'
            }
        }
        
        # Common phrases and greetings
        self.greetings = {
            'english': ['hello', 'hi', 'good morning', 'good afternoon', 'good evening', 'hey there'],
            'hindi': ['नमस्ते', 'हैलो', 'सुप्रभात', 'शुभ दोपहर', 'शुभ संध्या', 'हाय'],
            'tamil': ['வணக்கம்', 'ஹலோ', 'காலை வணக்கம்', 'மதிய வணக்கம்', 'மாலை வணக்கம்', 'ஹாய்'],
            'telugu': ['నమస్కారం', 'హలో', 'శుభోదయం', 'శుభ మధ్యాహ్నం', 'శుభ సాయంత్రం', 'హాయ్']
        }
        
        # Question patterns
        self.question_patterns = {
            'english': [
                'find', 'show me', 'search for', 'looking for', 'tell me about', 
                'where can I find', 'who are the', 'list all', 'can you help me find'
            ],
            'hindi': [
                'खोजें', 'मुझे दिखाएं', 'के लिए खोजें', 'की तलाश में', 'के बारे में बताएं',
                'कहां मिल सकता है', 'कौन हैं', 'सभी की सूची', 'क्या आप मदद कर सकते हैं'
            ],
            'tamil': [
                'தேடுங்கள்', 'காட்டுங்கள்', 'தேடல்', 'தேடுகிறேன்', 'பற்றி சொல்லுங்கள்',
                'எங்கே கிடைக்கும்', 'யார்', 'அனைத்தின் பட்டியல்', 'உதவி செய்ய முடியுமா'
            ],
            'telugu': [
                'వెతకండి', 'చూపించండి', 'వెతుకుట', 'వెతుకుతున్నాను', 'గురించి చెప్పండి',
                'ఎక్కడ దొరుకుతుంది', 'ఎవరు', 'అందరి జాబితా', 'సహాయం చేయగలరా'
            ]
        }
        
        # Location names (Indian states in different languages)
        self.locations = {
            'english': ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Andhra Pradesh', 'Kerala', 'Rajasthan', 'Gujarat', 'West Bengal', 'Punjab', 'Haryana'],
            'hindi': ['महाराष्ट्र', 'कर्नाटक', 'तमिल नाडु', 'आंध्र प्रदेश', 'केरल', 'राजस्थान', 'गुजरात', 'पश्चिम बंगाल', 'पंजाब', 'हरियाणा'],
            'tamil': ['மகாராஷ்ட்டிரா', 'கர்நாடகா', 'தமிழ்நாடு', 'ஆந்திரப் பிரதேசம்', 'கேரளா', 'ராஜஸ்தான்', 'குஜராத்', 'மேற்கு வங்காளம்', 'பஞ்சாப்', 'ஹரியானா'],
            'telugu': ['మహారాష్ట్ర', 'కర్ణాటక', 'తమిళనాడు', 'ఆంధ్రప్రదేశ్', 'కేరళ', 'రాజస్థాన్', 'గుజరాత్', 'పశ్చిమ బెంగాల్', 'పంజాబ్', 'హరియాణా']
        }
        
        # Response templates
        self.response_templates = {
            'english': {
                'greeting': 'Hello! I am Kala-Kaart AI assistant. How can I help you find traditional artisans today?',
                'found_artists': 'I found {count} {craft} artists in {location}. Here are their details:',
                'no_results': 'Sorry, I could not find any {craft} artists in {location}. Would you like to try a different search?',
                'help': 'I can help you find traditional Indian artisans by craft type, location, or name. What are you looking for?'
            },
            'hindi': {
                'greeting': 'नमस्ते! मैं कला-कार्त AI सहायक हूं। आज मैं आपको पारंपरिक कारीगर खोजने में कैसे मदद कर सकता हूं?',
                'found_artists': 'मुझे {location} में {count} {craft} कलाकार मिले हैं। यहां उनका विवरण है:',
                'no_results': 'क्षमा करें, मुझे {location} में कोई {craft} कलाकार नहीं मिले। क्या आप कोई अलग खोज करना चाहेंगे?',
                'help': 'मैं आपको शिल्प प्रकार, स्थान या नाम के आधार पर पारंपरिक भारतीय कारीगर खोजने में मदद कर सकता हूं। आप क्या खोज रहे हैं?'
            },
            'tamil': {
                'greeting': 'வணக்கம்! நான் கலா-கார்ட் AI உதவியாளர். இன்று பாரம்பரிய கைவினைஞர்களைக் கண்டறிய நான் எப்படி உதவ முடியும்?',
                'found_artists': '{location}ல் {count} {craft} கலைஞர்களை கண்டேன். இங்கே அவர்களின் விவரங்கள்:',
                'no_results': 'மன்னிக்கவும், {location}ல் {craft} கலைஞர்கள் எவரும் கிடைக்கவில்லை. வேறு தேடல் முயற்சிக்க விரும்புகிறீர்களா?',
                'help': 'கைவினை வகை, இடம் அல்லது பெயரின் அடிப்படையில் பாரம்பரிய இந்திய கைவினைஞர்களைக் கண்டறிய உதவ முடியும். நீங்கள் என்ன தேடுகிறீர்கள்?'
            },
            'telugu': {
                'greeting': 'నమస్కారం! నేను కలా-కార్ట్ AI సహాయకుడను. ఈ రోజు సాంప్రదాయ కళాకారులను కనుగొనడంలో నేను ఎలా సహాయం చేయగలను?',
                'found_artists': '{location}లో {count} {craft} కళాకారులను కనుగొన్నాను. ఇక్కడ వారి వివరాలు:',
                'no_results': 'క్షమించండి, {location}లో {craft} కళాకారులు ఎవరూ కనుగొనబడలేదు. వేరే శోధన ప్రయత్నించాలనుకుంటున్నారా?',
                'help': 'చేతిపని రకం, ప్రాంతం లేదా పేరు ఆధారంగా సాంప్రదాయ భారతీય కళాకారులను కనుగొనడంలో సహాయపడగలను. మీరు ఏమి వెతుకుతున్నారు?'
            }
        }

    def generate_training_conversations(self, num_samples: int = 1000) -> List[Dict[str, Any]]:
        """Generate training conversations in multiple languages"""
        conversations = []
        
        for _ in range(num_samples):
            lang = random.choice(self.languages)
            conversation = self._generate_single_conversation(lang)
            conversations.append(conversation)
        
        return conversations

    def _generate_single_conversation(self, language: str) -> Dict[str, Any]:
        """Generate a single conversation in specified language"""
        conversation_type = random.choice(['greeting', 'craft_search', 'location_search', 'artist_search', 'help_request'])
        
        if conversation_type == 'greeting':
            return self._generate_greeting_conversation(language)
        elif conversation_type == 'craft_search':
            return self._generate_craft_search_conversation(language)
        elif conversation_type == 'location_search':
            return self._generate_location_search_conversation(language)
        elif conversation_type == 'artist_search':
            return self._generate_artist_search_conversation(language)
        else:
            return self._generate_help_conversation(language)

    def _generate_greeting_conversation(self, language: str) -> Dict[str, Any]:
        """Generate greeting conversation"""
        greeting = random.choice(self.greetings[language])
        response = self.response_templates[language]['greeting']
        
        return {
            'language': language,
            'intent': 'greeting',
            'user_message': greeting,
            'bot_response': response,
            'entities': {},
            'context': {'conversation_type': 'greeting'}
        }

    def _generate_craft_search_conversation(self, language: str) -> Dict[str, Any]:
        """Generate craft search conversation"""
        craft_key = random.choice(list(self.craft_vocabulary['english'].keys()))
        craft_name = self.craft_vocabulary[language][craft_key]
        question_pattern = random.choice(self.question_patterns[language])
        location = random.choice(self.locations[language])
        
        user_message = f"{question_pattern} {craft_name}"
        if random.random() > 0.5:  # 50% chance to include location
            user_message += f" in {location}"
        
        # Simulate finding results
        count = random.randint(1, 15)
        if random.random() > 0.8:  # 20% chance of no results
            response = self.response_templates[language]['no_results'].format(
                craft=craft_name, location=location if 'in' in user_message else 'this area'
            )
        else:
            response = self.response_templates[language]['found_artists'].format(
                count=count, craft=craft_name, location=location if 'in' in user_message else 'various locations'
            )
        
        return {
            'language': language,
            'intent': 'craft_search',
            'user_message': user_message,
            'bot_response': response,
            'entities': {
                'craft': craft_name,
                'location': location if 'in' in user_message else None
            },
            'context': {'craft_type': craft_key, 'has_location': 'in' in user_message}
        }

    def _generate_location_search_conversation(self, language: str) -> Dict[str, Any]:
        """Generate location-based search conversation"""
        location = random.choice(self.locations[language])
        question_pattern = random.choice(self.question_patterns[language])
        craft_key = random.choice(list(self.craft_vocabulary['english'].keys()))
        craft_name = self.craft_vocabulary[language][craft_key]
        
        if random.random() > 0.5:
            user_message = f"{question_pattern} artists in {location}"
        else:
            user_message = f"{question_pattern} {craft_name} in {location}"
        
        count = random.randint(3, 25)
        response = self.response_templates[language]['found_artists'].format(
            count=count, craft=craft_name if craft_name in user_message else 'traditional', location=location
        )
        
        return {
            'language': language,
            'intent': 'location_search',
            'user_message': user_message,
            'bot_response': response,
            'entities': {
                'location': location,
                'craft': craft_name if craft_name in user_message else None
            },
            'context': {'location': location, 'has_craft': craft_name in user_message}
        }

    def _generate_artist_search_conversation(self, language: str) -> Dict[str, Any]:
        """Generate artist name search conversation"""
        # Mock artist names
        artist_names = {
            'english': ['Ravi Kumar', 'Priya Sharma', 'Amit Patel', 'Lakshmi Reddy'],
            'hindi': ['रवि कुमार', 'प्रिया शर्मा', 'अमित पटेल', 'लक्ष्मी रेड्डी'],
            'tamil': ['ரவி குமார்', 'பிரியா ஷர்மா', 'அமித் பட்டேல்', 'லட்சுமி ரெட்டி'],
            'telugu': ['రవి కుమార్', 'ప్రియా శర్మ', 'అమిత్ పటేల్', 'లక్ష్మి రెడ్డి']
        }
        
        artist_name = random.choice(artist_names[language])
        question_pattern = random.choice(self.question_patterns[language])
        
        user_message = f"{question_pattern} {artist_name}"
        
        if random.random() > 0.3:  # 70% chance of finding the artist
            craft_key = random.choice(list(self.craft_vocabulary['english'].keys()))
            craft_name = self.craft_vocabulary[language][craft_key]
            location = random.choice(self.locations[language])
            response = f"I found {artist_name}, a {craft_name} artist from {location}. Here are their contact details:"
        else:
            response = f"Sorry, I could not find an artist named {artist_name}. Would you like to search by craft or location instead?"
        
        return {
            'language': language,
            'intent': 'artist_search',
            'user_message': user_message,
            'bot_response': response,
            'entities': {'name': artist_name},
            'context': {'artist_name': artist_name}
        }

    def _generate_help_conversation(self, language: str) -> Dict[str, Any]:
        """Generate help request conversation"""
        help_requests = {
            'english': ['help', 'what can you do', 'how do I search', 'I need assistance'],
            'hindi': ['मदद', 'आप क्या कर सकते हैं', 'मैं कैसे खोजूं', 'मुझे सहायता चाहिए'],
            'tamil': ['உதவி', 'நீங்கள் என்ன செய்ய முடியும்', 'எப்படி தேடுவது', 'எனக்கு உதவி வேண்டும்'],
            'telugu': ['సహాయం', 'మీరు ఏమి చేయగలరు', 'ఎలా వెతకాలి', 'నాకు సహాయం కావాలి']
        }
        
        help_request = random.choice(help_requests[language])
        response = self.response_templates[language]['help']
        
        return {
            'language': language,
            'intent': 'help_request',
            'user_message': help_request,
            'bot_response': response,
            'entities': {},
            'context': {'request_type': 'help'}
        }

    def generate_craft_knowledge_base(self) -> Dict[str, List[Dict[str, str]]]:
        """Generate craft knowledge base in multiple languages"""
        craft_knowledge = {}
        
        for lang in self.languages:
            craft_knowledge[lang] = []
            
            for craft_en, craft_local in self.craft_vocabulary[lang].items():
                knowledge_entry = {
                    'craft_english': craft_en,
                    'craft_local': craft_local,
                    'description': self._get_craft_description(craft_en, lang),
                    'regions': self._get_craft_regions(craft_en, lang),
                    'materials': self._get_craft_materials(craft_en, lang),
                    'techniques': self._get_craft_techniques(craft_en, lang)
                }
                craft_knowledge[lang].append(knowledge_entry)
        
        return craft_knowledge

    def _get_craft_description(self, craft: str, language: str) -> str:
        """Get craft description in specified language"""
        descriptions = {
            'pottery': {
                'english': 'Traditional clay pottery making with wheel throwing and hand building techniques',
                'hindi': 'पारंपरिक मिट्टी के बर्तन बनाने की कला, चाक और हाथ से बनाने की तकनीकों के साथ',
                'tamil': 'சக்கர வீச்சு மற்றும் கை கட்டுமான நுட்பங்களுடன் பாரம்பரிய களிமண் மட்பாண்ட தயாரிப்பு',
                'telugu': 'చక్రం విసిరే మరియు చేతితో నిర్మాణ పద్ధతులతో సాంప్రదాయ మట్టి కుండల తయారీ'
            },
            'weaving': {
                'english': 'Traditional textile weaving using handlooms and natural fibers',
                'hindi': 'हाथ की तकिया और प्राकृतिक रेशों का उपयोग करके पारंपरिक कपड़ा बुनाई',
                'tamil': 'கைத்தறி மற்றும் இயற்கை இழைகளைப் பயன்படுத்தி பாரம்பரிய ஜவுளி நெசவு',
                'telugu': 'చేతితో వేసే గుడ్డలు మరియు సహజ ఫైబర్లను ఉపయోగించి సాంప్రదాయ వస్త్ర నేత'
            }
        }
        return descriptions.get(craft, {}).get(language, f"{craft} traditional craft")

    def _get_craft_regions(self, craft: str, language: str) -> List[str]:
        """Get regions known for specific craft"""
        regions = {
            'pottery': ['Gujarat', 'Rajasthan', 'West Bengal', 'Tamil Nadu'],
            'weaving': ['Karnataka', 'Andhra Pradesh', 'Tamil Nadu', 'Kerala'],
            'painting': ['Rajasthan', 'Madhya Pradesh', 'Orissa', 'Bihar']
        }
        return regions.get(craft, ['Various regions across India'])

    def _get_craft_materials(self, craft: str, language: str) -> List[str]:
        """Get materials used in craft"""
        materials = {
            'pottery': ['Clay', 'Natural pigments', 'Glazes'],
            'weaving': ['Cotton', 'Silk', 'Wool', 'Natural dyes'],
            'painting': ['Natural colors', 'Brushes', 'Canvas', 'Paper']
        }
        return materials.get(craft, ['Traditional materials'])

    def _get_craft_techniques(self, craft: str, language: str) -> List[str]:
        """Get techniques used in craft"""
        techniques = {
            'pottery': ['Wheel throwing', 'Hand building', 'Glazing', 'Firing'],
            'weaving': ['Plain weave', 'Twill weave', 'Pattern weaving', 'Dyeing'],
            'painting': ['Brush painting', 'Natural pigment preparation', 'Traditional patterns']
        }
        return techniques.get(craft, ['Traditional techniques'])

    def save_training_data(self, conversations: List[Dict], knowledge_base: Dict, filename: str = 'multilingual_training_data.json'):
        """Save training data to file"""
        training_data = {
            'conversations': conversations,
            'knowledge_base': knowledge_base,
            'metadata': {
                'languages': self.languages,
                'total_conversations': len(conversations),
                'languages_count': {lang: len([c for c in conversations if c['language'] == lang]) 
                                  for lang in self.languages}
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=2)
        
        print(f"Training data saved to {filename}")
        print(f"Total conversations: {len(conversations)}")
        for lang in self.languages:
            count = len([c for c in conversations if c['language'] == lang])
            print(f"{lang.capitalize()}: {count} conversations")

# Generate training data
if __name__ == "__main__":
    generator = MultilingualTrainingDataGenerator()
    
    # Generate training conversations
    print("Generating multilingual training conversations...")
    conversations = generator.generate_training_conversations(2000)
    
    # Generate knowledge base
    print("Generating craft knowledge base...")
    knowledge_base = generator.generate_craft_knowledge_base()
    
    # Save data
    generator.save_training_data(conversations, knowledge_base)
    print("Multilingual training data generation completed!")