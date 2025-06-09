from scryfall_syntax_parser import query_to_filter, apply_filters, print_filters

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
        filters = query_to_filter(q, debug_print=False)
        print_filters(filters)
        filtered_cards = apply_filters(ALL_CARDS, filters)
        if not filtered_cards:
            return {"error": "No cards found matching the query"}
        return {"cards": filtered_cards}
    except Exception as e:
        return {"error": "Failed to process query", "details": str(e)}

@app.get("/api/v1/random")
async def get_random_cards(q: str = "", count: int = 1) -> JSONResponse:
    """Get random cards from the database. Supports a count parameter."""
    if not ALL_CARDS:
        return JSONResponse({"error": "No cards available"}, status_code=500)

    filtered_cards_pool = ALL_CARDS
    if q:
        try:
            filters = query_to_filter(q, debug_print=False)
            print_filters(filters)
            filtered_cards_pool = apply_filters(ALL_CARDS, filters)
        except Exception as e:
            print(f"Error processing query '{q}': {e}") # Log error server-side
            return JSONResponse({"error": "Failed to process query", "details": str(e)}, status_code=400)

    if not filtered_cards_pool:
        return JSONResponse({"error": "No cards found matching the query"}, status_code=404)

    if len(filtered_cards_pool) < count:
        return JSONResponse({"error": "Not enough cards available"}, status_code=404)
    
    random_cards = random.sample(filtered_cards_pool, count)
    if len(random_cards) == 1:
        return JSONResponse({"card": random_cards[0]})
    return JSONResponse({"cards": random_cards})


@app.get("/api/v1/card/{safe_card_name}")
async def get_card_by_name(safe_card_name: str) -> Dict[str, Any]:
    """Get a card by its name."""
    for card in ALL_CARDS:
        if card["safe_name"] == safe_card_name:
            return {"card": card}
    return {"error": "Card not found"}


@app.get("/card/{safe_card_name}")
async def get_card_page(safe_card_name: str) -> HTMLResponse:
    """Serve the card page for a specific card."""
    with open("static/card.html", "r") as f:
        html_content = f.read()
    
    html_content = html_content.replace("[CARD_NAME]", safe_card_name)

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
    
    mime_type = "application/octet-stream"
    if "." in path:
        ext = path.split(".")[-1].lower()
        match ext:
            case "html": mime_type = "text/html"
            case "css": mime_type = "text/css"
            case "js": mime_type = "application/javascript"
            case "json": mime_type = "application/json"
            case "webp": mime_type = "image/webp"
    
    print(f"Serving file: {file_path} with MIME type: {mime_type}")

    return FileResponse(file_path, media_type=mime_type)

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    uvicorn.run(app, host="0.0.0.0", port=port)
