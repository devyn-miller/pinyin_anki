import csv
import re

CSV_PATH = 'pinyin_word_lookup_filled1.csv'

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

def load_meanings(csv_path):
    lookup = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            full_pinyin = row['FullPinyin'].strip()
            chars = row['Character(s)'].strip()
            simplified = chars.split()[0] if chars else ''
            meaning = row['Meaning'].strip()
            formatted_meaning = "<div style='font-size: 1.5em;'>" + simplified + "</div><div style='margin-top: 5px;'>" + "<br>".join(meaning.split('/')) + "</div>"
            lookup[full_pinyin] = formatted_meaning
    return lookup

# ---- MAIN TEST ----

syllable = 'zuo'
tone = 4
audio_file = f'{syllable}{tone}.mp3'
csv_path = CSV_PATH
lookup = load_meanings(csv_path)

pinyin_html = pinyin_with_tone(syllable, tone)
full_pinyin = syllable + str(tone)
meaning = lookup.get(full_pinyin, '[Not found]')

print("== Pinyin to Audio ==")
print("Front:")
print(pinyin_html)
print("Back:")
print(pinyin_html)
print(f"[sound:{audio_file}]")
print(meaning)

print("\n== Audio to Pinyin ==")
print("Front:")
print(f"[sound:{audio_file}]")
print("Back:")
print(f"[sound:{audio_file}]")
print(pinyin_html)
print(meaning)