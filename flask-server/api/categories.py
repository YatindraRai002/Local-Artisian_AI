import os
import csv
from flask import Flask, jsonify, request

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
            headers = next(reader, None)  # first row headers

            for row in reader:
                if not row or len(row) < len(headers):
                    continue
                try:
                    artist = {
                        "id": row[0],
                        "name": row[1],
                        "gender": row[2],
                        "age": int(row[3]) if row[3].isdigit() else 0,
                        "craft_type": row[4],
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
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue

        data_loaded = True
    except Exception as e:
        print(f"Error loading CSV: {e}")
        artists_data = []


@app.after_request
def add_cors_headers(response):
    """Set CORS headers like in your Vercel handler"""
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS,PATCH,DELETE,POST,PUT"
    response.headers[
        "Access-Control-Allow-Headers"
    ] = "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version"
    return response


@app.route("/categories", methods=["GET", "OPTIONS"])
def categories_handler():
    if request.method == "OPTIONS":
        return ("", 200)

    if request.method != "GET":
        return jsonify({"error": "Method not allowed"}), 405

    try:
        load_artists_data()

        crafts = sorted(set([a["craft_type"] for a in artists_data]))
        states = sorted(set([a["location"]["state"] for a in artists_data]))

        return jsonify({
            "crafts": crafts,
            "states": states,
            "status": "online",
        })
    except Exception as e:
        print(f"Categories API error: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
