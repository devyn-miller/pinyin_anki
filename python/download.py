import os
import requests
import time

SYLLABLE_FILE = 'legal_syllables.txt'
OUTPUT_DIR = 'mp3'
YOYO_BASE = "https://cdn.yoyochinese.com/audio/pychart/"

# Create output directory if not exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def to_url_syllable(s):
    # Use 'v' for ü in URL
    return s.replace('ü', 'v').replace('uu', 'v')

def to_filename_syllable(s):
    # Use 'uu' for ü in saved filename (for your convention)
    return s.replace('ü', 'uu').replace('v', 'uu')

with open(SYLLABLE_FILE, 'r', encoding='utf-8') as f:
    syllables = [line.strip() for line in f if line.strip()]

for syll in syllables:
    for tone in range(1, 5):
        url_syll = to_url_syllable(syll)
        file_syll = to_filename_syllable(syll)
        url = f"{YOYO_BASE}{url_syll}{tone}.mp3"
        out_path = os.path.join(OUTPUT_DIR, f"{file_syll}{tone}.mp3")
        # Skip if already downloaded
        if os.path.exists(out_path):
            continue
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200 and r.content:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                print(f"Downloaded: {out_path}")
            else:
                print(f"NOT FOUND: {url}")
        except Exception as e:
            print(f"ERROR downloading {url}: {e}")
        # time.sleep(0.2)  # avoid hammering the server