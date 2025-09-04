import os
import csv

_artists_cache = None

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
    """Load and cache artists from CSV"""
    global _artists_cache
    if _artists_cache is not None:
        return _artists_cache

    csv_path = os.path.join(os.getcwd(), "public", "Artisans.csv")
    artists = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        headers = lines[0].split(",")

        for line in lines[1:]:
            values = [v.strip() for v in line.split(",")]
            if len(values) < len(headers):
                continue
            artist = {
                "id": values[0],
                "name": values[1],
                "gender": values[2],
                "age": int(values[3]) if values[3].isdigit() else 0,
                "craft_type": values[4],
                "location": {
                    "state": values[5] if len(values) > 5 else "",
                    "district": values[6] if len(values) > 6 else "",
                    "village": values[7] if len(values) > 7 else ""
                },
                "languages": [l.strip() for l in values[8].split(",")] if len(values) > 8 and values[8] else [],
                "contact": {
                    "email": values[9] if len(values) > 9 else "",
                    "phone": format_phone_number(values[10]) if len(values) > 10 else "",
                    "phone_available": values[11].lower() == "yes" if len(values) > 11 else False
                },
                "government_id": values[12] if len(values) > 12 else "",
                "cluster_code": values[13] if len(values) > 13 else ""
            }
            artists.append(artist)
    except Exception as e:
        print("Error loading CSV:", e)

    _artists_cache = artists
    return artists
