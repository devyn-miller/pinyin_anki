# Save your chart to syllable_chart.csv first (no header row)
input_file = '1.csv'
output_file = 'legal_syllables.txt'

with open(input_file, 'r', encoding='utf-8') as fin, open(output_file, 'w', encoding='utf-8') as fout:
    sylls = set()
    for line in fin:
        for item in line.strip().split(','):
            s = item.strip()
            if s:  # skip empty
                sylls.add(s)
    for s in sorted(sylls):
        fout.write(s + '\n')
print(f"Saved {len(sylls)} unique syllables to {output_file}")



#muo: missing tones 1, 2, 4
#nue: missing tones 2, 3, 4
#nuo: missing tones 1
#nuue: missing tones 1
#rei: missing tones 2, 3, 4

