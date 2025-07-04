import os

mp3_folder = 'mp3'
legal_file = 'legal_syllables.txt'

with open(legal_file, encoding='utf-8') as f:
    legal = set(line.strip() for line in f if line.strip())

folder = set()
for fname in os.listdir(mp3_folder):
    if fname.endswith('.mp3'):
        # Strip off the tone and .mp3
        root = fname[:-5] if fname[-5] in '12345' else fname[:-4]
        folder.add(root)

missing = legal - folder
extra = folder - legal

print(f"Legal syllables: {len(legal)}")
print(f"Unique mp3 stems: {len(folder)}")
print("\nMissing syllables from mp3 folder:")
for s in sorted(missing): print(s)
print("\nUnexpected syllables in mp3 folder:")
for s in sorted(extra): print(s)