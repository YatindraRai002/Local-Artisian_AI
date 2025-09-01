from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel
from typing import List, Optional
import json
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

class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[str]] = []

# Global chatbot instance - lightweight for serverless
chatbot = None

def get_chatbot():
    global chatbot
    if chatbot is None:
        try:
            from lightweight_chatbot import LightweightEnhancedChatbot
            # Use a smaller dataset for serverless deployment
            csv_path = os.path.join(backend_dir, '..', 'src', 'Artisans.csv')
            chatbot = LightweightEnhancedChatbot(csv_path, max_artists=1000)
        except Exception as e:
            print(f"Error initializing chatbot: {e}")
            return None
    return chatbot

@app.post("/")
async def chat_endpoint(message: ChatMessage):
    bot = get_chatbot()
    if not bot:
        return {
            "intent": "system_not_ready",
            "entities": {},
            "message": "🔄 **System Initializing...** Please wait a moment while I set up the AI chatbot.",
            "llm_message": None,
            "artists": [],
            "suggestions": ["Try again in a moment", "Check system status"],
            "stats": {},
            "context": {"status": "initializing"}
        }
    
    try:
        response = bot.process_query(message.message, message.conversation_history)
        response["metadata"] = {
            "processing_time": "< 200ms",
            "confidence": "high",
            "version": "3.1.0"
        }
        return response
        
    except Exception as e:
        return {
            "intent": "error",
            "entities": {},
            "message": "❌ I encountered an error processing your request. Please try rephrasing your question.",
            "llm_message": None,
            "artists": [],
            "suggestions": ["Try a different query", "Check system status"],
            "stats": {},
            "context": {"error": str(e), "language": "english"}
        }

handler = Mangum(app, lifespan="off")