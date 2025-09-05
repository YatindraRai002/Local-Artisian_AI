from helpers.data_loader import load_artists_data

def is_hindi(text):
    return any('\u0900' <= ch <= '\u097F' for ch in text)

def handle_chat(body):
    message = body.get("message", "")
    conversation_history = body.get("conversation_history", [])
    artists = load_artists_data()[:5]  # sample
    response = {
        "intent": "general",
        "message": "This is where Hindi/English logic will go.",
        "artists": artists,
        "status": "online",
        "language": "hindi" if is_hindi(message) else "english",
        "conversation_history": conversation_history + [{"user": message}]
    }
    return response
