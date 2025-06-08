import json


# https://scryfall.com/docs/api/bulk-data

def load_data(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    for card in data:
        card["year"] = card.get("released_at", "").split("-")[0] if card.get("released_at") else None

    return data

