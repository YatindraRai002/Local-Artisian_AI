from helpers.data_loader import load_artists_data

def get_stats():
    data = load_artists_data()
    total = len(data)
    crafts = len(set(a["craft_type"] for a in data))
    states = len(set(a["location"]["state"] for a in data))
    districts = len(set(a["location"]["district"] for a in data))
    return {
        "total_artists": total,
        "unique_crafts": crafts,
        "unique_states": states,
        "unique_districts": districts,
        "status": "online"
    }
