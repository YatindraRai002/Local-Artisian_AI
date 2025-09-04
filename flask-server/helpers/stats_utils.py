from helpers.data_loader import load_artists_data

def get_stats():
    artists = load_artists_data()
    return {
        "total_artists": len(artists),
        "unique_crafts": len(set(a["craft_type"] for a in artists)),
        "unique_states": len(set(a["location"]["state"] for a in artists)),
        "unique_districts": len(set(a["location"]["district"] for a in artists)),
        "status": "online"
    }

def find_similar_artists(artist_id, limit=5):
    artists = load_artists_data()
    target = next((a for a in artists if str(a["id"]) == str(artist_id)), None)
    if not target:
        return []

    def is_similar(a):
        if str(a["id"]) == str(artist_id):
            return False
        return a["craft_type"] == target["craft_type"] or a["location"]["state"] == target["location"]["state"]

    similar = [a for a in artists if is_similar(a)]
    return similar[:limit]
