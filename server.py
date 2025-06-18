from scryfall_syntax_parser import query_to_filter, apply_filters, print_filters, Filter, LogicalFilter, LogicalOperator, Operator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
import uvicorn
import os
import sys
import re
from typing import Any, Dict, List, Union
import random
from scryfall_bulk_importer import load_data
from functools import lru_cache
from datetime import datetime
import uuid
from pydantic import BaseModel
from tqdm import tqdm

app = FastAPI()

ALL_CARDS = load_data("./cards.json")

draft_sessions: Dict[str, Dict[str, Any]] = {}

class NewDraftRequest(BaseModel):
    set_code: str
    num_packs: int = 3
    booster_type: str = "draft"

class PickCardRequest(BaseModel):
    player_id: str
    card_safe_name: str

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

def get_set_codes() -> tuple[str]:
    set_set = set()
    for card in ALL_CARDS:
        set_set.update(card.get("set", []))
    return tuple(sorted(set_set))

def get_set_codes_draftable() -> List[str]:
    fp = "draftable_sets.txt"
    if os.path.exists(fp):
        if os.path.getmtime(fp) > os.path.getmtime("./cards.json"):
            # If the file is newer than the cards.json, return cached data
            with open(fp, "r") as f:
                return [line.strip() for line in f.readlines() if line.strip()]
    

    set_codes = get_set_codes()
    ret_set_codes = []
    for set_code in tqdm(set_codes):
        for boster_type in ["draft", "set"]:
            sim_pack = generate_pack(set_code, boster_type)
            if len(sim_pack) < 15:
                continue
            ret_set_codes.append(set_code)

    ret_set_codes = sorted(set(ret_set_codes))
    with open(fp, "w") as f:
        for code in ret_set_codes:
            f.write(f"{code}\n")

    return ret_set_codes

@app.get("/api/v1/sets")
async def get_sets(only_draftable: bool = False):
    """Get a list of all sets."""
    if only_draftable:
        return JSONResponse({"sets": get_set_codes_draftable()})
    else:
        return JSONResponse({"sets": list(get_set_codes())})
    
def get_session_public_view(session_id: str):
    session = draft_sessions.get(session_id)
    if not session:
        return None
    return {
        "id": session_id,
        "set_code": session["set_code"],
        "players": [{"id": p["id"], "is_host": p["is_host"]} for p in session["players"]],
        "status": session["status"]
    }

@app.post("/api/v1/draft/new")
async def new_draft(request: NewDraftRequest):
    session_id = str(uuid.uuid4())
    player_id = str(uuid.uuid4())
    
    draft_sessions[session_id] = {
        "id": session_id,
        "set_code": request.set_code,
        "num_packs": request.num_packs,
        "booster_type": request.booster_type,
        "players": [{"id": player_id, "is_host": True, "picked_cards": [], "current_pack": []}],
        "status": "lobby", # lobby, picking, finished
        "current_pack_number": 0,
        "all_packs": []
    }
    return {"session_id": session_id, "player_id": player_id, "session": get_session_public_view(session_id)}

@app.get("/api/v1/draft/sessions")
async def get_sessions():
    return {"sessions": [get_session_public_view(sid) for sid, s in draft_sessions.items() if s["status"] == "lobby"]}

@app.post("/api/v1/draft/{session_id}/join")
async def join_draft(session_id: str):
    session = draft_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if len(session["players"]) >= 8:
        raise HTTPException(status_code=400, detail="Session is full")
    if session["status"] != "lobby":
        raise HTTPException(status_code=400, detail="Draft has already started")

    player_id = str(uuid.uuid4())
    session["players"].append({"id": player_id, "is_host": False, "picked_cards": [], "current_pack": []})
    return {"session_id": session_id, "player_id": player_id, "session": get_session_public_view(session_id)}

def get_cards_by_rarity(set_cards: List[Dict[str, Any]]):
    commons = [c for c in set_cards if c.get("rarity") == "common" and "Land" not in c.get("type_line", "")]
    uncommons = [c for c in set_cards if c.get("rarity") == "uncommon"]
    rares = [c for c in set_cards if c.get("rarity") == "rare"]
    mythics = [c for c in set_cards if c.get("rarity") == "mythic"]
    basic_lands = [c for c in set_cards if c.get("type_line", "").startswith("Basic Land")]
    return commons, uncommons, rares, mythics, basic_lands

