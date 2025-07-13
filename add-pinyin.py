#!/usr/bin/env python3
"""
Anki Deck Processor - Convert 8-field Yomitan/ASB Player decks to 17-field format
with Tkinter GUI for preview and editing.

Dependencies:
    pip install pypinyin pillow

Author: Assistant
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from PIL import Image, ImageTk
import pypinyin

@dataclass
class CardData:
    """Data class for storing card information"""
    word: str = ""
    definitions1: str = ""
    definitions2: str = ""
    example_sentence: str = ""
    sentence_translation: str = ""
    word_audio: str = ""
    sentence_audio: str = ""
    image: str = ""
    
    # Generated fields
    cloze_sentence: str = ""
    cloze_sentence_pinyin: str = ""
    scrambled_sentence: str = ""
    scrambled_sentence_pinyin: str = ""
    reconstructed_sentence: str = ""
    reconstructed_sentence_pinyin: str = ""
    prompt: str = ""
    word_pinyin: str = ""
    example_sentence_pinyin: str = ""
    
    # Card type selections
    selected_types: List[bool] = field(default_factory=lambda: [False] * 5)

class CardTypeProcessor:
    """Handles card type logic and auto-generation"""
    
    CARD_TYPES = {
        1: "Image + Audio (Concrete nouns)",
        2: "Cloze (Grammar/particles)", 
        3: "Prompt + Cloze (Complex grammar)",
        4: "Scrambled (Word order/particles)",
        5: "Reconstruction (Memorable sentences)"
    }
    
    # Common Chinese particles and grammar words
    PARTICLES = {'的', '了', '着', '过', '在', '是', '有', '会', '能', '可以', '应该', '要', '想', '觉得', '认为'}
    GRAMMAR_WORDS = {'如果', '要是', '虽然', '但是', '不过', '因为', '所以', '为了', '除了', '关于', '对于', '通过', '根据'}
    
    @classmethod
    def get_pinyin(cls, text: str) -> str:
        """Convert Chinese text to pinyin"""
        # Remove HTML tags and extra whitespace
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        if not clean_text:
            return ""
        
        # Generate pinyin with tone marks
        pinyin_list = pypinyin.pinyin(clean_text, style=pypinyin.TONE, heteronym=False)
        return ' '.join([item[0] for item in pinyin_list])
    
    @classmethod
    def suggest_card_types(cls, card: CardData) -> List[bool]:
        """Auto-suggest card types based on heuristics"""
        suggestions = [False] * 5
        
        word = card.word.strip()
        sentence = card.example_sentence.strip()
        has_image = bool(card.image.strip())
        has_audio = bool(card.word_audio.strip())
        
        # Type 1: Image + Audio (concrete nouns)
        if has_image and has_audio and len(word) <= 3:
            suggestions[0] = True
        
        # Type 2: Cloze (grammar/particles)
        if word in cls.PARTICLES or word in cls.GRAMMAR_WORDS:
            suggestions[1] = True
        
        # Type 3: Prompt + Cloze (complex grammar)
        if any(gram in sentence for gram in cls.GRAMMAR_WORDS) or '…' in sentence:
            suggestions[2] = True
        
        # Type 4: Scrambled (word order confusion)
        if len(sentence) > 5 and any(p in sentence for p in cls.PARTICLES):
            suggestions[3] = True
        
        # Type 5: Reconstruction (memorable sentences)
        if len(sentence) > 8 and ('!' in sentence or '?' in sentence or '…' in sentence):
            suggestions[4] = True
        
        return suggestions
    
    @classmethod
    def generate_cloze_sentence(cls, card: CardData) -> str:
        """Generate cloze sentence by replacing word with blanks"""
        sentence = card.example_sentence.strip()
        word = card.word.strip()
        
        if not sentence or not word:
            return sentence
        
        # Replace word with appropriate number of underscores
        blank = "_" * max(2, len(word))
        return sentence.replace(word, blank)
    
    @classmethod
    def generate_scrambled_sentence(cls, card: CardData) -> str:
        """Generate scrambled sentence by reordering words"""
        sentence = card.example_sentence.strip()
        if not sentence or len(sentence) < 3:
            return sentence
        
        # Simple character-level scrambling for Chinese
        chars = list(sentence)
        # Keep punctuation in place
        punct_positions = [(i, char) for i, char in enumerate(chars) if not char.isalnum()]
        
        # Scramble non-punctuation characters
        non_punct = [char for char in chars if char.isalnum()]
        if len(non_punct) > 2:
            random.shuffle(non_punct)
        
        # Reconstruct with punctuation
        result = non_punct.copy()
        for pos, punct in punct_positions:
            if pos < len(result):
                result.insert(pos, punct)
        
        return ''.join(result)
    
    @classmethod
    def generate_prompt(cls, card: CardData) -> str:
        """Generate usage hint/grammar note"""
        word = card.word.strip()
        
        if word in cls.PARTICLES:
            return f"Grammar particle: {word}"
        elif word in cls.GRAMMAR_WORDS:
            return f"Grammar pattern with: {word}"
        elif len(word) == 1:
            return f"Single character: {word}"
        else:
            return f"Usage: {word}"

class AnkiDeckProcessor:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Anki Deck Processor")
        self.root.geometry("1000x700")
        
        self.cards: List[CardData] = []
        self.current_card_index = 0
        self.input_file = ""
        self.output_file = ""
        
        self.setup_ui()
        self.processor = CardTypeProcessor()
    
    def setup_ui(self):
        """Setup the main UI"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Button(file_frame, text="Select Input File", command=self.select_input_file).grid(row=0, column=0, padx=(0, 5))
        self.input_label = ttk.Label(file_frame, text="No file selected")
        self.input_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Button(file_frame, text="Select Output File", command=self.select_output_file).grid(row=1, column=0, padx=(0, 5))
        self.output_label = ttk.Label(file_frame, text="No file selected")
        self.output_label.grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        ttk.Button(file_frame, text="Load Cards", command=self.load_cards).grid(row=2, column=0, pady=(5, 0))
        
        # Navigation frame
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        nav_frame.columnconfigure(1, weight=1)
        
        ttk.Button(nav_frame, text="Previous", command=self.prev_card).grid(row=0, column=0, padx=(0, 5))
        self.progress_label = ttk.Label(nav_frame, text="No cards loaded")
        self.progress_label.grid(row=0, column=1)
        ttk.Button(nav_frame, text="Next", command=self.next_card).grid(row=0, column=2, padx=(5, 0))
        
        # Main content frame
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Left panel - Card preview
        self.setup_preview_panel(content_frame)
        
        # Right panel - Card types and editing
        self.setup_editing_panel(content_frame)
        
        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Generate All", command=self.generate_all).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Save Current", command=self.save_current).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Export All", command=self.export_all).grid(row=0, column=2)
    
    def setup_preview_panel(self, parent):
        """Setup the left preview panel"""
        preview_frame = ttk.LabelFrame(parent, text="Card Preview", padding="5")
        preview_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(5, weight=1)
        
        # Word
        ttk.Label(preview_frame, text="Word:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        self.word_label = ttk.Label(preview_frame, text="", font=("Arial", 14))
        self.word_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Example sentence
        ttk.Label(preview_frame, text="Example Sentence:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W)
        self.sentence_label = ttk.Label(preview_frame, text="", wraplength=400)
        self.sentence_label.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Translation
        ttk.Label(preview_frame, text="Translation:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W)
        self.translation_label = ttk.Label(preview_frame, text="", wraplength=400)
        self.translation_label.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Media info
        media_frame = ttk.Frame(preview_frame)
        media_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        media_frame.columnconfigure(0, weight=1)
        
        self.audio_label = ttk.Label(media_frame, text="Audio: None")
        self.audio_label.grid(row=0, column=0, sticky=tk.W)
        
        self.image_label = ttk.Label(media_frame, text="Image: None")
        self.image_label.grid(row=1, column=0, sticky=tk.W)
        
        # Image preview
        self.image_preview = ttk.Label(media_frame, text="No image")
        self.image_preview.grid(row=2, column=0, pady=(5, 0))
    
    def setup_editing_panel(self, parent):
        """Setup the right editing panel"""
        edit_frame = ttk.LabelFrame(parent, text="Card Generation & Editing", padding="5")
        edit_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        edit_frame.columnconfigure(0, weight=1)
        edit_frame.rowconfigure(1, weight=1)
        
        # Card type selection
        type_frame = ttk.LabelFrame(edit_frame, text="Card Types", padding="5")
        type_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.type_vars = []
        for i, (num, desc) in enumerate(self.processor.CARD_TYPES.items()):
            var = tk.BooleanVar()
            self.type_vars.append(var)
            ttk.Checkbutton(type_frame, text=f"Type {num}: {desc}", variable=var, 
                           command=self.on_type_selection_change).grid(row=i, column=0, sticky=tk.W)
        
        # Auto-suggest button
        ttk.Button(type_frame, text="Auto-Suggest", command=self.auto_suggest_types).grid(row=len(self.processor.CARD_TYPES), column=0, pady=(5, 0))
        
        # Editable fields
        fields_frame = ttk.LabelFrame(edit_frame, text="Generated Fields", padding="5")
        fields_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        fields_frame.columnconfigure(0, weight=1)
        fields_frame.rowconfigure(0, weight=1)
        
        # Scrollable text area
        self.fields_text = scrolledtext.ScrolledText(fields_frame, height=20, width=50)
        self.fields_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def select_input_file(self):
        """Select input file"""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.input_file = filename
            self.input_label.config(text=os.path.basename(filename))
    
    def select_output_file(self):
        """Select output file"""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.output_file = filename
            self.output_label.config(text=os.path.basename(filename))
    
    def load_cards(self):
        """Load cards from input file"""
        if not self.input_file:
            messagebox.showerror("Error", "Please select an input file first")
            return
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.cards = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                fields = line.split('\t')
                if len(fields) < 8:
                    # Pad with empty strings if needed
                    fields.extend([''] * (8 - len(fields)))
                
                card = CardData(
                    word=fields[0],
                    definitions1=fields[1],
                    definitions2=fields[2],
                    example_sentence=fields[3],
                    sentence_translation=fields[4],
                    word_audio=fields[5],
                    sentence_audio=fields[6],
                    image=fields[7]
                )
                self.cards.append(card)
            
            self.current_card_index = 0
            self.update_display()
            messagebox.showinfo("Success", f"Loaded {len(self.cards)} cards")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def update_display(self):
        """Update the display with current card"""
        if not self.cards:
            return
        
        card = self.cards[self.current_card_index]
        
        # Update preview
        self.word_label.config(text=card.word)
        self.sentence_label.config(text=card.example_sentence)
        self.translation_label.config(text=card.sentence_translation)
        
        # Update media info
        audio_info = f"Word: {card.word_audio}" if card.word_audio else "Word: None"
        if card.sentence_audio:
            audio_info += f", Sentence: {card.sentence_audio}"
        self.audio_label.config(text=audio_info)
        
        image_info = f"Image: {card.image}" if card.image else "Image: None"
        self.image_label.config(text=image_info)
        
        # Update progress
        self.progress_label.config(text=f"Card {self.current_card_index + 1} of {len(self.cards)}")
        
        # Update card type selections
        for i, var in enumerate(self.type_vars):
            var.set(card.selected_types[i])
        
        # Update generated fields
        self.update_fields_display()
        
        # Try to load image preview
        self.load_image_preview(card.image)
    
    def load_image_preview(self, image_path: str):
        """Load and display image preview"""
        try:
            if image_path and os.path.exists(image_path):
                image = Image.open(image_path)
                # Resize to fit preview
                image.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(image)
                self.image_preview.config(image=photo, text="")
                self.image_preview.image = photo  # Keep a reference
            else:
                self.image_preview.config(image="", text="No image")
                self.image_preview.image = None
        except Exception:
            self.image_preview.config(image="", text="Image error")
            self.image_preview.image = None
    
    def update_fields_display(self):
        """Update the fields text display"""
        if not self.cards:
            return
        
        card = self.cards[self.current_card_index]
        
        fields_text = f"""Cloze Sentence:
{card.cloze_sentence}

Cloze Sentence Pinyin:
{card.cloze_sentence_pinyin}

Scrambled Sentence:
{card.scrambled_sentence}

Scrambled Sentence Pinyin:
{card.scrambled_sentence_pinyin}

Reconstructed Sentence:
{card.reconstructed_sentence}

Reconstructed Sentence Pinyin:
{card.reconstructed_sentence_pinyin}

Prompt:
{card.prompt}

Word Pinyin:
{card.word_pinyin}

Example Sentence Pinyin:
{card.example_sentence_pinyin}"""
        
        self.fields_text.delete(1.0, tk.END)
        self.fields_text.insert(1.0, fields_text)
    
    def prev_card(self):
        """Go to previous card"""
        if self.cards and self.current_card_index > 0:
            self.save_current_fields()
            self.current_card_index -= 1
            self.update_display()
    
    def next_card(self):
        """Go to next card"""
        if self.cards and self.current_card_index < len(self.cards) - 1:
            self.save_current_fields()
            self.current_card_index += 1
            self.update_display()
    
    def save_current_fields(self):
        """Save current field edits"""
        if not self.cards:
            return
        
        card = self.cards[self.current_card_index]
        
        # Save type selections
        for i, var in enumerate(self.type_vars):
            card.selected_types[i] = var.get()
        
        # Parse and save field edits
        content = self.fields_text.get(1.0, tk.END)
        self.parse_fields_content(card, content)
    
    def parse_fields_content(self, card: CardData, content: str):
        """Parse the fields content and update card"""
        sections = content.split('\n\n')
        
        field_map = {
            'Cloze Sentence:': 'cloze_sentence',
            'Cloze Sentence Pinyin:': 'cloze_sentence_pinyin',
            'Scrambled Sentence:': 'scrambled_sentence',
            'Scrambled Sentence Pinyin:': 'scrambled_sentence_pinyin',
            'Reconstructed Sentence:': 'reconstructed_sentence',
            'Reconstructed Sentence Pinyin:': 'reconstructed_sentence_pinyin',
            'Prompt:': 'prompt',
            'Word Pinyin:': 'word_pinyin',
            'Example Sentence Pinyin:': 'example_sentence_pinyin'
        }
        
        for section in sections:
            lines = section.strip().split('\n')
            if len(lines) >= 2:
                header = lines[0].strip()
                value = '\n'.join(lines[1:]).strip()
                
                if header in field_map:
                    setattr(card, field_map[header], value)
    
    def on_type_selection_change(self):
        """Handle card type selection change"""
        if self.cards:
            self.save_current_fields()
            self.generate_current()
    
    def auto_suggest_types(self):
        """Auto-suggest card types for current card"""
        if not self.cards:
            return
        
        card = self.cards[self.current_card_index]
        suggestions = self.processor.suggest_card_types(card)
        
        for i, suggestion in enumerate(suggestions):
            self.type_vars[i].set(suggestion)
            card.selected_types[i] = suggestion
        
        self.generate_current()
    
    def generate_current(self):
        """Generate fields for current card"""
        if not self.cards:
            return
        
        card = self.cards[self.current_card_index]
        
        # Generate pinyin fields
        card.word_pinyin = self.processor.get_pinyin(card.word)
        card.example_sentence_pinyin = self.processor.get_pinyin(card.example_sentence)
        
        # Generate based on selected types
        if card.selected_types[1] or card.selected_types[2]:  # Cloze types
            card.cloze_sentence = self.processor.generate_cloze_sentence(card)
            card.cloze_sentence_pinyin = self.processor.get_pinyin(card.cloze_sentence)
        
        if card.selected_types[3]:  # Scrambled
            card.scrambled_sentence = self.processor.generate_scrambled_sentence(card)
            card.scrambled_sentence_pinyin = self.processor.get_pinyin(card.scrambled_sentence)
        
        if card.selected_types[4]:  # Reconstruction
            card.reconstructed_sentence = card.example_sentence
            card.reconstructed_sentence_pinyin = card.example_sentence_pinyin
        
        if any(card.selected_types[1:4]):  # Any type that uses prompts
            card.prompt = self.processor.generate_prompt(card)
        
        self.update_fields_display()
    
    def generate_all(self):
        """Generate fields for all cards"""
        if not self.cards:
            messagebox.showwarning("Warning", "No cards loaded")
            return
        
        self.save_current_fields()
        
        for card in self.cards:
            # Auto-suggest types if none selected
            if not any(card.selected_types):
                card.selected_types = self.processor.suggest_card_types(card)
            
            # Generate fields
            card.word_pinyin = self.processor.get_pinyin(card.word)
            card.example_sentence_pinyin = self.processor.get_pinyin(card.example_sentence)
            
            if card.selected_types[1] or card.selected_types[2]:
                card.cloze_sentence = self.processor.generate_cloze_sentence(card)
                card.cloze_sentence_pinyin = self.processor.get_pinyin(card.cloze_sentence)
            
            if card.selected_types[3]:
                card.scrambled_sentence = self.processor.generate_scrambled_sentence(card)
                card.scrambled_sentence_pinyin = self.processor.get_pinyin(card.scrambled_sentence)
            
            if card.selected_types[4]:
                card.reconstructed_sentence = card.example_sentence
                card.reconstructed_sentence_pinyin = card.example_sentence_pinyin
            
            if any(card.selected_types[1:4]):
                card.prompt = self.processor.generate_prompt(card)
        
        self.update_display()
        messagebox.showinfo("Success", "Generated fields for all cards")
    
    def save_current(self):
        """Save current card edits"""
        if self.cards:
            self.save_current_fields()
            messagebox.showinfo("Success", "Current card saved")
    
    def export_all(self):
        """Export all cards to output file"""
        if not self.cards:
            messagebox.showwarning("Warning", "No cards to export")
            return
        
        if not self.output_file:
            messagebox.showerror("Error", "Please select an output file first")
            return
        
        self.save_current_fields()
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                for card in self.cards:
                    fields = [
                        card.word,
                        card.definitions1,
                        card.definitions2,
                        card.example_sentence,
                        card.sentence_translation,
                        card.word_audio,
                        card.sentence_audio,
                        card.image,
                        card.cloze_sentence,
                        card.cloze_sentence_pinyin,
                        card.scrambled_sentence,
                        card.scrambled_sentence_pinyin,
                        card.reconstructed_sentence,
                        card.reconstructed_sentence_pinyin,
                        card.prompt,
                        card.word_pinyin,
                        card.example_sentence_pinyin
                    ]
                    f.write('\t'.join(fields) + '\n')
            
            messagebox.showinfo("Success", f"Exported {len(self.cards)} cards to {self.output_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

def main():
    """Main function"""
    root = tk.Tk()
    app = AnkiDeckProcessor(root)
    root.mainloop()

if __name__ == "__main__":
    main()