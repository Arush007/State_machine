PLANT_CACHE = {
    "stamping press on line 1": {"AssetID": 4021},
    "kuka welding robot on line 2": {"AssetID": 1042},
    "conveyor belt line 3": {"AssetID": 8819}
}

def fetch_cag_context(user_query: str) -> str:
    query_lower = user_query.lower()
    matched = []
    for key, data in PLANT_CACHE.items():
        if key in query_lower:
            matched.append(f"Literal context match: '{key}' maps strictly to Key ID: {data['AssetID']}")
    return "\n".join(matched) if matched else "No explicit active asset indices detected."