def _add_cards_to_pack(pack: List[Dict[str, Any]], card_pool: List[Dict[str, Any]], count: int):
    """Helper to add non-duplicate cards to a pack."""
    if not card_pool or count == 0:
        return
    
    pack_card_names = {c['name'] for c in pack}
    available_cards = [c for c in card_pool if c['name'] not in pack_card_names]
    
    if len(available_cards) < count:
        pool_to_sample = available_cards if available_cards else card_pool
        if not pool_to_sample:
            return
        pack.extend(random.choices(pool_to_sample, k=count))
    else:
        pack.extend(random.sample(available_cards, k=count))

def generate_set_booster(set_code: str) -> List[Dict[str, Any]]:
    set_cards = [card for card in ALL_CARDS if set_code in card.get("set", []) and len(card.get("legal_formats", [])) != 0]
    
    commons, uncommons, rares, mythics, basic_lands = get_cards_by_rarity(set_cards)
    
    pack: List[Dict[str, Any]] = []

    # Slot 1: 6 Commons or uncommons
    c_u_outcomes = [(5, 1), (4, 2), (3, 3), (2, 4), (1, 5), (0, 6)]
    c_u_weights = [35, 40, 12.5, 7, 3.5, 2]
    num_c, num_u = random.choices(c_u_outcomes, weights=c_u_weights, k=1)[0]
    _add_cards_to_pack(pack, commons, num_c)
    _add_cards_to_pack(pack, uncommons, num_u)

    # Slot 2: 1 Common or uncommon
    commons_and_uncommons = commons + uncommons
    _add_cards_to_pack(pack, commons_and_uncommons, 1)

    # Slot 3: 2 Common or uncommon or rare or mythic rare
    slot3_outcomes = [('C', 'C'), ('C', 'U'), ('C', 'R/M'), ('U', 'U'), ('U', 'R/M'), ('R/M', 'R/M')]
    slot3_weights = [49, 24.5, 17.5, 3.1, 4.3, 1.6]
    card1_type, card2_type = random.choices(slot3_outcomes, weights=slot3_weights, k=1)[0]
    
    rares_and_mythics = rares + mythics
    type_map = {'C': commons, 'U': uncommons, 'R/M': rares_and_mythics}
    
    _add_cards_to_pack(pack, type_map[card1_type], 1)
    _add_cards_to_pack(pack, type_map[card2_type], 1)

    # Slot 4: 1 Rare or Mythic rare
    if mythics and random.random() < 0.135:
        _add_cards_to_pack(pack, mythics, 1)
    else:
        _add_cards_to_pack(pack, rares, 1)

    # Slot 5: 1 Anything from common to Mythic rare
    all_non_land = commons + uncommons + rares + mythics
    _add_cards_to_pack(pack, all_non_land, 1)

    # Slot 6: 1 Basic Land
    if basic_lands:
        _add_cards_to_pack(pack, basic_lands, 1)
    else:
        if commons:
            _add_cards_to_pack(pack, commons, 1)

    return pack

def generate_draft_booster(set_code: str) -> List[Dict[str, Any]]:
    set_cards = [card for card in ALL_CARDS if set_code in card.get("set", []) and len(card.get("legal_formats", [])) != 0]
    
    commons, uncommons, rares, mythics, basic_lands = get_cards_by_rarity(set_cards)
    
    pack: List[Dict[str, Any]] = []
    _add_cards_to_pack(pack, commons, 10)
    _add_cards_to_pack(pack, uncommons, 3)
    
    # 1 in 8 packs have a mythic instead of a rare
    if mythics and random.randint(1, 8) == 1:
        _add_cards_to_pack(pack, mythics, 1)
    elif rares:
        _add_cards_to_pack(pack, rares, 1)
        
    # Fill remaining slots if any rarity was short
    while len(pack) < 14 and commons:
        _add_cards_to_pack(pack, commons, 1)

    # Basic lands
    if basic_lands:
        _add_cards_to_pack(pack, basic_lands, 1)
    elif commons: # if no basic lands in set, add a common
        _add_cards_to_pack(pack, commons, 1)

    return pack

