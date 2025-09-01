from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from chatbot_engine import ArtisanChatbot
from data_processor import ArtisanDataProcessor
import asyncio
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="Kala-Kaart AI Chatbot API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[str]] = []

class ChatResponse(BaseModel):
    intent: str
    entities: Dict[str, Any]
    message: str
    llm_message: Optional[str] = None
    artists: List[Dict[str, Any]]
    suggestions: List[str]
    stats: Dict[str, Any]

class SearchFilters(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    craft_type: Optional[str] = None
    name: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    limit: Optional[int] = 20

class ArtistResponse(BaseModel):
    artists: List[Dict[str, Any]]
    total_count: int
    filters_applied: Dict[str, Any]

# Global chatbot instance
chatbot = None

def initialize_chatbot():
    """Initialize the chatbot with data"""
    global chatbot
    csv_path = "../src/Artisans.csv"  # Path to your CSV file
    model_data_path = "model_data.pkl"
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at {csv_path}")
    
    print("Initializing chatbot...")
    chatbot = ArtisanChatbot(csv_path, model_data_path)
    print("Chatbot initialized successfully!")

@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup"""
    try:
        await asyncio.create_task(asyncio.to_thread(initialize_chatbot))
    except Exception as e:
        print(f"Failed to initialize chatbot: {e}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Kala-Kaart AI Chatbot API is running!"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    stats = chatbot.data_processor.get_stats()
    return {
        "status": "healthy",
        "chatbot_initialized": True,
        "total_artists": stats.get('total_artists', 0),
        "database_loaded": len(stats) > 0
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        # Process the user message
        response = await asyncio.create_task(
            asyncio.to_thread(chatbot.process_query, message.message)
        )
        
        # Add conversation-based suggestions if history is provided
        if message.conversation_history:
            contextual_suggestions = chatbot.get_conversation_suggestions(
                message.conversation_history
            )
            response['suggestions'].extend(contextual_suggestions)
            response['suggestions'] = list(set(response['suggestions']))[:6]
        
        return ChatResponse(**response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/search", response_model=ArtistResponse)
async def search_artists(filters: SearchFilters):
    """Search artists with filters"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        filter_dict = {k: v for k, v in filters.dict().items() if v is not None and k != 'limit'}
        
        artists = await asyncio.create_task(
            asyncio.to_thread(chatbot.data_processor.search_artists, filter_dict)
        )
        
        # Apply limit
        limit = filters.limit or 20
        limited_artists = artists[:limit]
        
        return ArtistResponse(
            artists=limited_artists,
            total_count=len(artists),
            filters_applied=filter_dict
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching artists: {str(e)}")

@app.get("/artists/similar/{artist_id}")
async def get_similar_artists(artist_id: str, limit: int = 5):
    """Find similar artists to a given artist"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        # Find the artist first
        artist = chatbot.data_processor.search_artists({'artisan_id': artist_id})
        if not artist:
            raise HTTPException(status_code=404, detail="Artist not found")
        
        # Create a query from artist's details
        artist_data = artist[0]
        query = f"{artist_data['craft_type']} {artist_data['state']} {artist_data['district']}"
        
        similar_artists = await asyncio.create_task(
            asyncio.to_thread(chatbot.data_processor.find_similar_artists, query, limit + 1)
        )
        
        # Remove the original artist from results
        similar_artists = [a for a in similar_artists if str(a.get('artisan_id')) != str(artist_id)][:limit]
        
        return {
            "original_artist": artist_data,
            "similar_artists": similar_artists
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar artists: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        stats = await asyncio.create_task(
            asyncio.to_thread(chatbot.data_processor.get_stats)
        )
        
        # Add additional analytics
        categories = await asyncio.create_task(
            asyncio.to_thread(chatbot.data_processor.categorize_by_state_city_craft)
        )
        
        # Count artists per state
        state_counts = {}
        for state, cities in categories.items():
            count = sum(len(crafts) for city_crafts in cities.values() 
                       for crafts in city_crafts.values())
            state_counts[state] = count
        
        stats['artists_per_state'] = state_counts
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/categories")
async def get_categories():
    """Get all categorized data"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        categories = await asyncio.create_task(
            asyncio.to_thread(chatbot.data_processor.categorize_by_state_city_craft)
        )
        
        return {
            "categories": categories,
            "summary": {
                "total_states": len(categories),
                "total_combinations": sum(
                    len(cities) * len(crafts)
                    for cities in categories.values()
                    for crafts in cities.values()
                )
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting categories: {str(e)}")

@app.post("/retrain")
async def retrain_model(background_tasks: BackgroundTasks):
    """Retrain the model with updated data"""
    if chatbot is None:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    def retrain():
        # Reinitialize the data processor
        chatbot.data_processor.load_and_process_data()
        chatbot.data_processor.save_model_data("model_data.pkl")
        print("Model retrained successfully")
    
    background_tasks.add_task(retrain)
    
    return {"message": "Model retraining started in background"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)