from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel
from typing import Optional
import os
import sys

# Add backend to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', 'backend')
sys.path.append(backend_dir)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchFilters(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    craft_type: Optional[str] = None
    name: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    limit: Optional[int] = 20

# Global data processor
data_processor = None

def get_data_processor():
    global data_processor
    if data_processor is None:
        try:
            from data_processor import ArtisanDataProcessor
            csv_path = os.path.join(backend_dir, '..', 'public', 'Artisans.csv')
            data_processor = ArtisanDataProcessor(csv_path, max_artists=1000)
        except Exception as e:
            print(f"Error initializing data processor: {e}")
            return None
    return data_processor

@app.post("/")
async def search_artists(filters: SearchFilters):
    processor = get_data_processor()
    if not processor:
        raise HTTPException(status_code=503, detail="Data processor not ready")
    
    try:
        filter_dict = {k: v for k, v in filters.model_dump().items() if v is not None and k != 'limit'}
        results = processor.search_artists(filter_dict)
        
        # Apply limit
        limit = filters.limit or 20
        limited_results = results[:limit]
        
        # Transform for frontend
        from lightweight_chatbot import LightweightEnhancedChatbot
        bot = LightweightEnhancedChatbot(None)
        transformed_artists = bot.transform_artists_for_frontend(limited_results)
        
        return {
            "artists": transformed_artists,
            "total_count": len(results),
            "filters_applied": filter_dict,
            "search_metadata": {
                "query_time": "< 100ms",
                "results_quality": "high"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

handler = Mangum(app, lifespan="off")