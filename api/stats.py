import os
import csv
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

artists_data = []
data_loaded = False


def parse_csv_line(line):
    # Python's csv module handles quoted values properly, so this is simpler
    reader = csv.reader([line])
    return next(reader)


def format_phone_number(phone):
    if phone and "E+" in phone:
        try:
            num = float(phone)
            phone_str = str(int(round(num)))
            if len(phone_str) == 12 and phone_str.startswith("91"):
                return f"+{phone_str}"
            return phone_str
        except ValueError:
            return phone
    return phone or ""


def load_artists_data():
    global data_loaded, artists_data
    if data_loaded:
        return

    try:
        csv_path = os.path.join(os.getcwd(), "public", "Artisans.csv")
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            lines = csvfile.read().splitlines()

        headers = parse_csv_line(lines[0])
        artists_data = []

        for i, line in enumerate(lines[1:], start=2):
            if not line.strip():
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
                    "languages": (
                        [lang.strip().replace('"', "") for lang in values[8].split(",")]
                        if len(values) > 8 and values[8]
                        else []
                    ),
                    "contact": {
                        "email": values[9] if len(values) > 9 else "",
                        "phone": format_phone_number(values[10]) if len(values) > 10 else "",
                        "phone_available": (
                            values[11].lower() == "yes" if len(values) > 11 else False
                        ),
                    },
                    "government_id": values[12] if len(values) > 12 else "",
                    "cluster_code": values[13] if len(values) > 13 else "",
                }

                artists_data.append(artist)
            except Exception as e:
                print(f"Error parsing line {i}: {e}")

        data_loaded = True

    except Exception as e:
        print("Error loading CSV:", e)
        artists_data = []


@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS,PATCH,DELETE,POST,PUT"
    response.headers[
        "Access-Control-Allow-Headers"
    ] = "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version"
    return response


@app.route("/api/stats", methods=["GET", "OPTIONS"])
def stats_handler():
    if request.method == "OPTIONS":
        return make_response("", 200)

    if request.method != "GET":
        return jsonify({"error": "Method not allowed"}), 405

    try:
        load_artists_data()

        stats = {
            "total_artists": len(artists_data),
            "unique_crafts": len(set(a["craft_type"] for a in artists_data)),
            "unique_states": len(set(a["location"]["state"] for a in artists_data)),
            "unique_districts": len(set(a["location"]["district"] for a in artists_data)),
            "status": "online",
        }

        return jsonify(stats)
    except Exception as e:
        print("Stats API error:", e)
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
