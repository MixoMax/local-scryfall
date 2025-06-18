import json
import requests
from tqdm import tqdm
from PIL import Image
import threading
import queue
import os
import sys


def download_images(bulk_file_name, force_download=False):

    with open(bulk_file_name, "r", encoding="utf-8") as f:
        scryfall_dump = json.load(f)

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


    def download_image(url, filename):
        img = Image.open(requests.get(url, stream=True).raw)
        img.save(filename, "WEBP", quality=80)
        img.close()

    def e2e_download_worker(q: queue.Queue, pbar: tqdm, force_download: bool):
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
                name = card_name_to_file_name(card["name"] + "-" + card.get("type_line", card.get("card_faces", [{}])[0].get("type_line", "")))

                filename = f"./images/{name}.webp"
                
                # Skip if file already exists
                if os.path.exists(filename) and not force_download:
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

    NUM_THREADS = 100
    card_queue = queue.Queue()

    if not os.path.exists("./images"):
        os.makedirs("./images")

    for card_data in scryfall_dump:
        if card_data.get("lang", "en") != "en":
            continue
        if card_data.get("promo", False):
            continue
        card_queue.put(card_data)

    progress_bar = tqdm(total=card_queue.qsize(), desc="Downloading Images")

    threads = []
    for _ in range(NUM_THREADS):
        thread = threading.Thread(target=e2e_download_worker, args=(card_queue, progress_bar, force_download))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    progress_bar.close()
    print("Image download process completed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_images.py <bulk_file_name> <optional: force_download>")
        sys.exit(1)

    bulk_file_name = sys.argv[1]
    force_download = sys.argv[2].lower() == "true" if len(sys.argv) > 2 else False
    download_images(bulk_file_name, force_download)