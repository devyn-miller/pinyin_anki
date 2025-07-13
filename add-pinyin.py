#!/usr/bin/env python3
"""
Anki Deck Processor - Pinyin & Card Type Categorizer
Processes exported Anki decks to add pinyin and categorize flashcard types
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import re
import os
from typing import List, Dict, Optional, Tuple
import jieba
from pypinyin import pinyin, lazy_pinyin, Style

class AnkiDeckProcessor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Anki Deck Processor")
        self.root.geometry("800x600")
        
        # Updated field order based on your actual file format (13 fields)
        self.field_names = [
            'Word', 'Definitions 1', 'Definitions 2', 'Example Sentence',
            'Sentence Translation', 'word_audio', 'sentence_audio', 'image',
            'cloze_sentence', 'prompt', 'scrambled_sentence', 'reconstructed_sentence',
            'tags'  # Added tags column
        ]
        
        # We'll add pinyin fields after processing
        self.pinyin_fields = ['Word_Pinyin', 'Example_Sentence_Pinyin', 
                             'Cloze_Sentence_Pinyin', 'Scrambled_Sentence_Pinyin']
        
        self.df = None
        self.current_row = 0
        self.processed_data = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
        
        # Word and sentence display
        self.word_display = tk.StringVar()
        self.sentence_display = tk.StringVar()
        
        ttk.Label(self.card_frame, text="Word:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(self.card_frame, textvariable=self.word_display, font=('Arial', 14)).grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(self.card_frame, text="Sentence:").grid(row=2, column=0, sticky=tk.W)
        sentence_label = ttk.Label(self.card_frame, textvariable=self.sentence_display, font=('Arial', 12), wraplength=400)
        sentence_label.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # Decision questions
        ttk.Label(self.card_frame, text="Select card types for this word:", font=('Arial', 11, 'bold')).grid(row=3, column=0, columnspan=3, pady=10)
        
        # Checkboxes for card types
        self.card_types = {}
        questions = [
            ("type1", "Picture + Audio (Is this a concrete noun?)"),
            ("type2", "Cloze Sentence (Is this a structure or particle?)"),
            ("type3", "Cloze + Prompt (Is the word conjugated or contextual?)"),
            ("type4", "Word Placement (Is word order confusing?)"),
            ("type5", "Sentence Reconstruction (Do I want to mimic this whole sentence?)")
        ]
        
        for i, (key, question) in enumerate(questions):
            var = tk.BooleanVar()
            self.card_types[key] = var
            ttk.Checkbutton(self.card_frame, text=question, variable=var).grid(row=4+i, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        # Additional prompts
        ttk.Label(self.card_frame, text="Grammar hint/prompt (optional):").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.prompt_entry = tk.Text(self.card_frame, height=2, width=50)
        self.prompt_entry.grid(row=9, column=1, padx=10)
        
        # Navigation buttons
        button_frame = ttk.Frame(self.card_frame)
        button_frame.grid(row=10, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Previous", command=self.previous_card).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Next", command=self.next_card).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Finish Processing", command=self.finish_processing).pack(side=tk.LEFT, padx=5)
        
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
        
        self.word_display.set(f"{word} ({word_pinyin})")
        self.sentence_display.set(sentence)
        
        # Clear previous selections
        for var in self.card_types.values():
            var.set(False)
        self.prompt_entry.delete(1.0, tk.END)
        
        # Auto-suggest based on simple heuristics
        if word:
            # Simple auto-suggestions
            if any(char in word for char in ['的', '了', '着', '过', '么', '呢', '吧', '啊']):
                self.card_types['type2'].set(True)  # Particles
            
            if len(word) == 1 and not any(char in word for char in ['的', '了', '着', '过']):
                self.card_types['type1'].set(True)  # Single character nouns
    
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
        
        # Generate fields based on selected types
        if 'type2' in selected_types or 'type3' in selected_types:
            # Generate cloze sentence
            cloze_sentence = self.generate_cloze_sentence(row['Example Sentence'], row['Word'])
            row['cloze_sentence'] = cloze_sentence
            row['Cloze_Sentence_Pinyin'] = self.get_pinyin_for_text(cloze_sentence)
        
        if 'type3' in selected_types:
            # Add prompt
            row['prompt'] = prompt
        
        if 'type4' in selected_types:
            # Generate scrambled sentence with blank
            scrambled = self.generate_scrambled_with_blank(row['Example Sentence'], row['Word'])
            row['scrambled_sentence'] = scrambled
            row['Scrambled_Sentence_Pinyin'] = self.get_pinyin_for_text(scrambled)
        
        if 'type5' in selected_types:
            # Generate scrambled tokens
            scrambled = self.generate_scrambled_tokens(row['Example Sentence'])
            row['scrambled_sentence'] = scrambled
            row['reconstructed_sentence'] = row['Example Sentence']
            row['Scrambled_Sentence_Pinyin'] = self.get_pinyin_for_text(scrambled)
        
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
            
            messagebox.showinfo("Success", f"Processed deck saved to:\n{output_path}")
            
            # Hide card frame
            self.card_frame.grid_remove()
            self.progress_var.set(f"Processing complete! {len(self.processed_data)} cards processed.")
            
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
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install jieba pypinyin pandas")
        exit(1)
    
    app = AnkiDeckProcessor()
    app.run()