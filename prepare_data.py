# %%
import json
import requests
from tqdm import tqdm
from PIL import Image

# %%
def card_name_to_file_name(card_name):
    card_name = card_name.replace(" ", "-")

    card_name = "".join([char for char in card_name if char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"])

    while "--" in card_name:
        card_name = card_name.replace("--", "-")
    while card_name.startswith("-"):
        card_name = card_name[1:]
    while card_name.endswith("-"):
        card_name = card_name[:-1]
    return card_name.strip("-").lower()

# %%
with open("./oracle-cards-20250608210949.json", "r") as f:
    cards = json.load(f)

# %%
data_out = []

for card in tqdm(cards):
    data_out.append({
        "name": card["name"],
        "safe_name": card_name_to_file_name(card["name"]),
        "file_name": card_name_to_file_name(card["name"] + "-" + card["type_line"]) + ".webp",
        "released-at": card["released_at"],
        "year": int(card["released_at"].split("-")[0]),
        "mana_cost": card.get("mana_cost", ""),
        "cmc": card.get("cmc", 0),
        "type_line": card.get("type_line", ""),
        "oracle_text": card.get("oracle_text", ""),
        "power": card.get("power", ""),
        "toughness": card.get("toughness", ""),
        "loyalty": card.get("loyalty", ""),
        "colors": card.get("colors", []),
        "color_identity": card.get("color_identity", []),
        "keywords": card.get("keywords", []),
        "set": card.get("set", ""),
        "rarity": card.get("rarity", ""),
        "edhrec_rank": card.get("edhrec_rank", 0),
        "price_euro": card.get("prices", {}).get("eur", 0.0),
        "price_usd": card.get("prices", {}).get("usd", 0.0),
        "legal_formats": [fmt_str for fmt_str, legal in card.get("legalities", {}).items() if legal == "legal"],
    })

with open("./cards.json", "w") as f:
    json.dump(data_out, f, indent=4, ensure_ascii=False)



