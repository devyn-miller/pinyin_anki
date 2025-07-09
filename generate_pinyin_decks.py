import os
import pandas as pd
import genanki
import html
import logging
from typing import Dict, List, Optional, Tuple, Set

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants for tone colors
TONE_COLORS = {
    1: "#e33737",  # Red
    2: "#e39c37",  # Orange
    3: "#5cb85c",  # Green
    4: "#428bca",  # Blue
}

# Anki model IDs (must be unique and constant)
PINYIN_TO_AUDIO_MODEL_ID = 1589547384
AUDIO_TO_PINYIN_MODEL_ID = 1589547385

class PinyinDeckGenerator:
    def __init__(self, csv_path: str, mp3_dir: str):
        self.csv_path = csv_path
        self.mp3_dir = mp3_dir
        self.df: pd.DataFrame = pd.DataFrame()
        self.valid_audio_files: Set[str] = set()

    def load_and_validate_data(self) -> None:
        """Load CSV data and validate audio files."""
        # Read CSV file
        self.df = pd.read_csv(self.csv_path, sep=';')
        
        # Get list of available audio files
        self.valid_audio_files = {
            f for f in os.listdir(self.mp3_dir) if f.endswith('.mp3')
        }
        
        # Filter and clean data
        self.df = self.df[
            (self.df['Tone'].between(1, 4)) &  # Only tones 1-4
            (self.df['Audio'].isin(self.valid_audio_files))  # Audio must exist
        ].copy()

        # Clean HTML entities in Meaning column
        self.df['Meaning'] = self.df['Meaning'].fillna('').apply(html.unescape)

    def create_pinyin_models(self) -> Tuple[genanki.Model, genanki.Model]:
        """Create Anki models for both deck types."""
        # Shared styling
        shared_css = """
        .card {
            font-family: Arial, sans-serif;
            font-size: 20px;
            text-align: center;
            color: black;
            background-color: white;
            padding: 20px;
        }
        .pinyin {
            font-size: 40px;
            margin: 20px 0;
        }
        .characters {
            font-size: 48px;
            font-weight: bold;
            margin: 20px 0;
        }
        .meaning {
            font-size: 24px;
            color: #666;
            margin: 20px 0;
            white-space: pre-line;
        }
        """

        # Pinyin to Audio model
        pinyin_to_audio = genanki.Model(
            PINYIN_TO_AUDIO_MODEL_ID,
            'Pinyin to Audio',
            fields=[
                {'name': 'Pinyin'},
                {'name': 'ColoredPinyin'},
                {'name': 'Audio'},
                {'name': 'Characters'},
                {'name': 'Meaning'}
            ],
            templates=[{
                'name': 'Pinyin to Audio Card',
                'qfmt': '''
                    <div class="pinyin">{{ColoredPinyin}}</div>
                ''',
                'afmt': '''
                    <div class="pinyin">{{ColoredPinyin}}</div>
                    {{Audio}}<br>
                    <div class="characters">{{Characters}}</div>
                    <hr>
                    <div class="meaning">{{Meaning}}</div>
                '''
            }],
            css=shared_css
        )

        # Audio to Pinyin model
        audio_to_pinyin = genanki.Model(
            AUDIO_TO_PINYIN_MODEL_ID,
            'Audio to Pinyin',
            fields=[
                {'name': 'Pinyin'},
                {'name': 'ColoredPinyin'},
                {'name': 'Audio'},
                {'name': 'Characters'},
                {'name': 'Meaning'}
            ],
            templates=[{
                'name': 'Audio to Pinyin Card',
                'qfmt': '''
                    {{Audio}}
                ''',
                'afmt': '''
                    {{Audio}}<br>
                    <div class="pinyin">{{ColoredPinyin}}</div>
                    <div class="characters">{{Characters}}</div>
                    <hr>
                    <div class="meaning">{{Meaning}}</div>
                '''
            }],
            css=shared_css
        )

        return pinyin_to_audio, audio_to_pinyin

    def format_pinyin(self, syllable: str, tone: int) -> str:
        """Format pinyin with correct diacritics and color."""
        vowel_order = 'aeiouü'
        syllable = syllable.replace('uu', 'ü')
        
        # Find the vowel to modify
        vowels_in_syllable = [v for v in syllable if v.lower() in vowel_order]
        if not vowels_in_syllable:
            return syllable
        
        # Determine which vowel gets the tone mark
        if len(vowels_in_syllable) == 1:
            vowel_to_mark = vowels_in_syllable[0]
        else:
            # Handle special cases like 'iu', 'ui', etc.
            vowel_pairs = {'iu': 'u', 'ui': 'i', 'iu': 'u', 'ia': 'a', 'ua': 'a'}
            for pair, marked in vowel_pairs.items():
                if pair in syllable.lower():
                    vowel_to_mark = syllable[syllable.lower().index(marked)]
                    break
            else:
                vowel_to_mark = vowels_in_syllable[0]

        # Tone marks for each vowel
        tone_marks = {
            'a': 'āáǎà', 'e': 'ēéěè', 'i': 'īíǐì',
            'o': 'ōóǒò', 'u': 'ūúǔù', 'ü': 'ǖǘǚǜ'
        }

        # Replace the vowel with its tone-marked version
        vowel_lower = vowel_to_mark.lower()
        if vowel_lower in tone_marks:
            tone_vowel = tone_marks[vowel_lower][tone - 1]
            if vowel_to_mark.isupper():
                tone_vowel = tone_vowel.upper()
            
            # Apply color to the tone-marked vowel
            colored_vowel = f'<span style="color: {TONE_COLORS[tone]}">{tone_vowel}</span>'
            return syllable.replace(vowel_to_mark, colored_vowel)
        
        return syllable

    def create_note(self, row: pd.Series, model: genanki.Model) -> genanki.Note:
        """Create an Anki note from a row of data."""
        # Format the pinyin with tone marks and color
        colored_pinyin = self.format_pinyin(row['Syllable'], row['Tone'])
        
        # Format meaning (split on slashes and make one per line)
        meaning = row['Meaning'] if pd.notna(row['Meaning']) else ''
        meaning = meaning.replace(' / ', '\n')
        
        # Create note fields
        fields = [
            row['Syllable'],  # Plain pinyin
            colored_pinyin,   # Colored pinyin with tone marks
            f'[sound:{row["Audio"]}]',  # Audio reference
            row['Character(s)'] if pd.notna(row['Character(s)']) else '',  # Characters
            meaning  # Formatted meaning
        ]
        
        return genanki.Note(model=model, fields=fields)

    def generate_decks(self) -> None:
        """Generate both Anki decks."""
        # Create models
        pinyin_to_audio_model, audio_to_pinyin_model = self.create_pinyin_models()
        
        # Create decks
        pinyin_to_audio_deck = genanki.Deck(
            1589547386,
            'Mandarin Pinyin to Audio'
        )
        audio_to_pinyin_deck = genanki.Deck(
            1589547387,
            'Mandarin Audio to Pinyin'
        )

        # Add notes to decks
        for _, row in self.df.iterrows():
            try:
                # Create notes for both decks
                pinyin_note = self.create_note(row, pinyin_to_audio_model)
                audio_note = self.create_note(row, audio_to_pinyin_model)
                
                # Add notes to respective decks
                pinyin_to_audio_deck.add_note(pinyin_note)
                audio_to_pinyin_deck.add_note(audio_note)
                
            except Exception as e:
                logging.error(f"Error processing row {row['Syllable']}{row['Tone']}: {str(e)}")

        # Create media collection
        media_files = [
            os.path.join(self.mp3_dir, audio_file)
            for audio_file in self.valid_audio_files
            if audio_file in self.df['Audio'].values
        ]

        # Generate package files
        genanki.Package(pinyin_to_audio_deck, media_files).write_to_file('Pinyin-to-Audio.apkg')
        genanki.Package(audio_to_pinyin_deck, media_files).write_to_file('Audio-to-Pinyin.apkg')
        
        logging.info(f"Generated decks with {len(self.df)} cards each")

def main():
    """Main function to run the deck generation."""
    try:
        generator = PinyinDeckGenerator(
            csv_path='pinyin_word_lookup_filled1.csv',
            mp3_dir='mp3'
        )
        
        # Load and validate data
        logging.info("Loading and validating data...")
        generator.load_and_validate_data()
        
        # Generate decks
        logging.info("Generating Anki decks...")
        generator.generate_decks()
        
        logging.info("Deck generation completed successfully!")
        
    except Exception as e:
        logging.error(f"Error generating decks: {str(e)}")
        raise

if __name__ == '__main__':
    main() 