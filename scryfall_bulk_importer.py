import json


# https://scryfall.com/docs/api/bulk-data

def load_data(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

