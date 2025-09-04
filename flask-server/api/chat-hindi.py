import os
import csv
import re
import random

_artists_data = None

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
    global _artists_data
    if _artists_data is not None:
        return _artists_data

    csv_path = os.path.join(os.path.dirname(__file__), "..", "public", "Artisans.csv")
    artists_data = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
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
                            "phone_available": row[11].lower() == "yes" if len(row) > 11 else False,
                        },
                        "government_id": row[12] if len(row) > 12 else "",
                        "cluster_code": row[13] if len(row) > 13 else "",
                    }
                    artists_data.append(artist)
                except Exception:
                    continue
    except Exception as e:
        print(f"Error loading CSV: {e}")

    _artists_data = artists_data
    return _artists_data

# Hindi query processing
def process_hindi_query(message):
    """Returns (intent, entities)"""
    # (copy all your regex-based logic here)
    # Return intent, entities
    ...

def search_artisans(entities):
    """Return a list of matching artisans"""
    artists = load_artists_data()
    results = artists
    if "craft_type" in entities:
        craft_filter = entities["craft_type"].lower()
        results = [a for a in results if craft_filter in a["craft_type"].lower()]
    if "location" in entities:
        loc = entities["location"].lower()
        results = [a for a in results if loc in a["location"]["state"].lower()]
    return results[:10]

def generate_response(message, intent, entities, artists):
    """Return JSON response dictionary"""
    # (copy your response generation logic)
    ...
