import os
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

artists_data = []
data_loaded = False

# ---------------- CSV parsing helpers ---------------- #

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
        print(f"Loaded {len(artists_data)} artists for Flask deployment")

    except Exception as e:
        print("Error loading CSV:", e)
        artists_data = []


# ---------------- State mapping ---------------- #

state_mapping = {
    "andhra pradesh": ["andhra pradesh", "ap", "andhra"],
    "arunachal pradesh": ["arunachal pradesh", "arunachal"],
    "assam": ["assam"],
    "bihar": ["bihar"],
    "chhattisgarh": ["chhattisgarh", "chattisgarh", "cg"],
    "goa": ["goa"],
    "gujarat": ["gujarat", "gj"],
    "haryana": ["haryana", "hr"],
    "himachal pradesh": ["himachal pradesh", "himachal", "hp", "h.p."],
    "jammu & kashmir": ["jammu & kashmir", "jammu and kashmir", "jammu kashmir", "j&k", "jk", "kashmir", "jammu"],
    "jharkhand": ["jharkhand", "jh"],
    "karnataka": ["karnataka", "kn", "mysore"],
    "kerala": ["kerala", "kl", "kerela"],
    "madhya pradesh": ["madhya pradesh", "mp", "m.p.", "central pradesh"],
    "maharashtra": ["maharashtra", "mh"],
    "manipur": ["manipur", "mn"],
    "meghalaya": ["meghalaya", "ml"],
    "mizoram": ["mizoram", "mz"],
    "nagaland": ["nagaland", "nl"],
    "odisha": ["odisha", "orissa", "or"],
    "punjab": ["punjab", "pb"],
    "rajasthan": ["rajasthan", "rj"],
    "sikkim": ["sikkim", "sk"],
    "tamil nadu": ["tamil nadu", "tamilnadu", "tamil naidu", "tn"],
    "telangana": ["telangana", "ts"],
    "tripura": ["tripura", "tr"],
    "uttar pradesh": ["uttar pradesh", "up", "u.p."],
    "uttarakhand": ["uttarakhand", "uttaranchal", "uk", "ua"],
    "west bengal": ["west bengal", "bengal", "wb"],
    "ladakh": ["ladakh"],
    "delhi": ["delhi", "new delhi", "dl"],
    "chandigarh": ["chandigarh", "ch"],
    "puducherry": ["puducherry", "pondicherry", "py"],
    "andaman and nicobar islands": ["andaman", "nicobar", "andaman and nicobar", "an"],
    "dadra and nagar haveli": ["dadra", "nagar haveli", "dadra and nagar haveli", "dn"],
    "daman and diu": ["daman", "diu", "daman and diu", "dd"],
    "lakshadweep": ["lakshadweep", "ld"],
}


def match_state(search_state, artist_state):
    if not search_state or not artist_state:
        return False

    search_lower = search_state.lower().strip()
    artist_lower = artist_state.lower().strip()

    # direct match
    if artist_lower in search_lower or search_lower in artist_lower:
        return True

    # check against state variations
    for canonical, variations in state_mapping.items():
        search_matches = any(
            search_lower == v or search_lower in v or v in search_lower for v in variations
        )
        artist_matches = any(
            artist_lower == v or artist_lower in v or v in artist_lower for v in variations
        ) or canonical in artist_lower or artist_lower in canonical
        if search_matches and artist_matches:
            return True

    # normalize "&"
    search_norm = search_lower.replace("&", "and").replace("  ", " ")
    artist_norm = artist_lower.replace("&", "and").replace("  ", " ")
    return search_norm in artist_norm or artist_norm in search_norm


def get_available_states():
    if not artists_data:
        return []
    states = {a["location"]["state"] for a in artists_data if a["location"]["state"]}
    return sorted(states)


def get_search_statistics(filtered):
    if not filtered:
        return {}

    return {
        "total_artists": len(filtered),
        "unique_states": len({a["location"]["state"] for a in filtered}),
        "unique_districts": len({a["location"]["district"] for a in filtered}),
        "unique_crafts": len({a["craft_type"] for a in filtered}),
        "unique_clusters": len({a["cluster_code"] for a in filtered}),
        "states_found": sorted({a["location"]["state"] for a in filtered}),
        "crafts_found": sorted({a["craft_type"] for a in filtered}),
        "age_range": {
            "min": min(a["age"] for a in filtered),
            "max": max(a["age"] for a in filtered),
        },
    }


