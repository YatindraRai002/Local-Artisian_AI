import os
import csv
import re
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

artists_data = []
data_loaded = False


def format_phone_number(phone):
    if phone and "E+" in phone:
        try:
            num = float(phone)
            phone_str = str(round(num))
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
        artists_data = []

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)

            for row in reader:
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
                            [lang.strip().replace('"', "") for lang in row[8].split(",")]
                            if len(row) > 8 and row[8]
                            else []
                        ),
                        "contact": {
                            "email": row[9] if len(row) > 9 else "",
                            "phone": format_phone_number(row[10]) if len(row) > 10 else "",
                            "phone_available": (
                                row[11].lower() == "yes" if len(row) > 11 else False
                            ),
                        },
                        "government_id": row[12] if len(row) > 12 else "",
                        "cluster_code": row[13] if len(row) > 13 else "",
                    }
                    artists_data.append(artist)
                except Exception:
                    continue

        data_loaded = True
        print(f"✅ Loaded {len(artists_data)} artists for Hindi chat")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        artists_data = []


def process_hindi_query(message):
    hindi_patterns = {
        "greeting": re.compile(r"(नमस्ते|नमस्कार|हैलो)"),
        "search_pottery": re.compile(r"(कुम्हारी|मिट्टी.*बर्तन|pottery)", re.I),
        "search_embroidery": re.compile(r"(कढ़ाई|embroidery|चिकनकारी)", re.I),
        "search_weaving": re.compile(r"(बुनाई|कालीन|carpet|weaving)", re.I),
        "search_artisan": re.compile(r"(कारीगर|शिल्पकार|artisan|craftsman)", re.I),
        "search_metalwork": re.compile(r"(धातु.*काम|metalwork|metal)", re.I),
        "search_woodcarving": re.compile(r"(लकड़ी.*काम|wood.*carving)", re.I),
        "search_leather": re.compile(r"(चमड़ा.*काम|leather.*craft|leather)", re.I),
        "search_bamboo": re.compile(r"(बांस.*काम|bamboo|cane)", re.I),
    }

    intent = "general_query"
    entities = {}

    for key, pattern in hindi_patterns.items():
        if pattern.search(message):
            if key.startswith("search_"):
                intent = "search_craft"
                entities["craft_type"] = key.replace("search_", "").replace("_", " ")
            elif key == "greeting":
                intent = "greeting"
            elif key == "search_artisan":
                intent = "search_artisan"
            break

    # detect state
    state_names = [
        {"hindi": ["राजस्थान", "rajasthan"], "english": "rajasthan"},
        {"hindi": ["गुजरात", "gujarat"], "english": "gujarat"},
        {"hindi": ["उत्तर प्रदेश", "uttar pradesh", "up"], "english": "uttar pradesh"},
        {"hindi": ["बिहार", "bihar"], "english": "bihar"},
        {"hindi": ["केरल", "kerala", "kerela"], "english": "kerala"},
        {"hindi": ["तमिल नाडु", "tamil nadu"], "english": "tamil nadu"},
        {"hindi": ["महाराष्ट्र", "maharashtra"], "english": "maharashtra"},
        {"hindi": ["पश्चिम बंगाल", "west bengal", "bengal"], "english": "west bengal"},
        {"hindi": ["कर्नाटक", "karnataka"], "english": "karnataka"},
        {"hindi": ["मध्य प्रदेश", "madhya pradesh", "mp"], "english": "madhya pradesh"},
        {"hindi": ["हरियाणा", "haryana"], "english": "haryana"},
        {"hindi": ["पंजाब", "punjab"], "english": "punjab"},
        {"hindi": ["हिमाचल प्रदेश", "himachal pradesh"], "english": "himachal pradesh"},
        {"hindi": ["जम्मू कश्मीर", "jammu kashmir"], "english": "jammu & kashmir"},
        {"hindi": ["उड़ीसा", "ओडिशा", "odisha", "orissa"], "english": "odisha"},
        {"hindi": ["तेलंगाना", "telangana"], "english": "telangana"},
        {"hindi": ["आंध्र प्रदेश", "andhra pradesh"], "english": "andhra pradesh"},
    ]

    msg_lower = message.lower()
    for state in state_names:
        if any(name in msg_lower for name in state["hindi"]):
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
        loc = entities["location"].lower()
        results = [a for a in results if loc in a["location"]["state"].lower()]
    return results[:10]


def generate_response(message, intent, entities, artists):
    is_hindi = bool(re.search(r"[\u0900-\u097F]", message))

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

    lang = "hindi" if is_hindi else "english"

    if intent == "greeting":
        msg = random.choice(responses[lang]["greeting"])
    elif intent in ("search_craft", "search_artisan"):
        msg = responses[lang]["found_artisans"] if artists else responses[lang]["no_artisans"]
    else:
        msg = responses[lang]["general"]

    return {
        "message": msg,
        "language": lang,
        "intent": intent,
        "entities": entities,
        "artisans": artists,
        "suggestions": (
            ["कुम्हारी कारीगर दिखाओ", "राजस्थान में शिल्पकार", "चिकनकारी के बारे में बताओ", "आंकड़े दिखाओ"]
            if lang == "hindi"
            else ["Show pottery artisans", "Find crafts in Rajasthan", "Tell me about Chikankari", "Show statistics"]
        ),
    }


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS,PATCH,DELETE,POST,PUT"
    response.headers[
        "Access-Control-Allow-Headers"
    ] = "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version"
    return response


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat_handler():
    if request.method == "OPTIONS":
        return ("", 200)
    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405

    try:
        load_artists_data()
        data = request.get_json(force=True)
        message = data.get("message", "")
        _ = data.get("conversation_history", [])

        intent, entities = process_hindi_query(message)
        artists = search_artisans(entities) if intent in ("search_craft", "search_artisan") else []

        response = generate_response(message, intent, entities, artists)
        response["llm_message"] = "Enhanced Hindi NLP processing with multilingual support (Flask deployment)"
        response["status"] = "online"

        if intent == "get_stats":
            response["stats"] = {
                "total_artists": len(artists_data),
                "unique_crafts": len(set(a["craft_type"] for a in artists_data)),
                "unique_states": len(set(a["location"]["state"] for a in artists_data)),
                "unique_districts": len(set(a["location"]["district"] for a in artists_data)),
                "hindi_speakers": sum(
                    1
                    for a in artists_data
                    if any("hindi" in lang.lower() for lang in a["languages"])
                ),
            }

        return jsonify(response)

    except Exception as e:
        print(f"❌ Hindi Chat API error: {e}")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "क्षमा करें, कुछ त्रुटि हुई है। / Sorry, an error occurred.",
                    "status": "error",
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(debug=True)