def generate_pack(set_code: str, booster_type: str) -> List[Dict[str, Any]]:
    if booster_type == "set":
        pack = generate_set_booster(set_code)
    else:
        pack = generate_draft_booster(set_code)

    unique_names = []
    pack_unique = []
    for card in pack:
        safe_name = card.get("safe_name", "")
        if safe_name not in unique_names:
            unique_names.append(safe_name)
            pack_unique.append(card)
    return pack_unique

@app.post("/api/v1/draft/{session_id}/start")
async def start_draft(session_id: str):
    session = draft_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] != "lobby":
        raise HTTPException(status_code=400, detail="Draft already started or finished")

    session["status"] = "picking"
    session["current_pack_number"] = 1
    
    for player in session["players"]:
        player["has_picked_this_round"] = False
    
    # Generate all packs for the draft
    num_players = len(session["players"])
    for _ in range(session["num_packs"]):
        packs_for_round = [generate_pack(session["set_code"], session.get("booster_type", "draft")) for _ in range(num_players)]
        session["all_packs"].append(packs_for_round)

    # Distribute the first pack to each player
    first_round_packs = session["all_packs"][0]
    for i, player in enumerate(session["players"]):
        player["current_pack"] = first_round_packs[i]

    return {"message": "Draft started"}

@app.post("/api/v1/draft/{session_id}/pick")
async def pick_card(session_id: str, request: PickCardRequest):
    session = draft_sessions.get(session_id)
    if not session or session["status"] != "picking":
        raise HTTPException(status_code=404, detail="Invalid session or not in picking phase")

    player = next((p for p in session["players"] if p["id"] == request.player_id), None)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    pack = player["current_pack"]
    card_to_pick = next((c for c in pack if c["safe_name"] == request.card_safe_name), None)
    
    if not card_to_pick:
        raise HTTPException(status_code=400, detail="Card not in the current pack")

    player["picked_cards"].append(card_to_pick)
    player["current_pack"].remove(card_to_pick)
    player["has_picked_this_round"] = True
    
    # Check if all players have picked
    all_picked = all(p.get("has_picked_this_round", False) for p in session["players"])
    
    if all_picked:
        # Rotate packs
        num_players = len(session["players"])
        if len(player["current_pack"]) > 0: # If there are cards left to pass
            packs_to_pass = [p["current_pack"] for p in session["players"]]
            for i in range(num_players):
                # Pass clockwise for odd packs, counter-clockwise for even packs
                if session["current_pack_number"] % 2 != 0:
                    session["players"][i]["current_pack"] = packs_to_pass[(i - 1 + num_players) % num_players]
                else:
                    session["players"][i]["current_pack"] = packs_to_pass[(i + 1) % num_players]
        else: # End of a pack
            session["current_pack_number"] += 1
            if session["current_pack_number"] > session["num_packs"]:
                session["status"] = "finished"
            else:
                # Distribute next round of packs
                next_round_packs = session["all_packs"][session["current_pack_number"] - 1]
                for i, p in enumerate(session["players"]):
                    p["current_pack"] = next_round_packs[i]

        if session["status"] == "picking":
            for p in session["players"]:
                p["has_picked_this_round"] = False

    return {"message": "Card picked successfully"}

@app.get("/api/v1/draft/{session_id}/status")
async def get_draft_status(session_id: str, player_id: str):
    session = draft_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    player = next((p for p in session["players"] if p["id"] == player_id), None)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    response = {
        "status": session["status"],
        "players": [{"id": p["id"], "is_host": p["is_host"]} for p in session["players"]],
    }

    if session["status"] == "picking":
        # A player is waiting if they have picked but the packs haven't rotated.
        if player.get("has_picked_this_round", False):
             response["status"] = "waiting"
        else:
            response["pack"] = player["current_pack"]
    response["deck"] = player["picked_cards"]

    return response




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

@app.get("/draft")
async def get_draft_page() -> FileResponse:
    return FileResponse("static/draft.html")


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
