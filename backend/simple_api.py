from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import csv
import json

# Initialize FastAPI app
app = FastAPI(title="Kala-Kaart AI Chatbot API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    intent: str
    entities: Dict[str, Any]
    message: str
    artists: List[Dict[str, Any]]
    suggestions: List[str]

# Global data
artisan_data = []

def load_artisan_data():
    """Load artisan data from CSV"""
    global artisan_data
    csv_path = os.path.join(os.path.dirname(__file__), "..", "src", "Artisans.csv")
    
    if not os.path.exists(csv_path):
        print(f"Warning: CSV file not found at {csv_path}")
        return
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            artisan_data = list(reader)
            print(f"Loaded {len(artisan_data)} artisan records")
    except Exception as e:
        print(f"Error loading data: {e}")

def simple_search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Simple text-based search through artisan data"""
    if not artisan_data:
        return []
    
    query_lower = query.lower()
    results = []
    
    for artist in artisan_data:
        # Search in relevant fields
        searchable_text = " ".join([
            str(artist.get('name', '')),
            str(artist.get('craft_type', '')),
            str(artist.get('state', '')),
            str(artist.get('district', '')),
            str(artist.get('village', '')),
        ]).lower()
        
        if any(word in searchable_text for word in query_lower.split()):
            results.append(artist)
        
        if len(results) >= limit:
            break
    
    return results

def extract_entities(message: str) -> Dict[str, Any]:
    """Simple entity extraction"""
    entities = {}
    message_lower = message.lower()
    
    # Extract state names (simplified)
    states = ['punjab', 'haryana', 'rajasthan', 'gujarat', 'maharashtra', 'karnataka', 
              'tamil nadu', 'kerala', 'andhra pradesh', 'telangana', 'odisha', 'west bengal']
    
    for state in states:
        if state in message_lower:
            entities['state'] = state.title()
            break
    
    # Extract craft types (simplified)
    crafts = ['pottery', 'weaving', 'woodwork', 'metalwork', 'painting', 'textile', 
              'embroidery', 'sculpture', 'jewelry', 'leather']
    
    for craft in crafts:
        if craft in message_lower:
            entities['craft_type'] = craft.title()
            break
    
    return entities

@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    load_artisan_data()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Kala-Kaart AI Chatbot API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "chatbot_initialized": True,
        "total_artists": len(artisan_data),
        "database_loaded": len(artisan_data) > 0
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Main chat endpoint - simplified version"""
    try:
        user_message = message.message
        entities = extract_entities(user_message)
        
        # Determine intent (simplified)
        intent = "find_artist"
        
        # Search for artists
        artists = simple_search(user_message, limit=5)
        
        # Generate response message
        if artists:
            response_message = f"Found {len(artists)} artisan(s) matching your query."
            if entities:
                if 'state' in entities:
                    response_message += f" Showing results from {entities['state']}."
                if 'craft_type' in entities:
                    response_message += f" Specializing in {entities['craft_type']}."
        else:
            response_message = "Sorry, I couldn't find any artisans matching your query. Please try with different keywords."
        
        # Generate suggestions
        suggestions = [
            "Show me pottery artists",
            "Find artisans in Punjab",
            "Show textile workers",
            "Find artists in Karnataka"
        ]
        
        return ChatResponse(
            intent=intent,
            entities=entities,
            message=response_message,
            artists=artists,
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get basic statistics"""
    if not artisan_data:
        return {"message": "No data loaded"}
    
    # Calculate basic stats
    states = set()
    crafts = set()
    
    for artist in artisan_data:
        if artist.get('state'):
            states.add(artist['state'])
        if artist.get('craft_type'):
            crafts.add(artist['craft_type'])
    
    return {
        "total_artists": len(artisan_data),
        "unique_states": len(states),
        "unique_crafts": len(crafts),
        "states": sorted(list(states)),
        "crafts": sorted(list(crafts))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)