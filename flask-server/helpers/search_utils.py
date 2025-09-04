from helpers.data_loader import load_artists_data

def filter_artists(filters):
    artists = load_artists_data()
    results = artists.copy()

    # Filter by craft_type
    if "craft_type" in filters:
        results = [a for a in results if filters["craft_type"].lower() in a["craft_type"].lower()]

    # Filter by state
    if "state" in filters:
        results = [a for a in results if filters["state"].lower() in a["location"]["state"].lower()]

    # Filter by district
    if "district" in filters:
        results = [a for a in results if filters["district"].lower() in a["location"]["district"].lower()]

    # Filter by gender
    if "gender" in filters:
        results = [a for a in results if a["gender"].lower() == filters["gender"].lower()]

    # Filter by phone availability
    if "phone_available" in filters:
        results = [a for a in results if a["contact"]["phone_available"] == filters["phone_available"]]

    return results
