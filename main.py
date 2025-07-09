import genanki
import re
import os
import csv
import sys

# ---- CONFIG ----
# Use relative paths for better portability
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MP3_FOLDER = os.path.join(SCRIPT_DIR, 'mp3')
CSV_PATH = os.path.join(SCRIPT_DIR, 'pinyin_word_lookup_filled1.csv')
OUTPUT_APKG_P2A = 'Pinyin-to-Audio.apkg'
OUTPUT_APKG_A2P = 'Audio-to-Pinyin.apkg'
OUTPUT_APKG_BOTH = 'Pinyin-Audio-Bidirectional.apkg'
DECK_NAME = 'Mandarin Pinyin Bidirectional'
DECK_ID = 202407041
MODEL_ID = 202407042

# ---- HELPERS ----

def load_meanings(csv_path):
    lookup = {}
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                full_pinyin = row['FullPinyin']
                chars = row['Character(s)'].strip()
                simplified = chars.split()[0] if chars else ''
                meaning = row['Meaning']
                formatted_meaning = (
                    "<div style='font-size: 1.6em; font-weight: bold;'>" + simplified + "</div>"
                    "<div style='margin-top: 5px; font-size: 1.1em;'>" + "<br>".join(meaning.split('/')) + "</div>"
                )
                lookup[full_pinyin] = formatted_meaning
        print(f"Loaded {len(lookup)} entries from {csv_path}")
    except Exception as e:
        print(f"Error loading CSV file {csv_path}: {e}")
        sys.exit(1)
    return lookup

TONE_MAP = {
    'a': ['ā', 'á', 'ǎ', 'à'],
    'e': ['ē', 'é', 'ě', 'è'],
    'i': ['ī', 'í', 'ǐ', 'ì'],
    'o': ['ō', 'ó', 'ǒ', 'ò'],
    'u': ['ū', 'ú', 'ǔ', 'ù'],
    'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ'],
}

def pinyin_with_tone(syllable, tone):
    display = syllable.replace('uu', 'ü')
    vowels = 'aeiouü'
    if tone == 5 or tone == 0:
        return display
    for v in 'aoe':
        if v in display:
            idx = display.index(v)
            return display[:idx] + f'<span class="t{tone}">' + TONE_MAP[v][tone - 1] + '</span>' + display[idx + 1:]
    if 'iu' in display:
        idx = display.index('u')
        return display[:idx] + f'<span class="t{tone}">' + TONE_MAP['u'][tone - 1] + '</span>' + display[idx + 1:]
    if 'ui' in display:
        idx = display.index('i')
        return display[:idx] + f'<span class="t{tone}">' + TONE_MAP['i'][tone - 1] + '</span>' + display[idx + 1:]
    for i in range(len(display) - 1, -1, -1):
        if display[i] in vowels:
            v = display[i]
            return display[:i] + f'<span class="t{tone}">' + TONE_MAP[v][tone - 1] + '</span>' + display[i + 1:]
    return display

# ---- READ FILES ----
# Check if MP3 folder exists
if not os.path.exists(MP3_FOLDER):
    print(f"ERROR: MP3 folder not found at {MP3_FOLDER}")
    print("Creating mp3 folder...")
    try:
        os.makedirs(MP3_FOLDER)
        print(f"Created mp3 folder at {MP3_FOLDER}")
        print("Please add your .mp3 files to this folder and run the script again.")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to create mp3 folder: {e}")
        sys.exit(1)

filenames = [f for f in os.listdir(MP3_FOLDER) if f.endswith('.mp3')]
print(f"Found {len(filenames)} mp3 files in {MP3_FOLDER}")

meaning_lookup = load_meanings(CSV_PATH)

# ---- ANKI MODELS ----

model_p2a = genanki.Model(
    MODEL_ID + 1,
    'Pinyin to Audio Model',
    fields=[
        {'name': 'Pinyin'},
        {'name': 'Audio'},
        {'name': 'Meaning'},
    ],
    templates=[
        {
            'name': 'Pinyin→Audio',
            'qfmt': '{{Pinyin}}',
            'afmt': '{{FrontSide}}<hr id="answer">{{Audio}}<br>{{Meaning}}',
        },
    ])

