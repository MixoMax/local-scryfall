
import requests
from tqdm import tqdm
from prepare_data import prepare_card_data
from download_images import download_images
from scryfall_bulk_importer import load_data

# fetch Scryfall data API for the newest bulk data export
url = "https://api.scryfall.com/bulk-data"
response = requests.get(url)
data = response.json()
download_uri = data["data"][2]["download_uri"]
print(download_uri)

# download the data file
file_path = "scryfall-data.json"

# download with progress bar
with open(file_path, "wb") as file:
    response = requests.get(download_uri, stream=True)
    for chunk in tqdm(response.iter_content(chunk_size=8192), desc="Downloading data", unit="KB"):
        if chunk:
            file.write(chunk)
print(f"Data downloaded and saved to {file_path}")

# construct cards.json and images/*.webp files
prepare_card_data(file_path)
download_images(file_path)


ALL_CARDS = load_data("./cards.json")

