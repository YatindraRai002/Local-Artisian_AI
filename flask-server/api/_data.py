import os
import csv

# Cache loaded data
_artists_cache = None

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

def _load_csv():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "..", "public", "Artisans.csv")

    artists_data = []

    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)

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
                            "village": row[7] if len(row) > 7 else ""
                        },
                        "languages": [lang.strip().replace('"', '') for lang in row[8].split(",")] if len(row) > 8 and row[8] else [],
                        "contact": {
                            "email": row[9] if len(row) > 9 else "",
                            "phone": format_phone_number(row[10]) if len(row) > 10 else "",
                            "phone_available": row[11].lower() == "yes" if len(row) > 11 else False
                        },
                        "government_id": row[12] if len(row) > 12 else "",
                        "cluster_code": row[13] if len(row) > 13 else ""
                    }
                    artists_data.append(artist)
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
    except Exception as e:
        print(f"Error reading CSV: {e}")

    return artists_data

def load_csv_data():
    global _artists_cache
    if _artists_cache is None:
        _artists_cache = _load_csv()
    return _artists_cache
