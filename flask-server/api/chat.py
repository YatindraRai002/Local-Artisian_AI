from flask import Flask, request, jsonify
import csv
import os

app = Flask(__name__)

artists_data = []
data_loaded = False


def parse_csv_line(line):
    """Parse a CSV line manually to handle quotes and commas."""
    result = []
    current = ''
    in_quotes = False
    i = 0
    while i < len(line):
        char = line[i]
        next_char = line[i + 1] if i + 1 < len(line) else None

        if char == '"':
            if in_quotes and next_char == '"':
                current += '"'
                i += 1
            else:
                in_quotes = not in_quotes
        elif char == ',' and not in_quotes:
            result.append(current.strip())
            current = ''
        else:
            current += char
        i += 1
    result.append(current.strip())
    return result


def format_phone_number(phone):
    """Convert exponential or raw phone numbers into readable format."""
    if phone and "E+" in phone:
        try:
            num = float(phone)
            phone_str = str(int(round(num)))
            if len(phone_str) == 12 and phone_str.startswith("91"):
                return f"+{phone_str}"
            return phone_str
        except Exception:
            return phone
    return phone or ''


def load_artists_data():
    """Load artists data from CSV once."""
    global data_loaded, artists_data
    if data_loaded:
        return

    try:
        csv_path = os.path.join(os.getcwd(), "public", "Artisans.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        headers = parse_csv_line(lines[0])
        artists_data = []

        for i in range(1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue

            values = parse_csv_line(line)
            if len(values) < len(headers):
                continue

            try:
                artist = {
                    "id": values[0] if len(values) > 0 else "",
                    "name": values[1] if len(values) > 1 else "",
                    "gender": values[2] if len(values) > 2 else "",
                    "age": int(values[3]) if len(values) > 3 and values[3].isdigit() else 0,
                    "craft_type": values[4] if len(values) > 4 else "",
                    "location": {
                        "state": values[5] if len(values) > 5 else "",
                        "district": values[6] if len(values) > 6 else "",
                        "village": values[7] if len(values) > 7 else ""
                    },
                    "languages": [lang.strip().replace('"', '') for lang in values[8].split(",")] if len(values) > 8 and values[8] else [],
                    "contact": {
                        "email": values[9] if len(values) > 9 else "",
                        "phone": format_phone_number(values[10]) if len(values) > 10 else "",
                        "phone_available": values[11].lower() == "yes" if len(values) > 11 else False
                    },
                    "government_id": values[12] if len(values) > 12 else "",
                    "cluster_code": values[13] if len(values) > 13 else ""
                }
                artists_data.append(artist)
            except Exception as e:
                print(f"Error parsing line {i + 1}: {e}")

        data_loaded = True
        print(f"✅ Loaded {len(artists_data)} artists")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        artists_data = []


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat_handler():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return ("", 200, {
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS,PATCH,DELETE,POST,PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        })

    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405

    try:
        load_artists_data()
        body = request.json or {}
        message = body.get("message", "")
        conversation_history = body.get("conversation_history", [])
        lower_message = message.lower()

        # Detect Hindi
        is_hindi = any('\u0900' <= ch <= '\u097F' for ch in message)

        # === Place your Hindi/English patterns, state maps, craft maps, and search logic here ===
        # (Same as your Node.js implementation — I can port all that logic if you want.)

        # For now, just return a stub response
        response = {
            "intent": "general",
            "message": "This is where Hindi/English intent logic will go.",
            "artists": artists_data[:5],  # sample
            "status": "online",
            "language": "hindi" if is_hindi else "english",
            "conversation_history": conversation_history + [{"user": message}]
        }

        return jsonify(response)

    except Exception as e:
        print(f"Chat API error: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
