import os
import csv
import re
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

artists_data = []
data_loaded = False


def format_phone_number(phone: str) -> str:
    if phone and "E+" in phone:
        try:
            num = int(float(phone))
            phone_str = str(num)
            if len(phone_str) == 12 and phone_str.startswith("91"):
                return f"+{phone_str}"
            return phone_str
        except ValueError:
            return phone
    return phone or ""


def load_artists_data():
    global artists_data, data_loaded
    if data_loaded:
        return

    try:
        csv_path = os.path.join(os.getcwd(), "public", "Artisans.csv")
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)

            artists_data = []
            for i, row in enumerate(reader, start=2):
                if not row or len(row) < len(headers):
                    continue
                try:
                    artist = {
                        "id": row[0] if len(row) > 0 else "",
                        "name": row[1] if len(row) > 1 else "",
                        "gender": row[2] if len(row) > 2 else "",
                        "age": int(row[3]) if len(row) > 3 and row[3].isdigit() else 0,
                        "craft_type": row[4] if len(row) > 4 else "",
                        "location": {
                            "state": row[5] if len(row) > 5 else "",
                            "district": row[6] if len(row) > 6 else "",
                            "village": row[7] if len(row) > 7 else "",
                        },
                        "languages": (
                            [lang.strip().replace('"', '') for lang in row[8].split(",")]
                            if len(row) > 8 and row[8]
                            else []
                        ),
                        "contact": {
                            "email": row[9] if len(row) > 9 else "",
                            "phone": format_phone_number(row[10] if len(row) > 10 else ""),
                            "phone_available": (
                                row[11].lower() == "yes" if len(row) > 11 else False
                            ),
                        },
                        "government_id": row[12] if len(row) > 12 else "",
                        "cluster_code": row[13] if len(row) > 13 else "",
                    }
                    artists_data.append(artist)
                except Exception as e:
                    print(f"⚠️ Error parsing line {i}: {e}")
        data_loaded = True
        print(f"✅ Loaded {len(artists_data)} artisans for Hindi/English chat")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        artists_data = []


def process_hindi_query(message: str):
    hindi_patterns = {
        "greeting": re.compile(r"(नमस्ते|नमस्कार|हैलो)"),
        "search_pottery": re.compile(r"(कुम्हारी|मिट्टी.*बर्तन|pottery)", re.I),
        "search_embroidery": re.compile(r"(कढ़ाई|embroidery|चिकनकारी)", re.I),
        "search_weaving": re.compile(r"(बुनाई|कालीन|carpet|weaving)", re.I),
        "search_artisan": re.compile(r"(कारीगर|शिल्पकार|artisan|craftsman)", re.I),
        "search_metalwork": re.compile(r"(धातु.*काम|metalwork|metal)", re.I),
        "search_woodcarving": re.compile(r"(लकड़ी.*काम|wood.*carving|carving)", re.I),
        "search_leather": re.compile(r"(चमड़ा.*काम|leather.*craft|leather)", re.I),
        "search_bamboo": re.compile(r"(बांस.*काम|bamboo|cane)", re.I),
    }

    intent = "general_query"
    entities = {}

    for key, pattern in hindi_patterns.items():
        if pattern.search(message):
            if "search" in key:
                intent = "search_craft"
                entities["craft_type"] = key.replace("search_", "").replace("_", " ")
            elif key == "greeting":
                intent = "greeting"
            break

    state_names = [
        {"hindi": ["राजस्थान", "rajasthan"], "english": "rajasthan"},
        {"hindi": ["गुजरात", "gujarat"], "english": "gujarat"},
        {"hindi": ["उत्तर प्रदेश", "uttar pradesh", "up"], "english": "uttar pradesh"},
        {"hindi": ["बिहार", "bihar"], "english": "bihar"},
        {"hindi": ["केरल", "kerala"], "english": "kerala"},
        {"hindi": ["तमिल नाडु", "tamil nadu"], "english": "tamil nadu"},
        {"hindi": ["महाराष्ट्र", "maharashtra"], "english": "maharashtra"},
        {"hindi": ["पश्चिम बंगाल", "west bengal"], "english": "west bengal"},
        {"hindi": ["कर्नाटक", "karnataka"], "english": "karnataka"},
        {"hindi": ["मध्य प्रदेश", "madhya pradesh", "mp"], "english": "madhya pradesh"},
    ]

    message_lower = message.lower()
    for state in state_names:
        if any(name in message_lower for name in state["hindi"]):
            entities["location"] = state["english"]
            break

    return intent, entities


