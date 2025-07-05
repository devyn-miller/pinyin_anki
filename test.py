import requests
import time
import csv
import re

INPUT_FILE = "python/legal_syllables.txt"
OUTPUT_FILE = "pinyin_word_lookup.csv"
BASE_URL = "https://www.mdbg.net/chinese/dictionary?page=worddict&wdrst=0&wdqb="

def check_mdbg(pinyin_tone):
    """Returns (exists, matched_chars, meanings) tuple"""
    try:
        url = BASE_URL + pinyin_tone
        res = requests.get(url, timeout=5)
        html = res.text.lower()

        if "no results found" in html:
            return False, "", ""

        # Extract matched characters crudely
        matches = re.findall(r'<span class="c">(.{1,2})</span>', res.text)
        characters = ", ".join(set(matches))

        # Extract meanings: look for gloss blocks
        meanings = []
        gloss_matches = re.findall(r'<div class="defs">(.*?)</div>', res.text, re.DOTALL)
        for gloss in gloss_matches:
            gloss_text = re.sub(r"<.*?>", "", gloss).strip()
            if gloss_text:
                meanings.append(gloss_text)

        return True, characters, "; ".join(meanings[:3])  # up to 3 meanings
    except Exception as e:
        return False, "", ""

def load_syllables(filename):
    with open(filename, encoding="utf-8") as f:
        lines = f.readlines()
    all_sylls = []
    for line in lines:
        parts = [x.strip() for x in line.strip().split(",") if x.strip()]
        all_sylls.extend(parts)
    return sorted(set(all_sylls))

def main():
    syllables = load_syllables(INPUT_FILE)
    results = []

    for syll in syllables:
        for tone in range(1, 5):
            query = f"{syll}{tone}"
            exists, chars, meanings = check_mdbg(query)
            results.append({
                "Syllable": syll,
                "Tone": tone,
                "FullPinyin": query,
                "Exists": "Yes" if exists else "No",
                "Character(s)": chars,
                "Meaning": meanings
            })
            print(f"{query}: {'Yes' if exists else 'No'} | {chars} | {meanings}")
            # time.sleep(0.5)  # avoid overloading MDBG

    # Write to CSV
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Syllable", "Tone", "FullPinyin", "Exists", "Character(s)", "Meaning"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone! Results written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()