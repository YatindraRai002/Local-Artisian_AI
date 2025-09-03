from flask import Flask, request, jsonify
import os

app = Flask(__name__)

artists_data = []
data_loaded = False

def parse_csv_line(line):
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
    if phone and 'E+' in phone:
        try:
            num = float(phone)
            phone_str = str(int(round(num)))
            if len(phone_str) == 12 and phone_str.startswith("91"):
                return f"+{phone_str}"
            return phone_str
        except:
            return phone
    return phone or ''

def load_artists_data():
    global artists_data, data_loaded
    if data_loaded:
        return

    try:
        csv_path = os.path.join(os.getcwd(), "public", "Artisans.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        headers = lines[0].split(",")
        artists_data = []

        for i, line in enumerate(lines[1:], start=2):
            line = line.strip()
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
                    "contact": {
                        "email": values[9] if len(values) > 9 else "",
                        "phone": format_phone_number(values[10]) if len(values) > 10 else "",
                        "phone_available": values[11].lower() == "yes" if len(values) > 11 else False
                    },
                    "languages": values[8].replace('"', '').split(",") if values[8] else [],
                    "government_id": values[12] if len(values) > 12 else "",
                    "cluster_code": values[13] if len(values) > 13 else ""
                }
                artists_data.append(artist)
            except Exception as e:
                print(f"Error parsing line {i}: {e}")

        data_loaded = True
        print(f"Loaded {len(artists_data)} artists for similar API")

    except Exception as e:
        print("Error loading CSV:", e)
        artists_data = []


@app.route("/api/similar", methods=["GET", "OPTIONS"])
def similar_artists_handler():
    # Set CORS headers
    response_headers = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,OPTIONS,PATCH,DELETE,POST,PUT",
        "Access-Control-Allow-Headers": "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version"
    }

    if request.method == "OPTIONS":
        return ("", 200, response_headers)

    if request.method != "GET":
        return (jsonify({"error": "Method not allowed"}), 405, response_headers)

    try:
        load_artists_data()

        artist_id = request.args.get("artistId")
        limit = int(request.args.get("limit", 5))

        if not artist_id:
            return (jsonify({"error": "Artist ID is required"}), 400, response_headers)

        target_artist = next((a for a in artists_data if a["id"] == artist_id), None)
        if not target_artist:
            return (jsonify({"error": "Artist not found"}), 404, response_headers)

        # Find similar artists
        similar_artists = []
        for a in artists_data:
            if a["id"] == artist_id:
                continue
            if a["craft_type"] == target_artist["craft_type"]:
                similar_artists.append(a)
            elif a["location"]["state"] == target_artist["location"]["state"]:
                similar_artists.append(a)
            elif a.get("cluster_code") and target_artist.get("cluster_code") and a["cluster_code"] == target_artist["cluster_code"]:
                similar_artists.append(a)

        # Sort by similarity: craft > state
        def sort_key(artist):
            if artist["craft_type"] == target_artist["craft_type"]:
                return (0, artist["location"]["state"])
            elif artist["location"]["state"] == target_artist["location"]["state"]:
                return (1, artist["location"]["state"])
            else:
                return (2, artist["location"]["state"])

        similar_artists.sort(key=sort_key)

        response_data = {
            "similar_artists": similar_artists[:limit],
            "total_found": len(similar_artists),
            "target_artist": target_artist,
            "status": "online"
        }

        return (jsonify(response_data), 200, response_headers)

    except Exception as e:
        print("Similar artists API error:", e)
        return (jsonify({"error": "Internal server error"}), 500, response_headers)


if __name__ == "__main__":
    app.run(debug=True)
