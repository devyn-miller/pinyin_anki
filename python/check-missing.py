import os
import re
from collections import defaultdict

MP3_FOLDER = 'mp3'

# Map: syllable -> set of tones present
syllable_tones = defaultdict(set)

for fname in os.listdir(MP3_FOLDER):
    match = re.match(r"([a-z]+|[a-z]+uu)([1-4])\.mp3$", fname)
    if match:
        syllable, tone = match.group(1), int(match.group(2))
        syllable_tones[syllable].add(tone)

# Report missing tones 1–4 for each syllable
for syllable in sorted(syllable_tones):
    missing = [str(t) for t in range(1, 5) if t not in syllable_tones[syllable]]
    if missing:
        print(f"{syllable}: missing tones {', '.join(missing)}")

# Also, list any syllables present in the folder without ANY of tones 1–4
# (e.g. 'zhai.mp3' with no numbered version)
all_files = set(os.listdir(MP3_FOLDER))
unnumbered = set()
for fname in all_files:
    base = fname[:-4] if fname.endswith('.mp3') else None
    if base and not re.match(r".*[1-4]$", base):
        unnumbered.add(base)
if unnumbered:
    print("\nUnnumbered syllables detected (no tone number):")
    for base in sorted(unnumbered):
        print(base)