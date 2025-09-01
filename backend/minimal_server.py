from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import csv
import os

app = FastAPI(title="Kala-Kaart Minimal API", version="1.0.0")

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

# Global data
artists_data = []

def load_csv_data():
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

@app.on_event("startup")
async def startup_event():
    load_csv_data()

@app.get("/")
async def root():
    return {"message": "Kala-Kaart Minimal API is running!", "artists_loaded": len(artists_data)}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "total_artists": len(artists_data),
        "database_loaded": len(artists_data) > 0
    }

@app.get("/stats")
async def get_stats():
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

def process_natural_query(query: str, stats: dict):
    """Process natural language query and return structured response"""
    query_lower = query.lower()
    
    # Extract intent and entities
    intent = "general_query"
    entities = {}
    search_filters = {}
    response_message = ""
    artists = []
    suggestions = []
    
    # State detection
    states = stats.get('states', [])
    for state in states:
        if state.lower() in query_lower:
            entities['state'] = state
            search_filters['state'] = state
            intent = "find_by_location"
            break
    
    # Craft detection  
    crafts = stats.get('crafts', [])
    for craft in crafts:
        if craft.lower() in query_lower or craft.lower().replace(' ', '') in query_lower.replace(' ', ''):
            entities['craft'] = craft
            search_filters['craft_type'] = craft
            if intent == "find_by_location":
                intent = "find_by_location_and_craft"
            else:
                intent = "find_by_craft"
            break
    
    # Age-related queries
    if any(word in query_lower for word in ['young', 'old', 'age', 'senior', 'elderly']):
        if 'young' in query_lower:
            search_filters['age_max'] = 35
            entities['age_range'] = 'young (up to 35)'
        elif any(word in query_lower for word in ['old', 'senior', 'elderly']):
            search_filters['age_min'] = 50
            entities['age_range'] = 'senior (50+)'
        intent = "find_by_age" if 'craft' not in entities and 'state' not in entities else intent
    
    # Gender queries
    if any(word in query_lower for word in ['male', 'female', 'men', 'women']):
        if any(word in query_lower for word in ['male', 'men']):
            entities['gender'] = 'Male'
        elif any(word in query_lower for word in ['female', 'women']):
            entities['gender'] = 'Female'
    
    # Contact/phone queries
    if any(word in query_lower for word in ['contact', 'phone', 'call', 'reach']):
        intent = "get_contact_info"
    
    # Statistics queries
    if any(word in query_lower for word in ['how many', 'count', 'total', 'statistics', 'stats']):
        intent = "get_statistics"
    
    # Name-based queries
    name_patterns = ['named', 'called', 'name is', 'artist named']
    for pattern in name_patterns:
        if pattern in query_lower:
            # Extract potential name after the pattern
            parts = query_lower.split(pattern)
            if len(parts) > 1:
                potential_name = parts[1].strip().split()[0] if parts[1].strip() else ""
                if potential_name:
                    search_filters['name'] = potential_name
                    entities['name'] = potential_name
                    intent = "find_by_name"
            break
    
    return intent, entities, search_filters

