import csv
import requests
from bs4 import BeautifulSoup

def fetch_character_mdbg(pinyin):
    try:
        url = f"https://www.mdbg.net/chinese/dictionary?page=worddict&wdrst=0&wdqb={pinyin}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        hanzi = soup.find('div', class_='hanzi')
        if hanzi:
            character = hanzi.text.strip().split()[0]
            return character
        return ''
    except Exception as e:
        print(f"Error fetching character for {pinyin}: {e}")
        return ''

def fill_missing_characters(input_path, output_path):
    with open(input_path, newline='', encoding='utf-8') as infile, \
         open(output_path, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if row['Exists'] == 'Yes' and not row['Character(s)']:
                pinyin = row['FullPinyin']
                print(f"Fetching: {pinyin}")
                char = fetch_character_mdbg(pinyin)
                row['Character(s)'] = char
            writer.writerow(row)

if __name__ == "__main__":
    fill_missing_characters("pinyin_word_lookup.csv", "pinyin_word_lookup_filled.csv")