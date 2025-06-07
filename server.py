from scryfall_syntax_parser import query_to_filter, apply_filters

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
import uvicorn
import os
import sys
# import sqlite3
import re
from typing import Any, Dict, List, Union
import random
from scryfall_bulk_importer import load_data

app = FastAPI()

# conn = sqlite3.connect("scryfall_new.db", check_same_thread=False)
# cur = conn.cursor()

# rows = cur.execute("SELECT * FROM cards").fetchall()
# keys = ["name", "mana_cost", "cmc", "type_line", "oracle_text", "power", "toughness", "loyalty", "img_file_name"]
# types = [str, str, int, str, str, int, int, int, str]
# ALL_CARDS = []
# for row in rows:
#     row_data = []
#     for i, key in enumerate(keys):
#         value = row[i]
#         try:
#             value = types[i](value)
#         except:
#             value = str(value)
#         row_data.append(value)
#     ALL_CARDS.append({key: value for key, value in zip(keys, row_data)})
ALL_CARDS = load_data("./cards.json")



@app.get("/api/v1/search")
async def search_cards(q: str) -> Dict[str, Any]:
    """Search cards using Scryfall-like syntax."""
    try:
        filters = query_to_filter(q)
        filtered_cards = apply_filters(ALL_CARDS, filters)
        if not filtered_cards:
            return {"error": "No cards found matching the query"}
        return {"cards": filtered_cards}
    except Exception as e:
        return {"error": "Failed to process query", "details": str(e)}

@app.get("/api/v1/random")
async def get_random_card() -> Dict[str, Any]:
    """Get a random card from the database."""
    if not ALL_CARDS:
        return {"error": "No cards available"}
    random_card = random.choice(ALL_CARDS)
    return {"card": random_card}

@app.get("/api/v1/card/{card_name}")
async def get_card_by_name(card_name: str) -> Dict[str, Any]:
    """Get a card by its name."""
    card_name = re.sub(r"[^a-zA-Z0-9\s]", "", card_name).strip().lower()
    for card in ALL_CARDS:
        if card["name"].lower() == card_name:
            return {"card": card}
    return {"error": "Card not found"}


@app.get("/card/{card_name}")
async def get_card_page(card_name: str) -> HTMLResponse:
    """Serve the card page for a specific card."""
    with open("static/card.html", "r") as f:
        html_content = f.read()
    
    card_name = re.sub(r"[^a-zA-Z0-9\s]", "", card_name).strip().lower()
    html_content = html_content.replace("[CARD_NAME]", card_name)

    return HTMLResponse(content=html_content)

@app.get("/random")
async def get_random_card_page() -> FileResponse:
    return FileResponse("static/random.html")


@app.get("/")
@app.get("/{path:path}")
async def get_static_file(path: str = "", q: str = ""):
    if not path:
        path = "index.html"
    if path.endswith(".webp"):
        file_path = os.path.join("images", path)
    else:
        file_path = os.path.join("static", path)
    
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"message": "File not found"})
    return FileResponse(file_path)

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    uvicorn.run(app, host="0.0.0.0", port=port)