async def generate_response(intent: str, entities: dict, search_filters: dict, stats: dict):
    """Generate appropriate response based on intent and entities"""
    
    if intent == "get_statistics":
        return {
            "message": f"📊 **Kala-Kaart Database Statistics:**\n\n" +
                      f"🎨 **Total Artists:** {stats['total_artists']:,}\n" +
                      f"🏛️ **States Covered:** {stats['unique_states']}\n" +
                      f"🏘️ **Districts:** {stats['unique_districts']}\n" +
                      f"🎭 **Unique Crafts:** {stats['unique_crafts']}\n\n" +
                      f"**Age Range:** {stats['age_distribution']['min']}-{stats['age_distribution']['max']} years " +
                      f"(avg: {stats['age_distribution']['mean']:.1f})",
            "artists": [],
            "suggestions": ["Show me pottery artists", "Find artists in Gujarat", "Show craft types"]
        }
    
    # Search for artists based on filters
    artists = []
    if search_filters:
        # Simulate the search (in real implementation, this would call the search function)
        search_request = SearchFilters(**search_filters, limit=5)
        search_result = await search_artists(search_request)
        artists = search_result["artists"]
    
    if intent == "find_by_craft":
        craft = entities.get('craft', 'that craft')
        if artists:
            message = f"🎨 Found {len(artists)} **{craft}** artists. Here are the top results:"
            suggestions = [f"More {craft} artists", "Contact information", f"{craft} artists in Gujarat"]
        else:
            message = f"❌ No {craft} artists found. Try checking the spelling or browse our available crafts."
            suggestions = ["Show all crafts", "Find pottery artists", "Browse by state"]
    
    elif intent == "find_by_location":
        location = entities.get('state', 'that location')
        if artists:
            message = f"📍 Found {len(artists)} artists in **{location}**. Here are some featured artisans:"
            suggestions = [f"More artists in {location}", "Show craft types", f"Contact artists in {location}"]
        else:
            message = f"❌ No artists found in {location}. Check available states."
            suggestions = ["Show all states", "Find artists by craft", "Browse popular locations"]
    
    elif intent == "find_by_location_and_craft":
        location = entities.get('state', '')
        craft = entities.get('craft', '')
        if artists:
            message = f"🎯 Perfect match! Found {len(artists)} **{craft}** artists in **{location}**:"
            suggestions = [f"More {craft} in {location}", "Contact information", "Similar crafts"]
        else:
            message = f"❌ No {craft} artists found in {location}. Try nearby states or similar crafts."
            suggestions = [f"All {craft} artists", f"All artists in {location}", "Browse similar crafts"]
    
    elif intent == "find_by_name":
        name = entities.get('name', '')
        if artists:
            message = f"👤 Found artists with name '{name}':"
            suggestions = ["Contact information", "Similar artists", "Artists in same location"]
        else:
            message = f"❌ No artists named '{name}' found. Try checking the spelling or browse by location/craft."
            suggestions = ["Browse by state", "Find by craft type", "Show random artists"]
    
    elif intent == "get_contact_info":
        message = "📞 **Contact Information Available!** Search for specific artists to get their phone numbers and email addresses. All our verified artisans have contact details available."
        suggestions = ["Find pottery artists", "Search by location", "Browse featured artists"]
    
    else:  # general_query
        message = (f"🙏 Welcome to **Kala-Kaart**! I'm your AI assistant for finding traditional Indian artisans.\n\n"
                  f"📊 **Our Database:** {stats['total_artists']:,} verified artists from {stats['unique_states']} states\n"
                  f"🎨 **Specialties:** {stats['unique_crafts']} traditional crafts\n\n"
                  f"**Ask me things like:**\n"
                  f"• 'Show me pottery artists in Gujarat'\n"
                  f"• 'Find Kalamkari artists'\n"
                  f"• 'Artists in Rajasthan'\n"
                  f"• 'Young weaving artists'")
        suggestions = [
            "Show me pottery artists",
            "Find artists in Gujarat", 
            "Show Kalamkari artists",
            "Artists in Rajasthan",
            "Database statistics"
        ]
    
    return {
        "message": message,
        "artists": artists,
        "suggestions": suggestions
    }

@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    try:
        stats = await get_stats()
        query = message.message
        
        # Process the natural language query
        intent, entities, search_filters = process_natural_query(query, stats)
        
        # Generate appropriate response
        response = await generate_response(intent, entities, search_filters, stats)
        
        return {
            "intent": intent,
            "entities": entities,
            "message": response["message"],
            "llm_message": None,
            "artists": response["artists"],
            "suggestions": response["suggestions"],
            "stats": stats
        }
        
    except Exception as e:
        print(f"Chat error: {e}")
        stats = await get_stats()
        return {
            "intent": "error",
            "entities": {},
            "message": "❌ Sorry, I encountered an error processing your request. Please try again with a different query.",
            "llm_message": None,
            "artists": [],
            "suggestions": ["Show me pottery artists", "Find artists in Gujarat", "Database statistics"],
            "stats": stats
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)