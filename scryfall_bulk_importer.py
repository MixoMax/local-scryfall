import json


# https://scryfall.com/docs/api/bulk-data

"""
Each card approximately has the following fields:

{
    "name": str
    "safe_name": str
    "file_name": str
    "released-at": str ("YYYY-MM-DD")
    "year": int
    "mana_cost": str | None (eg: "{2}{B}{R}", None)
    "cmc": float
    "type_line": str
    "oracle_text": str
    "power": float | str | None (eg: 3, 4, "X", None)
    "toughness": float | str | None (same as power)
    "loyalty": float | str | None (same as power)
    "colors": list[str] (eg: ["B", "R"] for black and red colors)
    "color_identity": list[str] (eg: ["B", "R"] for black and red color identity)
    "keywords": list[str] (eg: ["deathtouch", "flying"])
    "set": list[str] (list of set codes this cards has been printed in, eg: ["m21", "m22"])
    "rarity": str (eg: "common", "uncommon", "rare", "mythic")
    "edhrec_rank": int | None (eg: 1234, None)
    "price_euro": float | None (eg: 1.23, None)
    "price_usd": float | None (eg: 1.23, None)
    "legal_formats": list[str] (list of formats where the card is legal, eg: ["standard", "modern", "legacy"])
}
"""

def load_data(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

