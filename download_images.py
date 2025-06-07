import json
import requests
from tqdm import tqdm
from PIL import Image
import threading
import queue
import os

NOT_ALLOWED = [" ", ":", "/", "\\", "?", "*", "\"", "<", ">", "|", "'", "!", "@", "#", "$", "%", "^", "&", "(", ")", "+", "=", "{", "}", "[", "]"]
def card_name_to_file_name(card_name):
    for char in NOT_ALLOWED:
        card_name = card_name.replace(char, "-")
    while "--" in card_name:
        card_name = card_name.replace("--", "-")
    return card_name.strip("-").lower()


with open("./oracle-cards-20250606210418.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

def download_image(url, filename):
    img = Image.open(requests.get(url, stream=True).raw)
    img.save(filename, "WEBP", quality=80)
    img.close()

def e2e_download_worker(q: queue.Queue, pbar: tqdm):
    while not q.empty():
        try:
            card = q.get_nowait()
            if "image_uris" not in card:
                card["image_uris"] = {
                    "normal": card["card_faces"][0]["image_uris"]["normal"] if "card_faces" in card and len(card["card_faces"]) > 0 else ""
                }
            
            if not card["image_uris"].get("normal"):
                # print(f"Skipping {card.get('name', 'Unknown Card')} due to missing image URI.")
                pbar.update(1)
                q.task_done()
                continue

            url = card["image_uris"]["normal"]
            name = card_name_to_file_name(card["name"])
            
            # Create images directory if it doesn't exist
            if not os.path.exists("./images"):
                os.makedirs("./images")
                
            filename = f"./images/{name}.webp"
            
            # Skip if file already exists
            if os.path.exists(filename):
                # print(f"Skipping {card['name']} as it already exists.")
                pbar.update(1)
                q.task_done()
                continue
                
            download_image(url, filename)
            pbar.update(1)
            q.task_done()
        except queue.Empty:
            break
        except Exception as e:
            print(f"Error downloading {card.get('name', 'Unknown Card')}: {e}")
            pbar.update(1)
            q.task_done()

NUM_THREADS = 100  # Adjust as needed
card_queue = queue.Queue()

for card_data in cards:
    card_queue.put(card_data)

progress_bar = tqdm(total=card_queue.qsize(), desc="Downloading Images")

threads = []
for _ in range(NUM_THREADS):
    thread = threading.Thread(target=e2e_download_worker, args=(card_queue, progress_bar))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

progress_bar.close()
print("Image download process completed.")
