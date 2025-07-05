import genanki
import re
import os
import csv
# ---- READ FILES ----

def load_meanings(csv_path):
    lookup = {}
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
    return lookup
import csv

# ---- HELPERS ----

def load_meanings(csv_path):
    lookup = {}
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
    return lookup

# ---- CONFIG ----
MP3_FOLDER = '/Users/devyn/Downloads/pinyin_anki/mp3'
CSV_PATH = '/Users/devyn/Downloads/pinyin_anki/pinyin_word_lookup_filled1.csv'
meaning_lookup = load_meanings(CSV_PATH)
OUTPUT_APKG_P2A = 'Pinyin-to-Audio.apkg'
OUTPUT_APKG_A2P = 'Audio-to-Pinyin.apkg'
DECK_NAME = 'Mandarin Pinyin Bidirectional'
DECK_ID = 202407041
MODEL_ID = 202407042

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

filenames = [f for f in os.listdir(MP3_FOLDER) if f.endswith('.mp3')]

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
media_files = []

# ---- BUILD CARDS ----

for fname in filenames:
    base = os.path.basename(fname)
    # Match a-z plus optional uu (no conversion to ü here)
    match = re.match(r"([a-z]+(?:uu)?)([1-5])\.mp3", base)
    if not match:
        print(f"SKIP (not matched): {fname}")
        continue
    syllable, tone = match.group(1), int(match.group(2))
    pinyin = pinyin_with_tone(syllable, tone)
    full_pinyin = syllable + str(tone)
    meaning = meaning_lookup.get(full_pinyin, "")
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
    deck_pinyin_to_audio.add_note(note_p2a)
    deck_audio_to_pinyin.add_note(note_a2p)
    media_files.append(os.path.join(MP3_FOLDER, base))

# ---- EXPORT ----

genanki.Package(deck_pinyin_to_audio, media_files).write_to_file(OUTPUT_APKG_P2A)
genanki.Package(deck_audio_to_pinyin, media_files).write_to_file(OUTPUT_APKG_A2P)
print(f"\nAnki decks created: {OUTPUT_APKG_P2A}, {OUTPUT_APKG_A2P}")