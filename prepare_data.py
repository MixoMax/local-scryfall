import json
from tqdm import tqdm

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

def prepare_card_data(bulk_file_name):

    with open(bulk_file_name, "r", encoding="utf-8") as f:
        cards = json.load(f)

    data_out = []

    for card in tqdm(cards):
        data_out.append({
            "name": card["name"],
            "safe_name": card_name_to_file_name(card["name"]),
            "file_name": card_name_to_file_name(card["name"] + "-" + card.get("type_line", card.get("card_faces", [{}])[0].get("type_line", ""))) + ".webp",
            "released-at": card["released_at"],
            "year": int(card["released_at"].split("-")[0]),
            "mana_cost": card.get("mana_cost", card.get("card_faces", [{}])[0].get("mana_cost", "")),
            "cmc": card.get("cmc", card.get("card_faces", [{}])[0].get("cmc", 0)),
            "type_line": card.get("type_line", card.get("card_faces", [{}])[0].get("type_line", "")),
            "oracle_text": card.get("oracle_text", card.get("card_faces", [{}])[0].get("oracle_text", "")),
            "power": card.get("power", card.get("card_faces", [{}])[0].get("power", "")),
            "toughness": card.get("toughness", card.get("card_faces", [{}])[0].get("toughness", "")),
            "loyalty": card.get("loyalty", card.get("card_faces", [{}])[0].get("loyalty", "")),
            "colors": card.get("colors", card.get("card_faces", [{}])[0].get("colors", [])),
            "color_identity": card.get("color_identity", []),
            "keywords": card.get("keywords", []),
            "set": [card.get("set", "")],
            "rarity": card.get("rarity", ""),
            "edhrec_rank": card.get("edhrec_rank", 0),
            "price_euro": card.get("prices", {}).get("eur", 0.0),
            "price_usd": card.get("prices", {}).get("usd", 0.0),
            "legal_formats": [fmt_str for fmt_str, legal in card.get("legalities", {}).items() if legal == "legal"],
        })

    names_to_card = {}
    for card in data_out:
        safe_name = card["safe_name"]
        if not safe_name in names_to_card:
            names_to_card[safe_name] = card
        else:
            names_to_card[safe_name]["set"].extend(card["set"])
            names_to_card[safe_name]["set"] = list(set(names_to_card[safe_name]["set"]))

    data_out = list(names_to_card.values())

    with open("./cards.json", "w", encoding="utf-8") as f:
        json.dump(data_out, f, indent=4, ensure_ascii=False)

