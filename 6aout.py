#!/usr/bin/env python3
"""
CSV to Anki Cards Generator
Converts CSV files with Chinese language learning data into Anki .apkg files
Supports two card types: Definition→Word and Sentence→English+Word Info
Uses Anki's built-in TTS for Chinese audio
"""

import csv
import re
import sys
import argparse
import logging
from typing import List, Tuple, Optional, Dict, Any
import genanki
import random
import os  # Needed for path operations


class AnkiCardGenerator:
    def __init__(self, deck_name: str = "Chinese Learning Deck", chunk_size: int = 20):
        self.deck_name = deck_name
        self.chunk_size = chunk_size
        self.deck_id = random.randrange(1 << 30, 1 << 31)
        
        # Define card models
        self.type1_model = genanki.Model(
            random.randrange(1 << 30, 1 << 31),
            'Chinese Definition to Word',
            fields=[
                {'name': 'English'},
                {'name': 'Hanzi'},
                {'name': 'Pinyin'},
                {'name': 'POS'},
                {'name': 'ExampleHanzi'},
                {'name': 'ExampleEnglish'},
                {'name': 'ExamplePinyin'},
            ],
            templates=[
                {
                    'name': 'Definition → Word',
                    'qfmt': '''
                    <div class="front">
                        <div class="english">{{English}}</div>
                    </div>
                    ''',
                    'afmt': '''
                    <div class="back">
                        <!-- Include front content -->
                        <div class="front-content">
                            <div class="english">{{English}}</div>
                        </div>
                        <hr>
                        <!-- Back content -->
                        <div class="hanzi">{{Hanzi}}</div>
                        <div class="pinyin">{{Pinyin}}</div>
                        <div class="pos">{{POS}}</div>
                        <div class="audio-controls">
                            <div class="audio-label">Word:</div>
                            <div class="audio-buttons">
                                <button onclick="playTTS('{{Hanzi}}', 1.0)">▶️ Normal</button>
                                <button onclick="playTTS('{{Hanzi}}', 0.7)">🐢 Slow</button>
                                <button onclick="playTTS('{{Hanzi}}', 0.5)">🐌 Very Slow</button>
                            </div>
                        </div>
                        {{#ExampleHanzi}}
                        <hr>
                        <div class="example-section">
                            <div class="example-hanzi">{{ExampleHanzi}}</div>
                            {{#ExamplePinyin}}<div class="example-pinyin">{{ExamplePinyin}}</div>{{/ExamplePinyin}}
                            {{#ExampleEnglish}}<div class="example-english">{{ExampleEnglish}}</div>{{/ExampleEnglish}}
                            <div class="audio-controls">
                                <div class="audio-label">Example:</div>
                                <div class="audio-buttons">
                                    <button onclick="playTTS('{{ExampleHanzi}}', 1.0)">▶️ Normal</button>
                                    <button onclick="playTTS('{{ExampleHanzi}}', 0.7)">🐢 Slow</button>
                                    <button onclick="playTTS('{{ExampleHanzi}}', 0.5)">🐌 Very Slow</button>
                                </div>
                            </div>
                        </div>
                        {{/ExampleHanzi}}

                        <!-- Hidden TTS elements that Anki will use -->
                        <div style="display: none;">
                            {{tts zh_CN:Hanzi}}
                            {{#ExampleHanzi}}{{tts zh_CN:ExampleHanzi}}{{/ExampleHanzi}}
                        </div>

                        <!-- JavaScript for custom TTS playback with speed control -->
                        <script>
                            function playTTS(text, speed) {
                                // Create a speechSynthesis utterance
                                const utterance = new SpeechSynthesisUtterance(text);
                                
                                // Set language to Mandarin Chinese
                                utterance.lang = 'zh-CN';
                                
                                // Set the speech rate
                                utterance.rate = speed;
                                
                                // Speak the utterance
                                window.speechSynthesis.speak(utterance);
                            }
                        </script>
                    </div>
                    ''',
                },
            ],
            css='''
            .card {
                font-family: Arial, sans-serif;
                font-size: 20px;
                text-align: center;
                color: black;
                background-color: white;
                padding: 20px;
            }
            .front .english {
                font-size: 24px;
                font-weight: bold;
                color: #2E86AB;
                margin-bottom: 20px;
            }
            .front-content {
                margin-bottom: 15px;
            }
            .back .hanzi {
                font-size: 36px;
                font-weight: bold;
                color: #A23B72;
                margin-bottom: 10px;
            }
            .back .pinyin {
                font-size: 20px;
                color: #F18F01;
                margin-bottom: 10px;
            }
            .back .pos {
                font-size: 16px;
                color: #666;
                font-style: italic;
                margin-bottom: 15px;
            }
            .audio-controls {
                margin: 15px 0;
            }
            .audio-label {
                font-weight: bold;
                margin-bottom: 5px;
                color: #333;
            }
            .audio-buttons {
                display: flex;
                justify-content: center;
                gap: 10px;
                flex-wrap: wrap;
            }
            .audio-buttons button {
                background-color: #2E86AB;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.2s;
            }
            .audio-buttons button:hover {
                background-color: #1A6A8F;
            }
            .example-section {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
            }
            .example-hanzi {
                font-size: 18px;
                margin-bottom: 8px;
            }
            .example-pinyin {
                font-size: 16px;
                color: #F18F01;
                margin-bottom: 8px;
            }
            .example-english {
                font-size: 16px;
                color: #666;
            }
            .highlight {
                background-color: #FFEB3B;
                font-weight: bold;
                color: #D32F2F;
            }
            hr {
                border: 0;
                height: 1px;
                background-color: #ddd;
                margin: 15px 0;
            }
            '''
        )
        
        self.type2_model = genanki.Model(
            random.randrange(1 << 30, 1 << 31),
            'Chinese Sentence to Translation',
            fields=[
                {'name': 'ChineseSentence'},
                {'name': 'PinyinSentence'},
                {'name': 'EnglishTranslation'},
                {'name': 'TargetWord'},
                {'name': 'TargetPinyin'},
                {'name': 'POS'},
                {'name': 'Meaning'},
            ],
            templates=[
                {
                    'name': 'Sentence → Translation + Word Info',
                    'qfmt': '''
                    <div class="front">
                        <div class="chinese-sentence">{{ChineseSentence}}</div>
                        {{#PinyinSentence}}<div class="pinyin-sentence">{{PinyinSentence}}</div>{{/PinyinSentence}}
                        
                        <div class="audio-controls">
                            <div class="audio-buttons">
                                <button onclick="playTTS('{{ChineseSentence}}', 1.0)">▶️ Normal</button>
                                <button onclick="playTTS('{{ChineseSentence}}', 0.7)">🐢 Slow</button>
                                <button onclick="playTTS('{{ChineseSentence}}', 0.5)">🐌 Very Slow</button>
                            </div>
                        </div>
                        
                        <!-- Hidden TTS element that Anki will use for auto-play -->
                        <div style="display: none;">
                            {{tts zh_CN:ChineseSentence}}
                        </div>
                        
                        <!-- JavaScript for custom TTS playback with speed control -->
                        <script>
                            function playTTS(text, speed) {
                                // Create a speechSynthesis utterance
                                const utterance = new SpeechSynthesisUtterance(text);
                                
                                // Set language to Mandarin Chinese
                                utterance.lang = 'zh-CN';
                                
                                // Set the speech rate
                                utterance.rate = speed;
                                
                                // Speak the utterance
                                window.speechSynthesis.speak(utterance);
                            }
                        </script>
                    </div>
                    ''',
                    'afmt': '''
                    <div class="back">
                        <!-- Include front content -->
                        <div class="front-content">
                            <div class="chinese-sentence">{{ChineseSentence}}</div>
                            {{#PinyinSentence}}<div class="pinyin-sentence">{{PinyinSentence}}</div>{{/PinyinSentence}}
                            
                            <div class="audio-controls">
                                <div class="audio-buttons">
                                    <button onclick="playTTS('{{ChineseSentence}}', 1.0)">▶️ Normal</button>
                                    <button onclick="playTTS('{{ChineseSentence}}', 0.7)">🐢 Slow</button>
                                    <button onclick="playTTS('{{ChineseSentence}}', 0.5)">🐌 Very Slow</button>
                                </div>
                            </div>
                        </div>
                        <hr>
                        <!-- Back content -->
                        <div class="english-translation">{{EnglishTranslation}}</div>
                        <hr>
                        <div class="word-info">
                            <div class="target-word">{{TargetWord}} ({{TargetPinyin}})</div>
                            <div class="pos">{{POS}}</div>
                            <div class="meaning">{{Meaning}}</div>
                            {{#TargetWord}}
                            <div class="audio-controls">
                                <div class="audio-label">Target Word:</div>
                                <div class="audio-buttons">
                                    <button onclick="playTTS('{{TargetWord}}', 1.0)">▶️ Normal</button>
                                    <button onclick="playTTS('{{TargetWord}}', 0.7)">🐢 Slow</button>
                                    <button onclick="playTTS('{{TargetWord}}', 0.5)">🐌 Very Slow</button>
                                </div>
                            </div>
                            {{/TargetWord}}
                        </div>
                        
                        <!-- Hidden TTS elements that Anki will use -->
                        <div style="display: none;">
                            {{tts zh_CN:ChineseSentence}}
                            {{#TargetWord}}{{tts zh_CN:TargetWord}}{{/TargetWord}}
                        </div>
                        
                        <!-- JavaScript for custom TTS playback with speed control -->
                        <script>
                            function playTTS(text, speed) {
                                // Create a speechSynthesis utterance
                                const utterance = new SpeechSynthesisUtterance(text);
                                
                                // Set language to Mandarin Chinese
                                utterance.lang = 'zh-CN';
                                
                                // Set the speech rate
                                utterance.rate = speed;
                                
                                // Speak the utterance
                                window.speechSynthesis.speak(utterance);
                            }
                        </script>
                    </div>
                    ''',
                },
            ],
            css='''
            .card {
                font-family: Arial, sans-serif;
                font-size: 20px;
                text-align: center;
                color: black;
                background-color: white;
                padding: 20px;
            }
            .front .chinese-sentence {
                font-size: 28px;
                font-weight: bold;
                color: #2E86AB;
                margin-bottom: 15px;
                line-height: 1.4;
            }
            .front .pinyin-sentence {
                font-size: 18px;
                color: #F18F01;
                margin-bottom: 10px;
                line-height: 1.4;
            }
            .front-content {
                margin-bottom: 15px;
            }
            .back .english-translation {
                font-size: 22px;
                color: #A23B72;
                font-weight: bold;
                margin-bottom: 20px;
            }
            .audio-controls {
                margin: 15px 0;
            }
            .audio-label {
                font-weight: bold;
                margin-bottom: 5px;
                color: #333;
            }
            .audio-buttons {
                display: flex;
                justify-content: center;
                gap: 10px;
                flex-wrap: wrap;
            }
            .audio-buttons button {
                background-color: #2E86AB;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.2s;
            }
            .audio-buttons button:hover {
                background-color: #1A6A8F;
            }
            .word-info {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
            }
            .target-word {
                font-size: 20px;
                font-weight: bold;
                color: #2E86AB;
                margin-bottom: 8px;
            }
            .pos {
                font-size: 16px;
                color: #666;
                font-style: italic;
                margin-bottom: 8px;
            }
            .meaning {
                font-size: 18px;
                color: #333;
                margin-bottom: 10px;
            }
            .highlight {
                background-color: #FFEB3B;
                font-weight: bold;
                color: #D32F2F;
            }
            hr {
                border: 0;
                height: 1px;
                background-color: #ddd;
                margin: 15px 0;
            }
            '''
        )
        
        self.deck = genanki.Deck(self.deck_id, self.deck_name)
        self.notes: List[genanki.Note] = []  # Store notes for chunked shuffling
        self.cards_created = 0
        self.rows_skipped = 0

    def contains_hanzi(self, text: str) -> bool:
        """Check if text contains Chinese characters (Hanzi)"""
        return bool(re.search(r'[一-龥]', text))

    def highlight_word_in_text(self, text: str, target_word: str) -> str:
        """Highlight target word in text with HTML styling"""
        if not text or not target_word:
            return text or ""
        
        # Remove any existing highlight spans to avoid double highlighting
        text = re.sub(r'<span class="highlight">(.*?)</span>', r'\1', text)
        
        # For Chinese text, we need exact matching (not case-insensitive)
        if self.contains_hanzi(target_word):
            # Escape special regex characters in target word
            escaped_target = re.escape(target_word)
            # Use word boundaries for Chinese characters
            highlighted_text = re.sub(
                f'({escaped_target})',
                r'<span class="highlight">\1</span>',
                text
            )
        else:
            # For non-Chinese text, use case-insensitive matching with word boundaries
            escaped_target = re.escape(target_word)
            # Add word boundary checks for non-Chinese text
            highlighted_text = re.sub(
                f'\\b({escaped_target})\\b',
                r'<span class="highlight">\1</span>',
                text,
                flags=re.IGNORECASE
            )
        
        return highlighted_text

    def create_type1_card(self, row: List[str]) -> Optional[genanki.Note]:
        """Create Type 1 card: Definition → Word"""
        try:
            # Ensure we have at least the minimum required fields
            if len(row) < 2:
                logging.warning(f"Not enough fields for Type 1 card: {len(row)} fields")
                return None
                
            # Map fields with safe defaults
            english = row[0].strip() if len(row) > 0 else ""
            hanzi = row[1].strip() if len(row) > 1 else ""
            pinyin = row[2].strip() if len(row) > 2 else ""
            pos = row[3].strip() if len(row) > 3 else ""
            example_hanzi = row[4].strip() if len(row) > 4 else ""
            example_english = row[5].strip() if len(row) > 5 else ""
            example_pinyin = row[6].strip() if len(row) > 6 else ""
            
            # Validate required fields
            if not english or not hanzi:
                logging.warning(f"Missing required fields for Type 1 card: English='{english}', Hanzi='{hanzi}'")
                return None
            
            # Clean up pinyin field - remove tone numbers if using diacritics
            pinyin = self.clean_pinyin(pinyin)
            
            # Highlight target word in examples if available
            if example_hanzi and hanzi:
                example_hanzi = self.highlight_word_in_text(example_hanzi, hanzi)
            
            if example_english and english:
                example_english = self.highlight_word_in_text(example_english, english)
            
            if example_pinyin and pinyin:
                # For pinyin, try to highlight the pinyin version
                example_pinyin = self.highlight_word_in_text(example_pinyin, pinyin)
            
            note = genanki.Note(
                model=self.type1_model,
                fields=[
                    english,
                    hanzi,
                    pinyin,
                    pos,
                    example_hanzi,
                    example_english,
                    example_pinyin,
                ]
            )
            return note
            
        except Exception as e:
            logging.error(f"Error creating Type 1 card: {e}")
            return None

    def create_type2_card(self, row: List[str]) -> Optional[genanki.Note]:
        """Create Type 2 card: Sentence → English + Word Info"""
        try:
            # Ensure we have at least the minimum required fields
            if len(row) < 2:
                logging.warning(f"Not enough fields for Type 2 card: {len(row)} fields")
                return None
                
            # Map fields with safe defaults
            chinese_sentence = row[0].strip() if len(row) > 0 else ""
            english_translation = row[1].strip() if len(row) > 1 else ""
            target_word = row[2].strip() if len(row) > 2 else ""
            target_pinyin = row[3].strip() if len(row) > 3 else ""
            pos = row[4].strip() if len(row) > 4 else ""
            meaning = row[5].strip() if len(row) > 5 else ""
            pinyin_sentence = row[6].strip() if len(row) > 6 else ""
            
            # Validate required fields
            if not chinese_sentence or not english_translation:
                logging.warning(f"Missing required fields for Type 2 card: Chinese='{chinese_sentence}', English='{english_translation}'")
                return None
            
            # Clean up pinyin fields
            target_pinyin = self.clean_pinyin(target_pinyin)
            pinyin_sentence = self.clean_pinyin(pinyin_sentence)
            
            # If target word is missing but we can detect it in the sentence
            if not target_word and self.contains_hanzi(chinese_sentence):
                # Try to find a prominent word (this is just a heuristic)
                words = re.findall(r'[\u4e00-\u9fff]+', chinese_sentence)
                if words:
                    # Use the longest word as target (could be improved)
                    target_word = max(words, key=len)
                    logging.info(f"Auto-detected target word: {target_word}")
            
            # Highlight target word in Chinese sentence
            if target_word:
                chinese_sentence = self.highlight_word_in_text(chinese_sentence, target_word)
            
            # Highlight target word in Pinyin sentence
            if pinyin_sentence and target_pinyin:
                pinyin_sentence = self.highlight_word_in_text(pinyin_sentence, target_pinyin)
            
            note = genanki.Note(
                model=self.type2_model,
                fields=[
                    chinese_sentence,
                    pinyin_sentence,
                    english_translation,
                    target_word,
                    target_pinyin,
                    pos,
                    meaning,
                ]
            )
            return note
            
        except Exception as e:
            logging.error(f"Error creating Type 2 card: {e}")
            return None
            
    def clean_pinyin(self, pinyin_text: str) -> str:
        """Clean up pinyin text - handle both number notation and diacritic notation"""
        if not pinyin_text:
            return ""
            
        # Remove tone numbers if using diacritics (assume if we see ā, ē, ī, ō, ū, ǖ)
        if re.search(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]', pinyin_text):
            # Already using diacritics, just clean up any numbers
            return re.sub(r'(\d+)', '', pinyin_text)
        
        # Otherwise leave as is - could be number notation
        return pinyin_text
        
    def process_csv(self, csv_file_path: str) -> None:
        """Process CSV file and create Anki cards"""
        logging.info(f"Processing CSV file: {csv_file_path}")
        
        try:
            # Track problematic rows for reporting
            problematic_rows = []
            encoding_errors = 0
            
            # Try different encodings if UTF-8 fails
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin1']
            file = None
            
            # Try different encodings
            for encoding in encodings:
                try:
                    file = open(csv_file_path, 'r', encoding=encoding)
                    # Read a bit to test encoding
                    file.read(1024)
                    file.seek(0)
                    logging.info(f"Successfully opened file with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    if file:
                        file.close()
                    continue
            
            if not file:
                raise ValueError(f"Could not open file with any of the encodings: {encodings}")
            
            try:
                # Try different CSV dialects
                sample = file.read(1024)
                file.seek(0)
                
                # Detect delimiter
                delimiter = ','  # Default delimiter
                if ';' in sample and sample.count(';') > sample.count(','):
                    delimiter = ';'
                elif '\t' in sample and sample.count('\t') > sample.count(','):
                    delimiter = '\t'
                
                logging.info(f"Using delimiter: '{delimiter}'")
                csv_reader = csv.reader(file, delimiter=delimiter)
                
                # Skip header row if it exists (check first row)
                first_row = next(csv_reader, None)
                if first_row and any(header.lower() in ['word', 'english', 'pinyin', 'hanzi', 'chinese'] 
                                    for header in first_row):
                    logging.info(f"Detected header row: {first_row}")
                else:
                    # If no header detected, reset file pointer and re-create reader
                    file.seek(0)
                    csv_reader = csv.reader(file, delimiter=delimiter)
                
                for row_num, row in enumerate(csv_reader, 1):
                    try:
                        if not row or len(row) == 0:
                            continue
                        
                        # Clean up row data - strip whitespace from all fields
                        row = [field.strip() if field else "" for field in row]
                        
                        # Detect card type based on content patterns
                        first_column = row[0]
                        if not first_column:
                            logging.warning(f"Row {row_num}: Empty first column, skipping")
                            self.rows_skipped += 1
                            continue
                        
                        # More reliable detection of card types
                        if self.contains_hanzi(first_column):
                            # Check if it's a sentence (longer text with spaces or punctuation)
                            if len(first_column) > 5 or any(p in first_column for p in "，。！？,.!?"):
                                note = self.create_type2_card(row)
                                card_type = "Type 2 (Sentence)"
                            else:
                                # Could be a single word in first column - check second column
                                if len(row) > 1 and not self.contains_hanzi(row[1]):
                                    # If second column is not Chinese, it's likely Type 1 with Chinese word first
                                    note = self.create_type1_card([row[1], row[0]] + row[2:])
                                    card_type = "Type 1 (Word - reversed)"
                                else:
                                    # Otherwise treat as Type 2
                                    note = self.create_type2_card(row)
                                    card_type = "Type 2 (Sentence)"
                        else:
                            # First column is not Chinese - check if second column has Chinese
                            if len(row) > 1 and self.contains_hanzi(row[1]):
                                note = self.create_type1_card(row)
                                card_type = "Type 1 (Word)"
                            else:
                                # No Chinese in first two columns - try Type 1 anyway
                                note = self.create_type1_card(row)
                                card_type = "Type 1 (fallback)"
                        
                        if note:
                            self.notes.append(note)  # Store note for chunked shuffling
                            self.cards_created += 1
                            logging.debug(f"Row {row_num}: Created {card_type} card")
                        else:
                            logging.warning(f"Row {row_num}: Failed to create {card_type} card")
                            self.rows_skipped += 1
                            problematic_rows.append((row_num, row, f"Failed to create {card_type} card"))
                    
                    except Exception as row_error:
                        logging.error(f"Error processing row {row_num}: {row_error}")
                        self.rows_skipped += 1
                        problematic_rows.append((row_num, row, str(row_error)))
                
            finally:
                file.close()
            
            # Report problematic rows
            if problematic_rows:
                logging.warning(f"Found {len(problematic_rows)} problematic rows:")
                for row_num, row, error in problematic_rows[:10]:  # Show first 10
                    logging.warning(f"  Row {row_num}: {error} - Data: {row[:3]}...")
                if len(problematic_rows) > 10:
                    logging.warning(f"  ... and {len(problematic_rows) - 10} more problematic rows")
            
        except FileNotFoundError:
            logging.error(f"CSV file not found: {csv_file_path}")
            raise
        except Exception as e:
            logging.error(f"Error processing CSV file: {e}")
            raise

    def apply_chunked_shuffling(self) -> None:
        """
        Apply chunked shuffling to the notes:
        1. Group notes into chunks of specified size (default 20)
        2. Shuffle cards within each chunk, but not across chunks
        3. This maintains some thematic/contextual flow while adding randomness
        """
        if not self.notes:
            return
            
        logging.info(f"Applying chunked shuffling with chunk size: {self.chunk_size}")
        
        # Set fixed seed for reproducibility
        random.seed(42)
        
        # Group notes into chunks
        chunks = []
        for i in range(0, len(self.notes), self.chunk_size):
            chunk = self.notes[i:i + self.chunk_size]
            chunks.append(chunk)
        
        # Shuffle within each chunk
        shuffled_notes = []
        for chunk_idx, chunk in enumerate(chunks):
            random.shuffle(chunk)  # Shuffle within chunk only
            shuffled_notes.extend(chunk)
            logging.debug(f"Shuffled chunk {chunk_idx + 1} with {len(chunk)} cards")
        
        # Add shuffled notes to deck
        for note in shuffled_notes:
            self.deck.add_note(note)
        
        logging.info(f"Applied chunked shuffling to {len(shuffled_notes)} cards across {len(chunks)} chunks")

    def export_deck(self, output_path: str) -> None:
        """Export deck to .apkg file"""
        # Apply chunked shuffling before export
        self.apply_chunked_shuffling()
        
        logging.info(f"Exporting deck to: {output_path}")
        
        try:
            # With TTS, we don't need to include media files
            genanki.Package(self.deck).write_to_file(output_path)
            
            logging.info(f"Successfully exported {self.cards_created} cards to {output_path}")
            if self.rows_skipped > 0:
                logging.warning(f"Skipped {self.rows_skipped} invalid/malformed rows")
                
        except Exception as e:
            logging.error(f"Error exporting deck: {e}")
            raise
            
    def debug_note_fields(self, note: genanki.Note) -> Dict[str, str]:
        """Debug helper to extract field values from a note"""
        if not note:
            return {"error": "Note is None"}
            
        model_fields = []
        if note.model == self.type1_model:
            model_fields = ['English', 'Hanzi', 'Pinyin', 'POS', 'ExampleHanzi', 'ExampleEnglish', 'ExamplePinyin']
        elif note.model == self.type2_model:
            model_fields = ['ChineseSentence', 'PinyinSentence', 'EnglishTranslation', 
                           'TargetWord', 'TargetPinyin', 'POS', 'Meaning']
        else:
            return {"error": "Unknown model type"}
            
        result = {}
        for i, field_name in enumerate(model_fields):
            if i < len(note.fields):
                result[field_name] = note.fields[i]
            else:
                result[field_name] = "MISSING"
                
        return result
        
    def validate_notes(self) -> List[Dict[str, Any]]:
        """Validate all notes and return any with issues"""
        issues = []
        
        for i, note in enumerate(self.notes):
            # Check for empty required fields
            fields_dict = self.debug_note_fields(note)
            
            if "error" in fields_dict:
                issues.append({
                    "note_index": i,
                    "issue": fields_dict["error"]
                })
                continue
                
            if note.model == self.type1_model:
                # Check Type 1 required fields
                if not fields_dict.get("English") or not fields_dict.get("Hanzi"):
                    issues.append({
                        "note_index": i,
                        "note_type": "Type 1",
                        "issue": "Missing required fields",
                        "fields": fields_dict
                    })
            elif note.model == self.type2_model:
                # Check Type 2 required fields
                if not fields_dict.get("ChineseSentence") or not fields_dict.get("EnglishTranslation"):
                    issues.append({
                        "note_index": i,
                        "note_type": "Type 2",
                        "issue": "Missing required fields",
                        "fields": fields_dict
                    })
                    
        return issues


def main():
    parser = argparse.ArgumentParser(description='Convert CSV to Anki cards with chunked shuffling')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('-o', '--output', default='chinese_cards.apkg', 
                       help='Output .apkg file path (default: chinese_cards.apkg)')
    parser.add_argument('-d', '--deck-name', default='Chinese Learning Deck',
                       help='Anki deck name (default: Chinese Learning Deck)')
    parser.add_argument('-c', '--chunk-size', type=int, default=20,
                       help='Chunk size for shuffling (default: 20)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode with additional validation')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )
    
    try:
        # Create card generator with chunk size
        generator = AnkiCardGenerator(args.deck_name, args.chunk_size)
        
        # Process CSV file
        generator.process_csv(args.csv_file)
        
        # Validate notes if debug mode is enabled
        if args.debug:
            logging.info("Running validation checks on generated cards...")
            issues = generator.validate_notes()
            if issues:
                logging.warning(f"Found {len(issues)} cards with potential issues:")
                for i, issue in enumerate(issues[:5]):  # Show first 5 issues
                    logging.warning(f"Issue {i+1}: {issue['issue']}")
                    if 'fields' in issue:
                        for field, value in issue['fields'].items():
                            if not value or value == "MISSING":
                                logging.warning(f"  - Missing field: {field}")
                if len(issues) > 5:
                    logging.warning(f"  ... and {len(issues) - 5} more issues")
            else:
                logging.info("All cards passed validation checks.")
        
        # Export deck (chunked shuffling applied automatically)
        generator.export_deck(args.output)
        
        print(f"✅ Successfully created {generator.cards_created} cards")
        print(f"🔀 Applied chunked shuffling (chunk size: {args.chunk_size})")
        print(f"🔊 Built-in Anki TTS enabled for Chinese")
        if generator.rows_skipped > 0:
            print(f"⚠️  Skipped {generator.rows_skipped} invalid rows")
        
    except Exception as e:
        logging.error(f"Script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()