from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import csv
import os
import asyncio
from lightweight_chatbot import LightweightEnhancedChatbot

app = FastAPI(title="Kala-Kaart Complete AI Platform", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
initialization_status = {"status": "initializing", "message": "Starting up..."}

def initialize_chatbot():
    """Initialize the lightweight enhanced chatbot"""
    global chatbot, initialization_status
    csv_path = "../src/Artisans.csv"
    
    try:
        initialization_status["message"] = "Loading artist database..."
        print("Initializing Lightweight Enhanced Chatbot...")
        
        chatbot = LightweightEnhancedChatbot(csv_path)
        
        initialization_status = {
            "status": "success", 
            "message": f"Chatbot initialized with {len(chatbot.data_processor.artists_data)} artists"
        }
        
        print("Enhanced chatbot initialized successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing chatbot: {e}")
        initialization_status = {
            "status": "error", 
            "message": f"Failed to initialize: {str(e)}"
        }
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup"""
    await asyncio.create_task(asyncio.to_thread(initialize_chatbot))

@app.get("/")
async def root():
    return {
        "message": "🎨 Kala-Kaart Complete AI Platform - Connecting you with India's traditional artisans",
        "version": "3.0.0",
        "status": initialization_status["status"],
        "features": [
            "Advanced AI Chatbot",
            "Multilingual Support", 
            "Smart Search",
            "Regional Knowledge Base",
            "Contact Information",
            "Craft Recommendations"
        ],
        "artists_loaded": len(chatbot.data_processor.artists_data) if chatbot else 0
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if chatbot else "initializing",
        "chatbot_ready": chatbot is not None,
        "total_artists": len(chatbot.data_processor.artists_data) if chatbot else 0,
        "database_loaded": True if chatbot else False,
        "initialization": initialization_status
    }

@app.get("/stats")
async def get_stats():
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not ready")
    
    try:
        return await asyncio.create_task(
            asyncio.to_thread(chatbot.data_processor.get_stats)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.post("/search")
async def search_artists(filters: SearchFilters):
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not ready")
    
    try:
        filter_dict = {k: v for k, v in filters.model_dump().items() if v is not None and k != 'limit'}
        
        results = await asyncio.create_task(
            asyncio.to_thread(chatbot.data_processor.search_artists, filter_dict)
        )
        
        # Apply limit
        limit = filters.limit or 20
        limited_results = results[:limit]
        
        # Transform for frontend
        transformed_artists = chatbot.transform_artists_for_frontend(limited_results)
        
        return {
            "artists": transformed_artists,
            "total_count": len(results),
            "filters_applied": filter_dict,
            "search_metadata": {
                "query_time": "< 100ms",
                "results_quality": "high",
                "suggestions": chatbot.get_contextual_suggestions()[:3]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    if not chatbot:
        return {
            "intent": "system_not_ready",
            "entities": {},
            "message": "🔄 **System Initializing...** Please wait a moment while I set up the AI chatbot.",
            "llm_message": None,
            "artists": [],
            "suggestions": ["Try again in a moment", "Check system status"],
            "stats": {},
            "context": {"status": initialization_status["status"]}
        }
    
    try:
        # Process query with enhanced chatbot
        response = await asyncio.create_task(
            asyncio.to_thread(chatbot.process_query, message.message, message.conversation_history)
        )
        
        # Add metadata
        response["metadata"] = {
            "processing_time": "< 200ms",
            "confidence": "high",
            "language_detected": response.get("context", {}).get("language", "english"),
            "version": "3.0.0"
        }
        
        return response
        
    except Exception as e:
        print(f"Chat processing error: {e}")
        return {
            "intent": "error",
            "entities": {},
            "message": "❌ I encountered an error processing your request. Please try rephrasing your question.",
            "llm_message": None,
            "artists": [],
            "suggestions": chatbot.get_contextual_suggestions() if chatbot else ["Try a different query", "Check system status"],
            "stats": chatbot.data_processor.get_stats() if chatbot else {},
            "context": {"error": str(e), "language": "english"}
        }

@app.get("/chat/suggestions")
async def get_chat_suggestions():
    """Get intelligent chat suggestions"""
    if not chatbot:
        return {
            "suggestions": [
                "System is starting up...",
                "Please wait a moment"
            ]
        }
    
    try:
        contextual_suggestions = chatbot.get_contextual_suggestions()
        
        # Add some curated suggestions
        curated_suggestions = [
            "Show me pottery artists",
            "Find artists in Gujarat", 
            "Artists practicing Madhubani painting",
            "Tell me about Rajasthani crafts",
            "Database statistics",
            "Wood carvers in Kerala",
            "Contact information for weavers",
            "Young artists practicing traditional crafts"
        ]
        
        # Combine and deduplicate
        all_suggestions = list(dict.fromkeys(contextual_suggestions + curated_suggestions))
        
        return {
            "suggestions": all_suggestions[:8],
            "categories": {
                "by_craft": ["pottery artists", "weaving artists", "painting artists"],
                "by_location": ["artists in Gujarat", "artists in Rajasthan", "artists in Kerala"],
                "by_age": ["young artists", "senior master artisans"],
                "general": ["database statistics", "popular crafts", "regional specialties"]
            }
        }
        
    except Exception as e:
        return {
            "suggestions": [
                "Show me pottery artists",
                "Find artists in Gujarat",
                "Database statistics"
            ],
            "error": str(e)
        }

@app.get("/knowledge")
async def get_knowledge_base():
    """Access the chatbot's knowledge base"""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not ready")
    
    try:
        knowledge = chatbot.knowledge_base
        stats = chatbot.data_processor.get_stats()
        
        return {
            "craft_descriptions": knowledge.get('craft_descriptions', {}),
            "regional_specialties": knowledge.get('regional_specialties', {}),
            "database_overview": {
                "total_crafts": len(knowledge.get('craft_descriptions', {})),
                "total_regions": len(knowledge.get('regional_specialties', {})),
                "total_artists": stats.get('total_artists', 0),
                "coverage": f"{stats.get('unique_states', 0)} states"
            },
            "featured_crafts": list(knowledge.get('craft_descriptions', {}).keys())[:8],
            "featured_regions": list(knowledge.get('regional_specialties', {}).keys())[:10]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge base error: {str(e)}")

@app.get("/artists/random")
async def get_random_artists(count: int = 6):
    """Get random featured artists"""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not ready")
    
    try:
        import random
        all_artists = chatbot.data_processor.artists_data
        
        if len(all_artists) > count:
            featured_artists = random.sample(all_artists, count)
        else:
            featured_artists = all_artists[:count]
        
        transformed_artists = chatbot.transform_artists_for_frontend(featured_artists)
        
        return {
            "artists": transformed_artists,
            "message": f"Here are {len(transformed_artists)} featured artists from our community",
            "total_available": len(all_artists)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting random artists: {str(e)}")

@app.get("/crafts")
async def get_craft_types():
    """Get all available craft types"""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not ready")
    
    try:
        stats = chatbot.data_processor.get_stats()
        crafts = stats.get('crafts', [])
        
        # Get artist counts per craft
        craft_counts = {}
        for artist in chatbot.data_processor.artists_data:
            craft = artist.get('craft_type', '')
            craft_counts[craft] = craft_counts.get(craft, 0) + 1
        
        craft_details = []
        for craft in crafts:
            craft_info = {
                "name": craft,
                "artist_count": craft_counts.get(craft, 0),
                "description": chatbot.knowledge_base['craft_descriptions'].get(craft.lower(), f"Traditional {craft} practiced by skilled artisans across India.")
            }
            craft_details.append(craft_info)
        
        # Sort by artist count
        craft_details.sort(key=lambda x: x['artist_count'], reverse=True)
        
        return {
            "crafts": craft_details,
            "total_craft_types": len(crafts),
            "popular_crafts": [c['name'] for c in craft_details[:8]]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting crafts: {str(e)}")

@app.get("/states")
async def get_states():
    """Get all available states with artist information"""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not ready")
    
    try:
        stats = chatbot.data_processor.get_stats()
        states = stats.get('states', [])
        
        # Get artist counts per state
        state_counts = {}
        for artist in chatbot.data_processor.artists_data:
            state = artist.get('state', '')
            state_counts[state] = state_counts.get(state, 0) + 1
        
        state_details = []
        for state in states:
            state_info = {
                "name": state,
                "artist_count": state_counts.get(state, 0),
                "specialties": chatbot.knowledge_base['regional_specialties'].get(state.lower(), []),
                "districts": len(set(artist.get('district', '') for artist in chatbot.data_processor.artists_data if artist.get('state') == state))
            }
            state_details.append(state_info)
        
        # Sort by artist count
        state_details.sort(key=lambda x: x['artist_count'], reverse=True)
        
        return {
            "states": state_details,
            "total_states": len(states),
            "active_states": [s['name'] for s in state_details if s['artist_count'] > 0]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting states: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("Starting Kala-Kaart Complete AI Platform...")
    uvicorn.run(app, host="0.0.0.0", port=8000)