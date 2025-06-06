import sqlite3
from PIL import Image
from io import BytesIO
import base64
from tqdm import tqdm
import concurrent.futures
import os

# Ensure the images directory exists
if not os.path.exists("images"):
    os.makedirs("images")

conn = sqlite3.connect("scryfall.db", check_same_thread=False)
cur = conn.cursor()

not_allowed = [" ", "\\", "/", ":", "*", "?", '"', "<", ">", "|", "'", "(", ")", ",", "!", "@", "#", "$", "%", "^", "&", "`", "~"]

def card_name_to_filename(name):
    file_path: str = name
    for char in not_allowed:
        file_path = file_path.replace(char, "-")
    while "--" in file_path:
        file_path = file_path.replace("--", "-")
    if file_path.endswith("-"):
        file_path = file_path[:-1]
    if file_path.endswith("."):
        file_path = file_path[:-1]
    return file_path + ".webp"


q = "SELECT * FROM cards"
cur.execute(q)
rows = cur.fetchall()

print(f"Found {len(rows)} rows in the database.")

def process_image_row(row_data: tuple) -> None:
    """Processes a single row from the database to extract and save an image."""
    img_b64: str = row_data[-1]
    img: Image.Image = Image.open(BytesIO(base64.b64decode(img_b64)))

    card_name: str = row_data[0]
    file_path = os.path.join("images", card_name_to_filename(card_name))

    img.save(file_path, "webp", quality=80)

# process images in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers = 192) as executor:
    futures = [executor.submit(process_image_row, row) for row in rows]

    for future in tqdm(concurrent.futures.as_completed(futures), total=len(rows)):
        future.result()

conn.close()