model_a2p = genanki.Model(
    MODEL_ID + 2,
    'Audio to Pinyin Model',
    fields=[
        {'name': 'Pinyin'},
        {'name': 'Audio'},
        {'name': 'Meaning'},
    ],
    templates=[
        {
            'name': 'Audio→Pinyin',
            'qfmt': '{{Audio}}',
            'afmt': '{{FrontSide}}<hr id="answer">{{Pinyin}}<br>{{Meaning}}',
        },
    ])

deck_pinyin_to_audio = genanki.Deck(DECK_ID + 1, 'Pinyin to Audio')
deck_audio_to_pinyin = genanki.Deck(DECK_ID + 2, 'Audio to Pinyin')
deck_bidirectional = genanki.Deck(DECK_ID + 3, DECK_NAME)

# ---- BUILD CARDS ----

added_files = set()
skipped_files = []
media_files = []  # Store actual media file paths

for fname in filenames:
    base = os.path.basename(fname)
    match = re.match(r"([a-z]+(?:uu)?)([1-5])\.mp3", base)
    if not match:
        print(f"SKIP (not matched): {fname}")
        skipped_files.append(fname)
        continue
    
    syllable, tone = match.group(1), int(match.group(2))
    pinyin = pinyin_with_tone(syllable, tone)
    full_pinyin = syllable + str(tone)
    meaning = meaning_lookup.get(full_pinyin, "")
    
    # Create notes for each deck
    note_p2a = genanki.Note(
        model=model_p2a,
        fields=[pinyin, f"[sound:{base}]", meaning],
        guid=f"{syllable}{tone}p2a"
    )
    note_a2p = genanki.Note(
        model=model_a2p,
        fields=[pinyin, f"[sound:{base}]", meaning],
        guid=f"{syllable}{tone}a2p"
    )
    note_bi_p2a = genanki.Note(
        model=model_p2a,
        fields=[pinyin, f"[sound:{base}]", meaning],
        guid=f"{syllable}{tone}bi_p2a"
    )
    note_bi_a2p = genanki.Note(
        model=model_a2p,
        fields=[pinyin, f"[sound:{base}]", meaning],
        guid=f"{syllable}{tone}bi_a2p"
    )
    
    # Add notes to decks
    deck_pinyin_to_audio.add_note(note_p2a)
    deck_audio_to_pinyin.add_note(note_a2p)
    deck_bidirectional.add_note(note_bi_p2a)
    deck_bidirectional.add_note(note_bi_a2p)
    
    # Add media file to the list
    full_path = os.path.join(MP3_FOLDER, base)
    if os.path.exists(full_path):
        media_files.append(full_path)
        added_files.add(base)
        print(f"ADD: {base} (path: {full_path})")
    else:
        print(f"MISSING FILE: {full_path}")
        skipped_files.append(base)

print(f"\nSummary: {len(added_files)} mp3 files added, {len(skipped_files)} skipped or missing.")
if skipped_files:
    print("Skipped or missing files:", skipped_files)

print(f"\nMedia files to be included in packages: {len(media_files)}")
if len(media_files) == 0:
    print("WARNING: No media files will be included in the Anki packages!")
else:
    print(f"First 5 media files: {media_files[:5]}")

# ---- EXPORT ----
print(f"\nCreating {OUTPUT_APKG_P2A}...")
p2a_package = genanki.Package(deck_pinyin_to_audio, media_files)
p2a_package.write_to_file(OUTPUT_APKG_P2A)
print(f"Creating {OUTPUT_APKG_A2P}...")
a2p_package = genanki.Package(deck_audio_to_pinyin, media_files)
a2p_package.write_to_file(OUTPUT_APKG_A2P)
print(f"Creating {OUTPUT_APKG_BOTH}...")
both_package = genanki.Package(deck_bidirectional, media_files)
both_package.write_to_file(OUTPUT_APKG_BOTH)
print(f"\nAnki decks created successfully:")
print(f"1. {OUTPUT_APKG_P2A}")
print(f"2. {OUTPUT_APKG_A2P}")
print(f"3. {OUTPUT_APKG_BOTH}")