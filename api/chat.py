import os
from flask import Flask, request, jsonify, make_response

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
    if phone and "E+" in phone:
        try:
            num = float(phone)
            phone_str = str(int(round(num)))
            if len(phone_str) == 12 and phone_str.startswith("91"):
                return f"+{phone_str}"
            return phone_str
        except Exception:
            return phone
    return phone or ""


def load_artists_data():
    global artists_data, data_loaded
    if data_loaded:
        return

    try:
        csv_path = os.path.join(os.getcwd(), "public", "Artisans.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")

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
                        "state": values[5] if len(values) > 5 else "",
                        "district": values[6] if len(values) > 6 else "",
                        "village": values[7] if len(values) > 7 else "",
                    },
                    "contact": {
                        "email": values[9] if len(values) > 9 else "",
                        "phone": format_phone_number(values[10]) if len(values) > 10 else "",
                        "phone_available": (
                            values[11].lower() == "yes" if len(values) > 11 else False
                        ),
                    },
                    "languages": (
                        [lang.strip().replace('"', '') for lang in values[8].split(",")]
                        if len(values) > 8 and values[8]
                        else []
                    ),
                    "government_id": values[12] if len(values) > 12 else "",
                    "cluster_code": values[13] if len(values) > 13 else "",
                }

                artists_data.append(artist)
            except Exception as e:
                print(f"Error parsing line {i+1}: {e}")

        data_loaded = True
    except Exception as e:
        print("Error loading CSV in Flask:", e)
        artists_data = []


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers[
        "Access-Control-Allow-Methods"
    ] = "GET,OPTIONS,PATCH,DELETE,POST,PUT"
    response.headers[
        "Access-Control-Allow-Headers"
    ] = "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version"
    return response


@app.route("/api/categories", methods=["GET", "OPTIONS"])
def categories_handler():
    if request.method == "OPTIONS":
        return make_response("", 200)

    if request.method != "GET":
        return jsonify({"error": "Method not allowed"}), 405

    try:
        load_artists_data()
        crafts = list({a["craft_type"] for a in artists_data})
        states = list({a["location"]["state"] for a in artists_data})

        return jsonify(
            {
                "crafts": crafts,
                "states": states,
                "status": "online",
            }
        )
    except Exception as e:
        print("Categories API error:", e)
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
