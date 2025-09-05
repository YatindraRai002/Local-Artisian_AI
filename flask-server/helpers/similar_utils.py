from helpers.data_loader import load_artists_data

def find_similar(args):
    artist_id = args.get("artistId")
    limit = int(args.get("limit", 5))
    data = load_artists_data()

    target = None
    for a in data:
        if str(a["id"]) == str(artist_id):
            target = a
            break
    if not target:
        return {"error": "Artist not found"}, 404

    similar = [a for a in data if a["craft_type"] == target["craft_type"] and a["id"] != target["id"]]
    return {"similar_artists": similar[:limit], "total_found": len(similar), "target_artist": target}
