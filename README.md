# Mandarin Pinyin Anki Deck Generator

This script generates two Anki decks for learning Mandarin Chinese Pinyin syllables:
1. Pinyin-to-Audio.apkg: Practice recognizing Pinyin and hearing the correct pronunciation
2. Audio-to-Pinyin.apkg: Practice identifying Pinyin from audio

## Features

- Generates two complementary Anki decks
- Properly formats Pinyin with tone marks and colors
- Includes audio for all syllables
- Shows Chinese characters and meanings when available
- Mobile-friendly card layout
- Validates all inputs and skips invalid entries
- Logs processing details and errors

## Requirements

```bash
pip install -r requirements.txt
```

## Input Files

1. CSV file (UTF-8 encoded) with columns:
   - Syllable: Base Pinyin (e.g., "ba")
   - Tone: Number 1-4
   - FullPinyin: Combined syllable and tone (e.g., "ba1")
   - Exists: "Yes" or "No" (for reference only)
   - Character(s): Optional Chinese characters
   - Meaning: Optional English definitions (slash-separated)
   - Audio: MP3 filename
   - Reference: Anki audio reference (optional)

2. MP3 files:
   - One file per syllable+tone combination
   - Named exactly as specified in the CSV's Audio column
   - Located in the `mp3/` directory

## Usage

1. Place your CSV file as `pinyin_word_lookup_filled1.csv` in the script directory
2. Place all MP3 files in the `mp3/` directory
3. Run the script:
   ```bash
   python generate_pinyin_decks.py
   ```
4. Import the generated .apkg files into Anki

## Card Formats

### Pinyin-to-Audio Deck
- Front: Colored Pinyin with tone marks
- Back:
  - Colored Pinyin
  - Audio playback
  - Chinese characters (if available)
  - English meaning (if available)

### Audio-to-Pinyin Deck
- Front: Audio playback only
- Back:
  - Colored Pinyin with tone marks
  - Chinese characters (if available)
  - English meaning (if available)

## Tone Colors

- Tone 1 (ā): Red (#e33737)
- Tone 2 (á): Orange (#e39c37)
- Tone 3 (ǎ): Green (#5cb85c)
- Tone 4 (à): Blue (#428bca)

## Validation

The script performs the following validations:
- Checks for valid tone numbers (1-4)
- Verifies audio file existence
- Validates CSV format and required columns
- Handles missing optional fields gracefully
- Logs any processing errors or skipped entries

## Output

Two .apkg files ready for import into Anki:
- Pinyin-to-Audio.apkg
- Audio-to-Pinyin.apkg

All audio files are embedded in the decks, making them fully portable. 