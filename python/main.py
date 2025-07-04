import genanki
import re
import os

# ---- CONFIG ----
MP3_FOLDER = '/Users/devyn/Downloads/pinyin_anki/mp3'
FILES_TXT = 'files.txt'
OUTPUT_APKG = 'Pinyin-Audio-Bidirectional.apkg'
DECK_NAME = 'Mandarin Pinyin Bidirectional'
DECK_ID = 202407041
MODEL_ID = 202407042

# ---- HELPERS ----

TONE_MAP = {
    'a': ['ā', 'á', 'ǎ', 'à'],
    'e': ['ē', 'é', 'ě', 'è'],
    'i': ['ī', 'í', 'ǐ', 'ì'],
    'o': ['ō', 'ó', 'ǒ', 'ò'],
    'u': ['ū', 'ú', 'ǔ', 'ù'],
    'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ'],
}

def pinyin_with_tone(syllable, tone):
    # Convert uu (as used in files) to ü
    syllable = syllable.replace('uu', 'ü')
    vowels = 'aeiouü'
    if tone == 5 or tone == 0:
        return syllable
    for v in 'aoe':
        if v in syllable:
            idx = syllable.index(v)
            return syllable[:idx] + TONE_MAP[v][tone - 1] + syllable[idx+1:]
    if 'iu' in syllable:
        idx = syllable.index('u')
        return syllable[:idx] + TONE_MAP['u'][tone - 1] + syllable[idx+1:]
    if 'ui' in syllable:
        idx = syllable.index('i')
        return syllable[:idx] + TONE_MAP['i'][tone - 1] + syllable[idx+1:]
    for i in range(len(syllable) - 1, -1, -1):
        if syllable[i] in vowels:
            v = syllable[i]
            return syllable[:i] + TONE_MAP[v][tone - 1] + syllable[i+1:]
    return syllable

# ---- READ FILES ----

with open(FILES_TXT, 'r', encoding='utf-8') as f:
    filenames = [line.strip() for line in f if line.strip()]

# ---- ANKI MODEL ----

model = genanki.Model(
    MODEL_ID,
    'Pinyin Bidirectional Model',
    fields=[
        {'name': 'Pinyin'},
        {'name': 'Audio'},
    ],
    templates=[
        {
            'name': 'Pinyin→Audio',
            'qfmt': '{{Pinyin}}',
            'afmt': '{{FrontSide}}<hr id="answer">{{Audio}}',
        },
        {
            'name': 'Audio→Pinyin',
            'qfmt': '{{Audio}}',
            'afmt': '{{FrontSide}}<hr id="answer">{{Pinyin}}',
        },
    ])

deck = genanki.Deck(DECK_ID, DECK_NAME)
media_files = []

# ---- BUILD CARDS ----

for fname in filenames:
    base = os.path.basename(fname)
    # Accept uu for ü
    match = re.match(r"([a-z]+|[a-z]+uu)([1-5])\.mp3", base)
    if not match:
        print(f"SKIP (not matched): {fname}")
        continue
    syllable, tone = match.group(1), int(match.group(2))
    pinyin = pinyin_with_tone(syllable, tone)
    note = genanki.Note(
        model=model,
        fields=[
            pinyin, f"[sound:{base}]"
        ])
    deck.add_note(note)
    media_files.append(os.path.join(MP3_FOLDER, base))

# ---- EXPORT ----

genanki.Package(deck, media_files).write_to_file(OUTPUT_APKG)
print(f"\nAnki deck created: {OUTPUT_APKG}")