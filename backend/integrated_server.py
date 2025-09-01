from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import csv
import os
import asyncio
from enhanced_chatbot import EnhancedKalaKaartChatbot

app = FastAPI(title="Kala-Kaart Integrated AI API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[str]] = []

class SearchFilters(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    craft_type: Optional[str] = None
    name: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    limit: Optional[int] = 20

# Global chatbot instance
chatbot = None
artists_data = []

def load_csv_data():
    """Load CSV data for fallback functionality"""
    global artists_data
    csv_path = "../src/Artisans.csv"
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            artists_data = []
            for row in reader:
                if row.get('name') and row.get('craft_type') and row.get('state'):
                    # Convert age to int if possible
                    try:
                        row['age'] = int(row['age'])
                    except:
                        row['age'] = 0
                    artists_data.append(row)
        
        print(f"Loaded {len(artists_data)} artist records")
        
    except Exception as e:
        print(f"Error loading CSV: {e}")
        artists_data = []

def initialize_enhanced_chatbot():
    """Initialize the enhanced chatbot"""
    global chatbot
    csv_path = "../src/Artisans.csv"
    model_data_path = "enhanced_model_data.pkl"
    
    try:
        print("Initializing Enhanced Kala-Kaart Chatbot...")
        chatbot = EnhancedKalaKaartChatbot(csv_path, model_data_path)
        print("Enhanced chatbot initialized successfully!")
        return True
    except Exception as e:
        print(f"Error initializing enhanced chatbot: {e}")
        print("Falling back to basic functionality...")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup"""
    load_csv_data()
    
    # Try to initialize enhanced chatbot
    success = await asyncio.create_task(asyncio.to_thread(initialize_enhanced_chatbot))
    
    if not success:
        print("Running in basic mode without enhanced AI features")

@app.get("/")
async def root():
    enhanced_status = "Enhanced AI" if chatbot else "Basic Mode"
    return {
        "message": f"Kala-Kaart Integrated API is running in {enhanced_status}!",
        "artists_loaded": len(artists_data),
        "enhanced_features": chatbot is not None
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "total_artists": len(artists_data),
        "database_loaded": len(artists_data) > 0,
        "enhanced_chatbot": chatbot is not None
    }

@app.get("/stats")
async def get_stats():
    if chatbot and hasattr(chatbot, 'data_processor'):
        # Use enhanced chatbot's data processor
        try:
            return await asyncio.create_task(
                asyncio.to_thread(chatbot.data_processor.get_stats)
            )
        except:
            pass
    
    # Fallback to basic stats
    if not artists_data:
        return {
            'total_artists': 0,
            'unique_states': 0,
            'unique_districts': 0,
            'unique_crafts': 0,
            'states': [],
            'crafts': []
        }
    
    states = set()
    districts = set()
    crafts = set()
    ages = []
    
    for artist in artists_data:
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
        'total_artists': len(artists_data),
        'unique_states': len(states),
        'unique_districts': len(districts),
        'unique_crafts': len(crafts),
        'states': sorted(list(states)),
        'crafts': sorted(list(crafts)),
        'age_distribution': age_stats
    }

@app.post("/search")
async def search_artists(filters: SearchFilters):
    if chatbot and hasattr(chatbot, 'data_processor'):
        # Use enhanced chatbot's search
        try:
            filter_dict = {k: v for k, v in filters.model_dump().items() if v is not None and k != 'limit'}
            
            results = await asyncio.create_task(
                asyncio.to_thread(chatbot.data_processor.search_artists, filter_dict)
            )
            
            # Apply limit
            limit = filters.limit or 20
            limited_results = results[:limit]
            
            # Transform data to match frontend expectations
            transformed_artists = []
            for artist in limited_results:
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
            
            return {
                "artists": transformed_artists,
                "total_count": len(results),
                "filters_applied": filter_dict
            }
        except Exception as e:
            print(f"Enhanced search failed: {e}, falling back to basic search")
    
    # Fallback to basic search
    if not artists_data:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    filtered_artists = []
    
    for artist in artists_data:
        # Apply filters
        if filters.state and filters.state.lower() not in artist.get('state', '').lower():
            continue
        if filters.district and filters.district.lower() not in artist.get('district', '').lower():
            continue
        if filters.craft_type and filters.craft_type.lower() not in artist.get('craft_type', '').lower():
            continue
        if filters.name and filters.name.lower() not in artist.get('name', '').lower():
            continue
        if filters.age_min and artist.get('age', 0) < filters.age_min:
            continue
        if filters.age_max and artist.get('age', 0) > filters.age_max:
            continue
        
        filtered_artists.append(artist)
    
    # Apply limit
    limit = filters.limit or 20
    limited_artists = filtered_artists[:limit]
    
    # Transform data to match frontend expectations
    transformed_artists = []
    for artist in limited_artists:
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
    
    return {
        "artists": transformed_artists,
        "total_count": len(filtered_artists),
        "filters_applied": {k: v for k, v in filters.model_dump().items() if v is not None}
    }

@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    if chatbot:
        # Use enhanced chatbot
        try:
            response = await asyncio.create_task(
                asyncio.to_thread(chatbot.process_query, message.message, message.conversation_history)
            )
            return response
        except Exception as e:
            print(f"Enhanced chat failed: {e}, falling back to basic response")
    
    # Fallback to basic response
    try:
        stats = await get_stats()
        return {
            "intent": "general_query",
            "entities": {},
            "message": f"Welcome to Kala-Kaart! I have {stats['total_artists']:,} artists from {stats['unique_states']} states. How can I help you find traditional artisans?",
            "llm_message": None,
            "artists": [],
            "suggestions": [
                "Show me pottery artists",
                "Find artists in Gujarat",
                "Database statistics",
                "Browse craft types"
            ],
            "stats": stats
        }
    except Exception as e:
        return {
            "intent": "error",
            "entities": {},
            "message": "❌ Service temporarily unavailable. Please try again later.",
            "llm_message": None,
            "artists": [],
            "suggestions": ["Try again later", "Browse artists", "Check service status"],
            "stats": {}
        }

@app.get("/chat/suggestions")
async def get_chat_suggestions():
    """Get suggested queries for the chat interface"""
    suggestions = [
        "Show me pottery artists",
        "Find artists in Gujarat",
        "Artists practicing Kalamkari",
        "Young weaving artists",
        "Pottery artists in Rajasthan",
        "Tell me about traditional crafts",
        "Database statistics",
        "Contact information for artists"
    ]
    
    if chatbot:
        # Add context-aware suggestions from chatbot
        try:
            context = getattr(chatbot, 'conversation_context', {})
            if context.get('last_intent') == 'find_by_craft' and 'craft' in context.get('last_entities', {}):
                craft = context['last_entities']['craft']
                suggestions.extend([
                    f"More {craft} artists",
                    f"{craft} artists in different states",
                    f"Contact {craft} artists"
                ])
        except:
            pass
    
    return {"suggestions": suggestions}

@app.get("/knowledge")
async def get_knowledge_base():
    """Get information from the chatbot's knowledge base"""
    if chatbot and hasattr(chatbot, 'knowledge_base'):
        try:
            knowledge = chatbot.knowledge_base
            return {
                "craft_descriptions": knowledge.get('craft_descriptions', {}),
                "regional_specialties": knowledge.get('regional_specialties', {}),
                "total_crafts": len(knowledge.get('craft_descriptions', {})),
                "total_regions": len(knowledge.get('regional_specialties', {}))
            }
        except Exception as e:
            return {"error": f"Knowledge base unavailable: {e}"}
    
    return {"message": "Knowledge base not available in basic mode"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)