# ---------------- API handler ---------------- #

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS,PATCH,DELETE,POST,PUT"
    response.headers["Access-Control-Allow-Headers"] = (
        "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, "
        "Content-Length, Content-MD5, Content-Type, Date, X-Api-Version"
    )
    return response


@app.route("/api/search", methods=["POST", "OPTIONS"])
def search_handler():
    if request.method == "OPTIONS":
        return make_response("", 200)

    if request.method != "POST":
        return jsonify({"error": "Method not allowed"}), 405

    try:
        load_artists_data()
        filters = request.get_json() or {}
        filtered = list(artists_data)

        # state
        if "state" in filters:
            filtered = [a for a in filtered if match_state(filters["state"], a["location"]["state"])]

        # district
        if "district" in filters:
            sd = filters["district"].lower().strip()
            filtered = [a for a in filtered if sd in a["location"]["district"].lower()]

        # craft
        if "craft_type" in filters:
            sc = filters["craft_type"].lower().strip()
            filtered = [a for a in filtered if sc in a["craft_type"].lower()]

        # name
        if "name" in filters:
            sn = filters["name"].lower().strip()
            filtered = [a for a in filtered if sn in a["name"].lower()]

        # language
        if "language" in filters:
            sl = filters["language"].lower().strip()
            filtered = [a for a in filtered if any(sl in l.lower() for l in a["languages"])]

        # cluster
        if "cluster_code" in filters:
            sc = filters["cluster_code"].lower()
            filtered = [a for a in filtered if sc in a["cluster_code"].lower()]

        # age
        if "age_min" in filters:
            filtered = [a for a in filtered if a["age"] >= filters["age_min"]]
        if "age_max" in filters:
            filtered = [a for a in filtered if a["age"] <= filters["age_max"]]

        # gender
        if "gender" in filters:
            sg = filters["gender"].lower()
            filtered = [a for a in filtered if a["gender"].lower() == sg]

        # phone availability
        if "phone_available" in filters:
            want = filters["phone_available"]
            filtered = [a for a in filtered if a["contact"]["phone_available"] == want]

        # sorting
        if "sort_by" in filters:
            sort_field = filters["sort_by"]
            order = filters.get("sort_order", "asc")

            def key_func(a):
                if sort_field == "name":
                    return a["name"].lower()
                elif sort_field == "age":
                    return a["age"]
                elif sort_field == "state":
                    return a["location"]["state"].lower()
                elif sort_field == "craft":
                    return a["craft_type"].lower()
                return ""

            reverse = order == "desc"
            filtered.sort(key=key_func, reverse=reverse)

        # pagination
        limit = filters.get("limit", 20)
        offset = filters.get("offset", 0)
        results = filtered[offset : offset + limit]

        response = {
            "artists": results,
            "total": len(filtered),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(filtered),
            "status": "online",
            "search_metadata": {
                "filters_applied": [
                    k for k in filters.keys() if k not in ["limit", "offset", "sort_by", "sort_order"]
                ],
                "available_states": get_available_states(),
                "search_statistics": get_search_statistics(filtered),
            },
        }

        # suggestions
        if "state" in filters and not filtered:
            suggestions = [
                s
                for s in get_available_states()
                if filters["state"].lower() in s.lower()
                or any(filters["state"].lower() in v for v in sum(state_mapping.values(), []))
            ]
            response["suggestions"] = {
                "message": f'No artists found for "{filters["state"]}". Did you mean:',
                "states": suggestions[:5],
            }

        return jsonify(response)

    except Exception as e:
        print("Search API error:", e)
        return jsonify(
            {
                "error": "Internal server error",
                "message": str(e),
                "available_states": get_available_states() if artists_data else [],
            }
        ), 500


if __name__ == "__main__":
    app.run(debug=True)
