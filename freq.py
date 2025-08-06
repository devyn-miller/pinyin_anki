import pandas as pd
import genanki
import random
import time
from typing import List, Dict, Optional
import requests
import json
import re
import os

class ChineseAnkiConverter:
    def __init__(self):
        # Generate unique model IDs
        self.definition_model_id = random.randrange(1 << 30, 1 << 31)
        self.sentence_model_id = random.randrange(1 << 30, 1 << 31)
        
        # Create card models
        self.definition_model = self._create_definition_model()
        self.sentence_model = self._create_sentence_model()
        
        # Create deck
        self.deck_id = random.randrange(1 << 30, 1 << 31)
        self.deck = genanki.Deck(self.deck_id, 'Chinese Vocabulary')
        
        # Debug counters
        self.skipped_rows = 0
        self.processed_rows = 0
        self.error_rows = 0
        self.skipped_reasons = {}
    
    def _create_definition_model(self):
        """Create model for Definition → Word cards"""
        return genanki.Model(
            self.definition_model_id,
            'Chinese Definition to Word',
            fields=[
                {'name': 'Meaning'},
                {'name': 'Word'},
                {'name': 'Pinyin'},
                {'name': 'PartOfSpeech'},
                {'name': 'ChineseExample'},
                {'name': 'SentencePinyin'},
                {'name': 'EnglishTranslation'}
            ],
            templates=[
                {
                    'name': 'Definition to Word',
                    'qfmt': '''
                        <div class="front">
                            <div class="meaning">{{Meaning}}</div>
                        </div>
                    ''',
                    'afmt': '''
                        <div class="back">
                            <div class="word">{{Word}}</div>
                            <div class="pinyin">{{Pinyin}}</div>
                            <div class="pos">{{PartOfSpeech}}</div>
                            <hr>
                            <div class="notes">
                                <div class="example">{{ChineseExample}}</div>
                                <div class="sentence-pinyin">{{SentencePinyin}}</div>
                                <div class="translation">{{EnglishTranslation}}</div>
                            </div>
                        </div>
                    ''',
                }
            ],
            css='''
                .card {
                    font-family: "Noto Sans CJK SC", "Source Han Sans", "Microsoft YaHei", sans-serif;
                    text-align: center;
                    color: #333;
                    background-color: #fafafa;
                    padding: 20px;
                }
                
                .front .meaning {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c5aa0;
                    padding: 20px;
                    border: 2px solid #2c5aa0;
                    border-radius: 10px;
                    background-color: white;
                }
                
                .back .word {
                    font-size: 36px;
                    font-weight: bold;
                    color: #d73502;
                    margin-bottom: 10px;
                }
                
                .back .pinyin {
                    font-size: 20px;
                    color: #666;
                    font-style: italic;
                    margin-bottom: 5px;
                }
                
                .back .pos {
                    font-size: 16px;
                    color: #888;
                    margin-bottom: 15px;
                }
                
                .notes {
                    text-align: left;
                    font-size: 14px;
                    color: #555;
                    background-color: #f9f9f9;
                    padding: 10px;
                    border-radius: 5px;
                }
                
                .notes .example {
                    margin-bottom: 8px;
                    font-size: 16px;
                }
                
                .notes .sentence-pinyin {
                    font-size: 14px;
                    color: #666;
                    font-style: italic;
                    margin-bottom: 8px;
                }
                
                .notes .translation {
                    font-style: italic;
                    color: #2c5aa0;
                }
                
                hr {
                    border: 1px solid #ddd;
                    margin: 15px 0;
                }
                
                b {
                    color: #d73502;
                    font-weight: bold;
                }
            '''
        )
    
    def _create_sentence_model(self):
        """Create model for Sentence → Word cards"""
        return genanki.Model(
            self.sentence_model_id,
            'Chinese Sentence to Word',
            fields=[
                {'name': 'ChineseSentence'},
                {'name': 'SentencePinyin'},
                {'name': 'EnglishTranslation'},
                {'name': 'Word'},
                {'name': 'Pinyin'},
                {'name': 'PartOfSpeech'},
                {'name': 'Meaning'}
            ],
            templates=[
                {
                    'name': 'Sentence to Word',
                    'qfmt': '''
                        <div class="front">
                            <div class="english-sentence">{{EnglishTranslation}}</div>
                        </div>
                    ''',
                    'afmt': '''
                        <div class="back">
                            <div class="chinese-sentence">{{ChineseSentence}}</div>
                            <div class="sentence-pinyin">{{SentencePinyin}}</div>
                            <hr>
                            <div class="vocab-info">
                                <div class="word">{{Word}} ({{Pinyin}})</div>
                                <div class="meaning">{{Meaning}}</div>
                                <div class="pos">{{PartOfSpeech}}</div>
                            </div>
                        </div>
                    ''',
                }
            ],
            css='''
                .card {
                    font-family: "Noto Sans CJK SC", "Source Han Sans", "Microsoft YaHei", sans-serif;
                    text-align: center;
                    color: #333;
                    background-color: #fafafa;
                    padding: 20px;
                }
                
                .front .english-sentence {
                    font-size: 24px;
                    color: #2c5aa0;
                    padding: 20px;
                    border: 2px solid #2c5aa0;
                    border-radius: 10px;
                    background-color: white;
                    line-height: 1.4;
                }
                
                .back .chinese-sentence {
                    font-size: 28px;
                    color: #d73502;
                    font-weight: bold;
                    margin-bottom: 5px;
                    line-height: 1.3;
                }
                
                .back .sentence-pinyin {
                    font-size: 16px;
                    color: #666;
                    font-style: italic;
                    margin-bottom: 15px;
                }
                
                .vocab-info {
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: left;
                }
                
                .vocab-info .word {
                    font-size: 20px;
                    font-weight: bold;
                    color: #d73502;
                    margin-bottom: 5px;
                }
                
                .vocab-info .meaning {
                    font-size: 16px;
                    color: #333;
                    margin-bottom: 3px;
                }
                
                .vocab-info .pos {
                    font-size: 14px;
                    color: #666;
                    font-style: italic;
                }
                
                hr {
                    border: 1px solid #ddd;
                    margin: 15px 0;
                }
                
                b {
                    color: #d73502;
                    font-weight: bold;
                }
            '''
        )
    
    def process_example_sentence(self, sentence: str, word: str) -> str:
        """
        Process the example sentence by replacing tildes with the target word 
        and highlighting the target word with bold tags
        """
        if not sentence or sentence == 'nan':
            return ""
            
        # Replace tilde with the target word in bold
        if '～' in sentence or '~' in sentence:
            formatted_sentence = sentence.replace('～', f'<b>{word}</b>')
            formatted_sentence = formatted_sentence.replace('~', f'<b>{word}</b>')
            return formatted_sentence
        
        # If no tilde, try to find and highlight the word
        if word in sentence:
            formatted_sentence = sentence.replace(word, f'<b>{word}</b>')
            return formatted_sentence
            
        # If word not found, return the original sentence
        return sentence
    
    def process_csv_with_pinyin(self, csv_path: str) -> None:
        """Process the CSV file with pinyin sentences and create Anki cards"""
        print(f"Reading CSV file: {csv_path}")
        
        # Read the CSV file without headers
        df = pd.read_csv(csv_path, header=None)
        
        # Check if file has content
        if df.empty:
            print("Error: CSV file is empty")
            return
        
        # Create lists to store word and sentence data
        word_entries = []
        sentence_entries = []
        
        print("Processing CSV file with pinyin...")
        row_count = len(df)
        print(f"Found {row_count} rows in the CSV file")
        
        # Process all rows and collect data
        for i in range(0, len(df), 2):  # Process every other row (definition cards)
            try:
                self.processed_rows += 1
                
                # Skip if there's no matching sentence row
                if i+1 >= len(df):
                    continue
                
                # Get data from definition card (even row)
                meaning = str(df.iloc[i, 0]).strip()
                word = str(df.iloc[i, 1]).strip()
                # Column 2 is empty for definition rows
                pinyin = str(df.iloc[i, 4]).strip()  # Fixed: Pinyin is in column 4
                part_of_speech = str(df.iloc[i, 5]).strip()  # Fixed: Part of speech is in column 5
                chinese_example = str(df.iloc[i, 6]).strip()  # Fixed: Example is in column 6
                
                # Skip empty or invalid rows
                if not word or word == 'nan':
                    reason = "Empty word"
                    self.skipped_rows += 1
                    self.skipped_reasons[reason] = self.skipped_reasons.get(reason, 0) + 1
                    continue
                
                # Get data from sentence card (odd row)
                chinese_sentence = str(df.iloc[i+1, 0]).strip()
                english_translation = str(df.iloc[i+1, 1]).strip()
                sentence_pinyin = str(df.iloc[i+1, 2]).strip()
                
                # Add to word entries list
                word_entries.append({
                    'meaning': meaning,
                    'word': word,
                    'pinyin': pinyin,
                    'part_of_speech': part_of_speech,
                    'chinese_example': chinese_example,
                    'sentence_pinyin': sentence_pinyin,
                    'english_translation': english_translation
                })
                
                # Add to sentence entries list
                sentence_entries.append({
                    'chinese_sentence': chinese_sentence,
                    'sentence_pinyin': sentence_pinyin,
                    'english_translation': english_translation,
                    'word': word,
                    'pinyin': pinyin,
                    'part_of_speech': part_of_speech,
                    'meaning': meaning
                })
                
            except Exception as e:
                self.error_rows += 1
                print(f"Error processing row {i}: {e}")
                continue
        
        print(f"Collected {len(word_entries)} word entries")
        print(f"Collected {len(sentence_entries)} sentence entries")
        
        # Create cards from collected data
        word_cards_created = 0
        sentence_cards_created = 0
        
        # Create word cards
        for entry in word_entries:
            try:
                # Format the example sentence
                formatted_example = self.process_example_sentence(entry['chinese_example'], entry['word'])
                
                # Create Definition → Word card
                definition_note = genanki.Note(
                    model=self.definition_model,
                    fields=[
                        entry['meaning'],  # Meaning
                        entry['word'],  # Word
                        entry['pinyin'],  # Pinyin
                        entry['part_of_speech'],  # Part of Speech
                        formatted_example,  # Chinese Example with formatting
                        entry['sentence_pinyin'],  # Sentence Pinyin
                        entry['english_translation']  # English Translation
                    ]
                )
                self.deck.add_note(definition_note)
                word_cards_created += 1
            except Exception as e:
                print(f"Error creating definition card for {entry['word']}: {e}")
        
        # Create sentence cards
        for entry in sentence_entries:
            try:
                # Format the sentence with the word highlighted
                formatted_sentence = self.process_example_sentence(entry['chinese_sentence'], entry['word'])
                
                # Create Sentence → Word card
                sentence_note = genanki.Note(
                    model=self.sentence_model,
                    fields=[
                        formatted_sentence,  # Chinese Sentence with formatting
                        entry['sentence_pinyin'],  # Sentence Pinyin
                        entry['english_translation'],  # English Translation
                        entry['word'],  # Word
                        entry['pinyin'],  # Pinyin
                        entry['part_of_speech'],  # Part of Speech
                        entry['meaning']  # Meaning
                    ]
                )
                self.deck.add_note(sentence_note)
                sentence_cards_created += 1
            except Exception as e:
                print(f"Error creating sentence card for {entry['chinese_sentence']}: {e}")
        
        # Print detailed statistics
        print("\n=== Processing Statistics ===")
        print(f"Total rows in CSV: {row_count}")
        print(f"Rows processed: {self.processed_rows}")
        print(f"Rows skipped: {self.skipped_rows}")
        print(f"Rows with errors: {self.error_rows}")
        print(f"Word cards created: {word_cards_created}")
        print(f"Sentence cards created: {sentence_cards_created}")
        print(f"Total cards created: {len(self.deck.notes)}")
        
        if self.skipped_rows > 0:
            print("\nSkipped rows by reason:")
            for reason, count in self.skipped_reasons.items():
                print(f"  - {reason}: {count}")
    
    def export_deck(self, output_path: str) -> None:
        """Export the deck to an .apkg file"""
        print(f"Exporting deck to: {output_path}")
        
        package = genanki.Package(self.deck)
        package.write_to_file(output_path)
        
        print("Export completed successfully!")
    
    def convert(self, csv_path: str, output_path: str) -> None:
        """Main conversion function"""
        print("=== Chinese Vocabulary to Anki Converter ===")
        
        try:
            self.process_csv_with_pinyin(csv_path)
            self.export_deck(output_path)
            
            print(f"\n✅ Success! Created Anki deck with {len(self.deck.notes)} cards")
            print(f"📁 Output file: {output_path}")
            
        except Exception as e:
            print(f"❌ Error during conversion: {e}")

def main():
    """Example usage"""
    converter = ChineseAnkiConverter()
    
    # Specify your file paths
    csv_file = "chinese_vocab_with_pinyin.csv"  # Use the CSV file with pinyin
    output_file = "chinese_vocabulary_deck.apkg"  # Output Anki deck file
    
    # Convert
    converter.convert(csv_file, output_file)

if __name__ == "__main__":
    main()

# INSTALLATION REQUIREMENTS:
# pip install genanki pandas openpyxl requests