from helpers.data_loader import load_artists_data

def apply_filters(filters):
    df = load_artists_data()
    results = df

    # Example: filter by craft_type
    craft = filters.get("craft_type")
    if craft:
        results = [a for a in results if craft.lower() in a["craft_type"].lower()]

    # Limit results
    limit = filters.get("limit", 20)
    return {"artists": results[:limit], "total": len(results)}
