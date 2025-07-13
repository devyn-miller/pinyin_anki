#!/usr/bin/env python3
"""
Enhanced Anki Deck Processor - Pinyin & Card Type Categorizer
Processes exported Anki decks to add pinyin and categorize flashcard types
with automatic suggestions and unused field cleanup
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import re
import os
from typing import List, Dict, Optional, Tuple
import jieba
from pypinyin import pinyin, lazy_pinyin, Style
from PIL import Image, ImageTk
import random

class AnkiDeckProcessor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced Anki Deck Processor")
        self.root.geometry("900x700")
        
        # Updated field order based on your actual file format (13 fields)
        self.field_names = [
            'Word', 'Definitions 1', 'Definitions 2', 'Example Sentence',
            'Sentence Translation', 'word_audio', 'sentence_audio', 'image',
            'cloze_sentence', 'prompt', 'scrambled_sentence', 'reconstructed_sentence',
            'tags'
        ]
        
        # We'll add pinyin fields after processing
        self.pinyin_fields = ['Word_Pinyin', 'Example_Sentence_Pinyin', 
                             'Cloze_Sentence_Pinyin', 'Scrambled_Sentence_Pinyin']
        
        # Card type definitions
        self.card_type_definitions = {
            'type1': 'Picture + Audio (Concrete nouns)',
            'type2': 'Cloze Sentence (Particles, function words)',
            'type3': 'Cloze + Prompt (Contextual/conjugated words)',
            'type4': 'Word Placement (Complex word order)',
            'type5': 'Sentence Reconstruction (Full sentence patterns)'
        }
        
        # Common particles and function words
        self.particles = ['的', '了', '着', '过', '么', '呢', '吧', '啊', '吗', '呀', '嘛', '哦', '噢']
        self.function_words = ['和', '或', '但', '因为', '所以', '如果', '虽然', '然而', '而且', '不过', '可是']
        
        self.df = None
        self.current_row = 0
        self.processed_data = []
        self.unused_notes = []  # Track notes with no card types selected
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create scrollable main frame
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main frame
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # File selection
        ttk.Label(main_frame, text="Select Anki Export File (.txt):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_file).grid(row=0, column=2)
        
        # Process button
        ttk.Button(main_frame, text="Process Deck", command=self.process_deck).grid(row=1, column=0, columnspan=3, pady=10)
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready to process...")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=2, column=0, columnspan=3, pady=5)
        
        # Card categorization frame (initially hidden)
        self.card_frame = ttk.LabelFrame(main_frame, text="Card Categorization", padding="10")
        self.card_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        self.card_frame.grid_remove()  # Hide initially
        
        self.setup_card_ui()
        
    def setup_card_ui(self):
        # Current card info
        self.card_info = tk.StringVar()
        ttk.Label(self.card_frame, textvariable=self.card_info, font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=3, pady=5)
        
        # Content display frame
        content_frame = ttk.LabelFrame(self.card_frame, text="Card Content", padding="10")
        content_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Word display
        self.word_display = tk.StringVar()
        ttk.Label(content_frame, text="Word:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(content_frame, textvariable=self.word_display, font=('Arial', 16)).grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Sentence display
        self.sentence_display = tk.StringVar()
        ttk.Label(content_frame, text="Sentence:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W)
        sentence_label = ttk.Label(content_frame, textvariable=self.sentence_display, font=('Arial', 12), wraplength=500)
        sentence_label.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Translation display
        self.translation_display = tk.StringVar()
        ttk.Label(content_frame, text="Translation:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.W)
        translation_label = ttk.Label(content_frame, textvariable=self.translation_display, font=('Arial', 12), 
                                    wraplength=500, foreground='blue')
        translation_label.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # Image display
        self.image_display = tk.StringVar()
        ttk.Label(content_frame, text="Image:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky=tk.W)
        self.image_label = ttk.Label(content_frame, textvariable=self.image_display, font=('Arial', 10))
        self.image_label.grid(row=3, column=1, sticky=tk.W, padx=10)
        
        # Suggestions frame
        suggestions_frame = ttk.LabelFrame(self.card_frame, text="Auto-Suggestions", padding="10")
        suggestions_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.suggestions_text = tk.Text(suggestions_frame, height=3, width=80, font=('Arial', 9))
        self.suggestions_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Decision frame
        decision_frame = ttk.LabelFrame(self.card_frame, text="Select Card Types", padding="10")
        decision_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Checkboxes for card types
        self.card_types = {}
        for i, (key, description) in enumerate(self.card_type_definitions.items()):
            var = tk.BooleanVar()
            self.card_types[key] = var
            cb = ttk.Checkbutton(decision_frame, text=description, variable=var)
            cb.grid(row=i, column=0, sticky=tk.W, pady=3)
        
        # Additional prompts
        ttk.Label(decision_frame, text="Grammar hint/prompt (optional):").grid(row=len(self.card_type_definitions), column=0, sticky=tk.W, pady=5)
        self.prompt_entry = tk.Text(decision_frame, height=2, width=60)
        self.prompt_entry.grid(row=len(self.card_type_definitions)+1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Quick action buttons
        action_frame = ttk.Frame(decision_frame)
        action_frame.grid(row=len(self.card_type_definitions)+2, column=0, pady=10)
        
        ttk.Button(action_frame, text="Accept Suggestions", command=self.accept_suggestions).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Clear All", command=self.clear_all_selections).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Skip Card", command=self.skip_card).pack(side=tk.LEFT, padx=5)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.card_frame)
        nav_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(nav_frame, text="Previous", command=self.previous_card).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Next", command=self.next_card).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Finish Processing", command=self.finish_processing).pack(side=tk.LEFT, padx=5)
        
        # Store current suggestions for quick acceptance
        self.current_suggestions = {}
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Anki Export File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
    
    def process_deck(self):
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select a file first!")
            return
        
        try:
            # Read the file and handle Anki export format
            with open(self.file_path.get(), 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip header lines (lines starting with #)
            data_lines = []
            for line in lines:
                if not line.strip().startswith('#') and line.strip():
                    data_lines.append(line.strip())
            
            if not data_lines:
                messagebox.showerror("Error", "No data found in file!")
                return
            
            # Parse tab-separated data
            data = []
            for line in data_lines:
                fields = line.split('\t')
                # Ensure we have exactly 13 fields
                while len(fields) < 13:
                    fields.append('')
                data.append(fields[:13])  # Take only first 13 fields
            
            # Create DataFrame
            self.df = pd.DataFrame(data, columns=self.field_names)
            
            # Clean up empty rows
            self.df = self.df[self.df['Word'].str.strip() != '']
            
            if self.df.empty:
                messagebox.showerror("Error", "No valid cards found in file!")
                return
            
            # Add pinyin columns
            self.add_pinyin_columns()
            
            # Initialize processed data
            self.processed_data = []
            self.unused_notes = []
            self.current_row = 0
            
            # Show card categorization UI
            self.card_frame.grid()
            self.display_current_card()
            
            self.progress_var.set(f"Processing card 1 of {len(self.df)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file: {str(e)}")
    
    def add_pinyin_columns(self):
        """Add pinyin for Chinese text fields"""
        def clean_chinese_text(text):
            if pd.isna(text) or text == '':
                return ""
            # Remove HTML tags and keep only Chinese characters
            text = re.sub(r'<[^>]+>', '', str(text))
            text = re.sub(r'[^\u4e00-\u9fff]', '', text)
            return text
        
        def get_pinyin(text):
            if not text:
                return ""
            try:
                return ' '.join(lazy_pinyin(text, style=Style.TONE))
            except:
                return ""
        
        # Add pinyin for Word
        self.df['Word_Pinyin'] = self.df['Word'].apply(lambda x: get_pinyin(clean_chinese_text(x)))
        
        # Add pinyin for Example Sentence
        self.df['Example_Sentence_Pinyin'] = self.df['Example Sentence'].apply(lambda x: get_pinyin(clean_chinese_text(x)))
        
        # Initialize empty pinyin columns for fields we'll generate
        self.df['Cloze_Sentence_Pinyin'] = ""
        self.df['Scrambled_Sentence_Pinyin'] = ""
    
    def analyze_word_characteristics(self, word: str, sentence: str) -> Dict[str, bool]:
        """Analyze word characteristics for auto-suggestions"""
        analysis = {
            'is_concrete_noun': False,
            'is_particle': False,
            'is_function_word': False,
            'is_single_char': False,
            'has_complex_context': False,
            'sentence_has_complex_structure': False
        }
        
        if not word or pd.isna(word):
            return analysis
        
        word = str(word).strip()
        
        # Check if single character
        analysis['is_single_char'] = len(word) == 1
        
        # Check for particles
        analysis['is_particle'] = any(particle in word for particle in self.particles)
        
        # Check for function words
        analysis['is_function_word'] = any(func_word in word for func_word in self.function_words)
        
        # Simple heuristic for concrete nouns (single characters that aren't particles)
        if analysis['is_single_char'] and not analysis['is_particle']:
            analysis['is_concrete_noun'] = True
        
        # Check for complex context (word appears multiple times or in different forms)
        if sentence and not pd.isna(sentence):
            sentence = str(sentence)
            word_count = sentence.count(word)
            analysis['has_complex_context'] = word_count > 1
            
            # Check for complex sentence structure
            complex_indicators = ['因为', '所以', '虽然', '但是', '不仅', '而且', '如果', '就']
            analysis['sentence_has_complex_structure'] = any(indicator in sentence for indicator in complex_indicators)
        
        return analysis
    
    def generate_suggestions(self, word: str, sentence: str, translation: str, image_path: str) -> Dict[str, str]:
        """Generate automatic suggestions based on word analysis"""
        analysis = self.analyze_word_characteristics(word, sentence)
        suggestions = {}
        reasons = []
        
        # Type 1: Picture + Audio (Concrete nouns)
        if analysis['is_concrete_noun'] and image_path:
            suggestions['type1'] = True
            reasons.append("✓ Type 1: Single character + has image (likely concrete noun)")
        elif analysis['is_single_char'] and not analysis['is_particle']:
            suggestions['type1'] = True
            reasons.append("✓ Type 1: Single character, non-particle (potential concrete noun)")
        
        # Type 2: Cloze Sentence (Particles, function words)
        if analysis['is_particle']:
            suggestions['type2'] = True
            reasons.append("✓ Type 2: Particle detected (的, 了, 着, etc.)")
        elif analysis['is_function_word']:
            suggestions['type2'] = True
            reasons.append("✓ Type 2: Function word detected")
        
        # Type 3: Cloze + Prompt (Contextual/conjugated)
        if analysis['has_complex_context']:
            suggestions['type3'] = True
            reasons.append("✓ Type 3: Word appears multiple times (contextual usage)")
        elif len(str(word)) > 1 and not analysis['is_function_word']:
            suggestions['type3'] = True
            reasons.append("✓ Type 3: Multi-character word (may need context)")
        
        # Type 4: Word Placement (Complex word order)
        if analysis['sentence_has_complex_structure']:
            suggestions['type4'] = True
            reasons.append("✓ Type 4: Complex sentence structure detected")
        
        # Type 5: Sentence Reconstruction (Full sentence patterns)
        if analysis['sentence_has_complex_structure']:
            suggestions['type5'] = True
            reasons.append("✓ Type 5: Complex sentence - good for pattern practice")
        elif sentence and len(str(sentence)) > 15:
            suggestions['type5'] = True
            reasons.append("✓ Type 5: Long sentence - useful for reconstruction")
        
        # If no suggestions, suggest basic cloze
        if not suggestions:
            suggestions['type2'] = True
            reasons.append("✓ Type 2: Default cloze sentence (no specific patterns detected)")
        
        return suggestions, reasons
    
    def display_current_card(self):
        if self.current_row >= len(self.df):
            self.finish_processing()
            return
            
        row = self.df.iloc[self.current_row]
        
        # Update display
        self.card_info.set(f"Card {self.current_row + 1} of {len(self.df)}")
        
        # Handle empty or NaN values
        word = str(row['Word']) if pd.notna(row['Word']) else ""
        word_pinyin = str(row['Word_Pinyin']) if pd.notna(row['Word_Pinyin']) else ""
        sentence = str(row['Example Sentence']) if pd.notna(row['Example Sentence']) else ""
        translation = str(row['Sentence Translation']) if pd.notna(row['Sentence Translation']) else ""
        image_path = str(row['image']) if pd.notna(row['image']) else ""
        
        # Update displays
        self.word_display.set(f"{word} ({word_pinyin})")
        self.sentence_display.set(sentence)
        self.translation_display.set(translation)
        
        # Handle image display
        if image_path and image_path != "":
            self.image_display.set(f"📷 {os.path.basename(image_path)}")
        else:
            self.image_display.set("No image")
        
        # Clear previous selections
        for var in self.card_types.values():
            var.set(False)
        self.prompt_entry.delete(1.0, tk.END)
        
        # Generate and display suggestions
        suggestions, reasons = self.generate_suggestions(word, sentence, translation, image_path)
        self.current_suggestions = suggestions
        
        # Display suggestions
        self.suggestions_text.delete(1.0, tk.END)
        self.suggestions_text.insert(tk.END, "Auto-suggestions:\n")
        for reason in reasons:
            self.suggestions_text.insert(tk.END, f"{reason}\n")
        
        # Apply suggestions as default
        self.accept_suggestions()
    
    def accept_suggestions(self):
        """Apply current suggestions to checkboxes"""
        for card_type, var in self.card_types.items():
            var.set(self.current_suggestions.get(card_type, False))
    
    def clear_all_selections(self):
        """Clear all card type selections"""
        for var in self.card_types.values():
            var.set(False)
        self.prompt_entry.delete(1.0, tk.END)
    
    def skip_card(self):
        """Skip current card (mark as unused)"""
        self.clear_all_selections()
        self.next_card()
    
    def previous_card(self):
        if self.current_row > 0:
            self.save_current_card()
            self.current_row -= 1
            self.display_current_card()
    
    def next_card(self):
        if self.current_row < len(self.df) - 1:
            self.save_current_card()
            self.current_row += 1
            self.display_current_card()
        else:
            self.finish_processing()
    
    def save_current_card(self):
        """Save current card's categorization and generate fields"""
        row = self.df.iloc[self.current_row].copy()
        
        # Get selected card types
        selected_types = [key for key, var in self.card_types.items() if var.get()]
        
        # Get prompt
        prompt = self.prompt_entry.get(1.0, tk.END).strip()
        
        # If no card types selected, mark as unused
        if not selected_types:
            self.unused_notes.append({
                'row_index': self.current_row,
                'word': row['Word'],
                'sentence': row['Example Sentence']
            })
            # Clear all generated fields
            row['cloze_sentence'] = ""
            row['prompt'] = ""
            row['scrambled_sentence'] = ""
            row['reconstructed_sentence'] = ""
            row['Cloze_Sentence_Pinyin'] = ""
            row['Scrambled_Sentence_Pinyin'] = ""
        else:
            # Generate fields based on selected types
            if 'type2' in selected_types or 'type3' in selected_types:
                # Generate cloze sentence
                cloze_sentence = self.generate_cloze_sentence(row['Example Sentence'], row['Word'])
                row['cloze_sentence'] = cloze_sentence
                row['Cloze_Sentence_Pinyin'] = self.get_pinyin_for_text(cloze_sentence)
            else:
                row['cloze_sentence'] = ""
                row['Cloze_Sentence_Pinyin'] = ""
            
            if 'type3' in selected_types:
                # Add prompt
                row['prompt'] = prompt
            else:
                row['prompt'] = ""
            
            if 'type4' in selected_types:
                # Generate scrambled sentence with blank
                scrambled = self.generate_scrambled_with_blank(row['Example Sentence'], row['Word'])
                row['scrambled_sentence'] = scrambled
                row['Scrambled_Sentence_Pinyin'] = self.get_pinyin_for_text(scrambled)
            elif 'type5' in selected_types:
                # Generate scrambled tokens
                scrambled = self.generate_scrambled_tokens(row['Example Sentence'])
                row['scrambled_sentence'] = scrambled
                row['reconstructed_sentence'] = row['Example Sentence']
                row['Scrambled_Sentence_Pinyin'] = self.get_pinyin_for_text(scrambled)
            else:
                row['scrambled_sentence'] = ""
                row['reconstructed_sentence'] = ""
                row['Scrambled_Sentence_Pinyin'] = ""
        
        # Store processed row
        if len(self.processed_data) <= self.current_row:
            self.processed_data.append(row)
        else:
            self.processed_data[self.current_row] = row
    
    def generate_cloze_sentence(self, sentence: str, word: str) -> str:
        """Replace target word with blank in sentence"""
        if pd.isna(sentence) or pd.isna(word) or sentence == '' or word == '':
            return ""
        return str(sentence).replace(str(word), "___")
    
    def generate_scrambled_with_blank(self, sentence: str, word: str) -> str:
        """Generate sentence with blank where word should go"""
        if pd.isna(sentence) or pd.isna(word) or sentence == '' or word == '':
            return ""
        return f"___ {str(sentence).replace(str(word), '').strip()}"
    
    def generate_scrambled_tokens(self, sentence: str) -> str:
        """Generate scrambled tokens separated by /"""
        if pd.isna(sentence) or sentence == '':
            return ""
        
        try:
            # Simple tokenization - using jieba for Chinese
            tokens = list(jieba.cut(str(sentence)))
            # Remove empty tokens
            tokens = [t for t in tokens if t.strip()]
            
            if not tokens:
                return ""
            
            # Scramble (simple reverse for now - you could randomize)
            tokens.reverse()
            
            return " / ".join(tokens)
        except:
            return ""
    
    def get_pinyin_for_text(self, text: str) -> str:
        """Get pinyin for any Chinese text"""
        if not text or pd.isna(text):
            return ""
        
        try:
            # Remove HTML and non-Chinese characters for pinyin
            clean_text = re.sub(r'<[^>]+>', '', str(text))
            clean_text = re.sub(r'[^\u4e00-\u9fff]', '', clean_text)
            
            if not clean_text:
                return ""
            
            return ' '.join(lazy_pinyin(clean_text, style=Style.TONE))
        except:
            return ""
    
    def finish_processing(self):
        """Save the final processed deck"""
        if not self.processed_data:
            messagebox.showwarning("Warning", "No cards processed!")
            return
        
        # Save current card if we're not at the end
        if self.current_row < len(self.df):
            self.save_current_card()
        
        try:
            # Create output DataFrame
            output_df = pd.DataFrame(self.processed_data)
            
            # Reorder columns to match Anki import format
            output_columns = self.field_names + self.pinyin_fields
            output_df = output_df[output_columns]
            
            # Save to file
            input_path = self.file_path.get()
            output_path = input_path.replace('.txt', '_processed.txt')
            
            # Write with proper Anki format
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write header lines
                f.write("#separator:tab\n")
                f.write("#html:true\n")
                f.write(f"#tags column:{len(output_columns)}\n")
                
                # Write data
                for _, row in output_df.iterrows():
                    line = '\t'.join(str(val) if pd.notna(val) else '' for val in row)
                    f.write(line + '\n')
            
            # Generate unused notes report
            if self.unused_notes:
                unused_report_path = input_path.replace('.txt', '_unused_notes.txt')
                with open(unused_report_path, 'w', encoding='utf-8') as f:
                    f.write("UNUSED NOTES REPORT\n")
                    f.write("===================\n\n")
                    f.write(f"Total unused notes: {len(self.unused_notes)}\n\n")
                    
                    for note in self.unused_notes:
                        f.write(f"Row {note['row_index'] + 1}:\n")
                        f.write(f"  Word: {note['word']}\n")
                        f.write(f"  Sentence: {note['sentence']}\n")
                        f.write("-" * 40 + "\n")
                
                message = f"Processing complete!\n\nProcessed deck saved to:\n{output_path}\n\nUnused notes report saved to:\n{unused_report_path}\n\nTotal cards: {len(self.processed_data)}\nUnused notes: {len(self.unused_notes)}"
            else:
                message = f"Processing complete!\n\nProcessed deck saved to:\n{output_path}\n\nTotal cards processed: {len(self.processed_data)}"
            
            messagebox.showinfo("Success", message)
            
            # Hide card frame
            self.card_frame.grid_remove()
            self.progress_var.set(f"Processing complete! {len(self.processed_data)} cards processed, {len(self.unused_notes)} unused notes.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save processed deck: {str(e)}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # Check for required dependencies
    try:
        import jieba
        import pypinyin
        import pandas as pd
        from PIL import Image, ImageTk
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install jieba pypinyin pandas pillow")
        exit(1)
    
    app = AnkiDeckProcessor()
    app.run()