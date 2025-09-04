from flask import Flask, request, jsonify
import csv
import os

app = Flask(__name__)

artists_data = []
data_loaded = False

def parse_csv_line(line):
    # Simple CSV line parser
    result = []
    current = ''
    in_quotes = False
    i = 0
    while i < len(line):
        char = line[i]
        next_char = line[i+1] if i+1 < len(line) else None
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
    if phone and "E+" in phone:
        try:
            num = float(phone)
            phone_str = str(int(round(num)))
            if phone_str.startswith("91") and len(phone_str) == 12:
                return "+" + phone_str
            return phone_str
        except:
            return phone
    return phone or ""

def load_artists_data():
    global data_loaded, artists_data
    if data_loaded:
        return

    try:
        csv_path = os.path.join("public", "Artisans.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        headers = lines[0].split(",")

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
                    "id": values[0],
                    "name": values[1],
                    "gender": values[2],
                    "age": int(values[3]) if values[3].isdigit() else 0,
                    "craft_type": values[4],
                    "location": {
                        "state": values[5] or "",
                        "district": values[6] or "",
                        "village": values[7] or ""
                    },
                    "languages": [lang.strip().replace('"','') for lang in values[8].split(",")] if values[8] else [],
                    "contact": {
                        "email": values[9] or "",
                        "phone": format_phone_number(values[10]),
                        "phone_available": values[11].lower() == "yes" if len(values) > 11 else False
                    },
                    "government_id": values[12] if len(values) > 12 else "",
                    "cluster_code": values[13] if len(values) > 13 else ""
                }
                artists_data.append(artist)
            except Exception as e:
                print(f"Error parsing line {i+1}: {e}")

        data_loaded = True
        print(f"Loaded {len(artists_data)} artists for Stats API")
    except Exception as e:
        print("Error loading CSV:", e)
        artists_data = []

@app.route("/stats", methods=["GET"])
def stats_handler():
    try:
        load_artists_data()

        stats = {
            "total_artists": len(artists_data),
            "unique_crafts": len(set(a["craft_type"] for a in artists_data)),
            "unique_states": len(set(a["location"]["state"] for a in artists_data)),
            "unique_districts": len(set(a["location"]["district"] for a in artists_data)),
            "status": "online"
        }
        return jsonify(stats)
    except Exception as e:
        print("Stats API error:", e)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