def search_artisans(entities):
    results = artists_data
    if "craft_type" in entities:
        craft_filter = entities["craft_type"].lower()
        results = [
            a
            for a in results
            if craft_filter in a["craft_type"].lower()
        ]
    if "location" in entities:
        location = entities["location"].lower()
        results = [a for a in results if location in a["location"]["state"].lower()]
    return results[:10]


def generate_response(message, intent, entities, artists):
    is_hindi = bool(re.search(r"[\u0900-\u097F]", message))
    lang = "hindi" if is_hindi else "english"

    responses = {
        "hindi": {
            "greeting": [
                "नमस्ते! मैं आपकी पारंपरिक कारीगरों की खोज में मदद कर सकता हूँ।",
                "नमस्कार! आप किस प्रकार के शिल्पकार की तलाश में हैं?",
                "आपका स्वागत है! मैं भारतीय हस्तशिल्प कारीगरों के बारे में जानकारी दे सकता हूँ।",
            ],
            "found_artisans": f"मुझे {len(artists)} कारीगर मिले हैं।",
            "no_artisans": "क्षमा करें, इस खोज के लिए कोई कारीगर नहीं मिला।",
            "general": "मैं आपकी कैसे मदद कर सकता हूँ? आप कारीगरों के बारे में पूछ सकते हैं।",
        },
        "english": {
            "greeting": [
                "Hello! I can help you find traditional Indian artisans.",
                "Welcome! What type of craftsperson are you looking for?",
                "Hi there! I can provide information about Indian handicraft artisans.",
            ],
            "found_artisans": f"I found {len(artists)} artisans matching your criteria.",
            "no_artisans": "Sorry, no artisans found for this search.",
            "general": "How can I help you? You can ask about artisans and crafts.",
        },
    }

    if intent == "greeting":
        response_text = random.choice(responses[lang]["greeting"])
    elif intent in ["search_craft", "search_artisan"]:
        response_text = (
            responses[lang]["found_artisans"]
            if artists
            else responses[lang]["no_artisans"]
        )
    else:
        response_text = responses[lang]["general"]

    return {
        "message": response_text,
        "language": lang,
        "intent": intent,
        "entities": entities,
        "artisans": artists,
        "suggestions": [
            "कुम्हारी कारीगर दिखाओ",
            "राजस्थान में शिल्पकार",
            "चिकनकारी के बारे में बताओ",
        ]
        if is_hindi
        else [
            "Show pottery artisans",
            "Find crafts in Rajasthan",
            "Tell me about Chikankari",
        ],
        "status": "online",
    }


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat_handler():
    if request.method == "OPTIONS":
        return ("", 200, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        })

    try:
        load_artists_data()
        data = request.json or {}
        message = data.get("message", "")

        intent, entities = process_hindi_query(message)
        artists = search_artisans(entities) if intent.startswith("search") else []

        response = generate_response(message, intent, entities, artists)
        response["llm_message"] = "Enhanced Hindi NLP with multilingual support (Flask deployment)"
        response["stats"] = {
            "total_artists": len(artists_data),
            "unique_crafts": len(set(a["craft_type"] for a in artists_data)),
            "unique_states": len(set(a["location"]["state"] for a in artists_data)),
        }

        return jsonify(response)
    except Exception as e:
        print("❌ Chat API error:", e)
        return jsonify({
            "error": "Internal server error",
            "message": "क्षमा करें, कुछ त्रुटि हुई है। / Sorry, an error occurred.",
            "status": "error",
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
