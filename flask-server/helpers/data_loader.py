import csv
import os

_artists_cache = None

def load_artists_data():
    global _artists_cache
    if _artists_cache is not None:
        return _artists_cache

    csv_path = os.path.join(os.path.dirname(__file__), "..", "public", "Artisans.csv")
    artists_data = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        headers = lines[0].split(",")

        for line in lines[1:]:
            values = line.split(",")
            if len(values) < len(headers):
                continue
            artist = {
                "id": values[0],
                "name": values[1],
                "gender": values[2],
                "age": int(values[3]) if values[3].isdigit() else 0,
                "craft_type": values[4],
                "location": {"state": values[5], "district": values[6], "village": values[7]},
                "languages": [lang.strip() for lang in values[8].split(",")] if values[8] else [],
                "contact": {"email": values[9], "phone": values[10], "phone_available": values[11].lower() == "yes"},
                "government_id": values[12] if len(values) > 12 else "",
                "cluster_code": values[13] if len(values) > 13 else ""
            }
            artists_data.append(artist)
    except Exception as e:
        print(f"Error loading CSV: {e}")

    _artists_cache = artists_data
    return _artists_cache
