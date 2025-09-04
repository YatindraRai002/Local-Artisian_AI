from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import os

app = FastAPI(title="Kala-Kaart Simple API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
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
data = None

def load_data():
    global data
    csv_path = "../src/Artisans.csv"
    try:
        data = pd.read_csv(csv_path)
        print(f"Loaded {len(data)} artisan records")
        # Clean data
        data = data.dropna(subset=['name', 'craft_type', 'state', 'district'])
        data['languages_spoken'] = data['languages_spoken'].fillna('')
        data['contact_phone'] = data['contact_phone'].astype(str)
    except Exception as e:
        print(f"Error loading data: {e}")
        data = pd.DataFrame()

@app.on_event("startup")
async def startup_event():
    load_data()

@app.get("/")
async def root():
    return {"message": "Kala-Kaart Simple API is running!"}

@app.get("/health")
async def health_check():
    if data is None or data.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    return {
        "status": "healthy",
        "total_artists": len(data),
        "database_loaded": True
    }

@app.get("/stats")
async def get_stats():
    if data is None or data.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    return {
        'total_artists': len(data),
        'unique_states': len(data['state'].unique()),
        'unique_districts': len(data['district'].unique()),
        'unique_crafts': len(data['craft_type'].unique()),
        'states': sorted(data['state'].unique().tolist()),
        'crafts': sorted(data['craft_type'].unique().tolist()),
        'age_distribution': {
            'min': int(data['age'].min()),
            'max': int(data['age'].max()),
            'mean': float(data['age'].mean())
        }
    }

@app.post("/search")
async def search_artists(filters: SearchFilters):
    if data is None or data.empty:
        raise HTTPException(status_code=503, detail="Data not loaded")
    
    filtered_df = data.copy()
    
    if filters.state:
        filtered_df = filtered_df[
            filtered_df['state'].str.contains(filters.state, case=False, na=False)
        ]
    
    if filters.district:
        filtered_df = filtered_df[
            filtered_df['district'].str.contains(filters.district, case=False, na=False)
        ]
    
    if filters.craft_type:
        filtered_df = filtered_df[
            filtered_df['craft_type'].str.contains(filters.craft_type, case=False, na=False)
        ]
    
    if filters.name:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(filters.name, case=False, na=False)
        ]
    
    if filters.age_min:
        filtered_df = filtered_df[filtered_df['age'] >= filters.age_min]
    
    if filters.age_max:
        filtered_df = filtered_df[filtered_df['age'] <= filters.age_max]
    
    # Apply limit
    limit = filters.limit or 20
    artists = filtered_df.head(limit).to_dict('records')
    
    return {
        "artists": artists,
        "total_count": len(filtered_df),
        "filters_applied": {k: v for k, v in filters.dict().items() if v is not None}
    }

@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    # Simple fallback response
    return {
        "intent": "general_query",
        "entities": {},
        "message": "Simple API mode: Chat functionality requires full dependencies.",
        "llm_message": None,
        "artists": [],
        "suggestions": ["Try searching by state", "Try searching by craft", "Browse all artists"],
        "stats": await get_stats() if data is not None else {}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)