#!/usr/bin/env python3
"""
Anki Deck Processor - Transform 8-field Yomitan exports to 17-field custom note type

This script processes .txt files exported from Yomitan + ASB Player with 8 fields
and expands them to 17 fields for use with a custom Anki note type that generates
5 different card types.

Requirements:
    pip install pypinyin pillow

Usage:
    python anki_processor.py input.txt output.txt

Author: Generated for Anki deck processing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import random
from PIL import Image, ImageTk
from pypinyin import pinyin, Style
import sys
from typing import List, Dict, Optional, Tuple


class AnkiNote:
    """Represents a single Anki note with 8 input fields and 17 output fields"""
    
    def __init__(self, input_fields: List[str]):
        """Initialize with 8 input fields from tab-separated line"""
        if len(input_fields) < 8:
            # Pad with empty strings if insufficient fields
            input_fields.extend([''] * (8 - len(input_fields)))
        
        # Input fields (8 total)
        self.word = input_fields[0].strip()
        self.definitions_1 = input_fields[1].strip()
        self.definitions_2 = input_fields[2].strip()
        self.example_sentence = input_fields[3].strip()
        self.sentence_translation = input_fields[4].strip()
        self.word_audio = input_fields[5].strip()
        self.sentence_audio = input_fields[6].strip()
        self.image = input_fields[7].strip()
        
        # Generated fields (will be populated based on card type selection)
        self.cloze_sentence = ""
        self.cloze_sentence_pinyin = ""
        self.scrambled_sentence = ""
        self.scrambled_sentence_pinyin = ""
        self.reconstructed_sentence = ""
        self.reconstructed_sentence_pinyin = ""
        self.prompt = ""
        self.word_pinyin = ""
        self.example_sentence_pinyin = ""
        
        # Clean HTML from definitions for display
        self.clean_definitions_1 = self._clean_html(self.definitions_1)
        self.clean_definitions_2 = self._clean_html(self.definitions_2)
        self.clean_sentence = self._clean_html(self.example_sentence)
        
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean up text for display"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Convert HTML entities
        text = text.replace('&quot;', '"').replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        return text
    
    def get_pinyin(self, chinese_text: str) -> str:
        """Convert Chinese text to pinyin"""
        if not chinese_text:
            return ""
        
        # Clean the text first
        clean_text = self._clean_html(chinese_text)
        
        try:
            # Generate pinyin with tone marks
            pinyin_result = pinyin(clean_text, style=Style.TONE, heteronym=False)
            return ' '.join([item[0] for item in pinyin_result])
        except Exception as e:
            print(f"Error generating pinyin for '{clean_text}': {e}")
            return ""
    
    def suggest_card_types(self) -> List[int]:
        """Suggest appropriate card types based on heuristics"""
        suggestions = []
        
        # Type 1: Image + Audio (concrete nouns, visual content)
        if (self.image and 
            any(keyword in self.clean_definitions_1.lower() for keyword in 
                ['noun', 'object', 'thing', 'person', 'place', 'animal', 'food'])):
            suggestions.append(1)
        
        # Type 2: Cloze (function words, particles, grammar)
        if (len(self.word) <= 2 and 
            any(keyword in self.clean_definitions_1.lower() for keyword in 
                ['particle', 'marker', 'auxiliary', 'conjunction', 'preposition'])):
            suggestions.append(2)
        
        # Type 3: Prompt + Cloze (grammar patterns, complex usage)
        if (any(keyword in self.clean_definitions_1.lower() for keyword in 
                ['grammar', 'pattern', 'structure', 'usage', 'expression']) or
            '得' in self.clean_sentence or '不' in self.clean_sentence):
            suggestions.append(3)
        
        # Type 4: Scrambled (word order, sentence structure)
        if (len(self.clean_sentence.split()) > 4 and
            any(keyword in self.clean_definitions_1.lower() for keyword in 
                ['order', 'structure', 'arrangement', 'particle'])):
            suggestions.append(4)
        
        # Type 5: Reconstruction (memorable sentences, complete thoughts)
        if (len(self.clean_sentence.split()) > 3 and
            any(keyword in self.sentence_translation.lower() for keyword in 
                ['should', 'would', 'could', 'if', 'when', 'because'])):
            suggestions.append(5)
        
        # Default suggestions if no specific heuristics match
        if not suggestions:
            if self.image:
                suggestions.append(1)
            if len(self.word) <= 2:
                suggestions.append(2)
            else:
                suggestions.append(5)
        
        return suggestions
    
    def generate_content(self, selected_card_types: List[int]) -> None:
        """Generate content for selected card types"""
        # Always generate basic pinyin
        self.word_pinyin = self.get_pinyin(self.word)
        self.example_sentence_pinyin = self.get_pinyin(self.clean_sentence)
        
        # Generate content based on selected card types
        if 2 in selected_card_types or 3 in selected_card_types:
            self._generate_cloze_content()
        
        if 4 in selected_card_types:
            self._generate_scrambled_content()
        
        if 5 in selected_card_types:
            self._generate_reconstruction_content()
        
        # Generate prompt for any card type that needs it
        if any(ct in selected_card_types for ct in [1, 2, 3, 4, 5]):
            self._generate_prompt()
    
    def _generate_cloze_content(self) -> None:
        """Generate cloze deletion content"""
        if self.word in self.clean_sentence:
            self.cloze_sentence = self.clean_sentence.replace(self.word, "___", 1)
            # Generate pinyin version
            pinyin_sentence = self.get_pinyin(self.clean_sentence)
            word_pinyin = self.get_pinyin(self.word)
            if word_pinyin and word_pinyin in pinyin_sentence:
                self.cloze_sentence_pinyin = pinyin_sentence.replace(word_pinyin, "___", 1)
        else:
            # If word not found directly, create cloze at the end
            self.cloze_sentence = self.clean_sentence + " ___"
            self.cloze_sentence_pinyin = self.example_sentence_pinyin + " ___"
    
    def _generate_scrambled_content(self) -> None:
        """Generate scrambled sentence content"""
        # Split sentence into words/characters
        words = self.clean_sentence.split()
        if len(words) > 1:
            # Scramble word order
            scrambled_words = words.copy()
            random.shuffle(scrambled_words)
            self.scrambled_sentence = " / ".join(scrambled_words)
            
            # Generate pinyin version
            pinyin_words = []
            for word in scrambled_words:
                pinyin_words.append(self.get_pinyin(word))
            self.scrambled_sentence_pinyin = " / ".join(pinyin_words)
        else:
            # For single words or short phrases, scramble characters
            chars = list(self.clean_sentence)
            random.shuffle(chars)
            self.scrambled_sentence = " / ".join(chars)
            self.scrambled_sentence_pinyin = self.get_pinyin(self.scrambled_sentence)
    
    def _generate_reconstruction_content(self) -> None:
        """Generate reconstruction content"""
        self.reconstructed_sentence = self.clean_sentence
        self.reconstructed_sentence_pinyin = self.example_sentence_pinyin
    
    def _generate_prompt(self) -> None:
        """Generate helpful prompt based on definitions and context"""
        prompts = []
        
        # Add definition-based prompt
        if self.clean_definitions_1:
            prompts.append(f"Meaning: {self.clean_definitions_1[:50]}...")
        
        # Add usage context
        if "student" in self.clean_definitions_1.lower():
            prompts.append("Used in educational contexts")
        elif "time" in self.clean_definitions_1.lower():
            prompts.append("Related to time or timing")
        elif "food" in self.clean_definitions_1.lower():
            prompts.append("Food-related vocabulary")
        elif "particle" in self.clean_definitions_1.lower():
            prompts.append("Grammar particle")
        
        self.prompt = " | ".join(prompts)
    
    def to_output_fields(self) -> List[str]:
        """Convert to 17-field output format"""
        return [
            self.word,
            self.definitions_1,
            self.definitions_2,
            self.example_sentence,
            self.sentence_translation,
            self.word_audio,
            self.sentence_audio,
            self.image,
            self.cloze_sentence,
            self.cloze_sentence_pinyin,
            self.scrambled_sentence,
            self.scrambled_sentence_pinyin,
            self.reconstructed_sentence,
            self.reconstructed_sentence_pinyin,
            self.prompt,
            self.word_pinyin,
            self.example_sentence_pinyin
        ]


class AnkiProcessorGUI:
    """GUI interface for processing Anki notes"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Anki Deck Processor")
        self.root.geometry("1000x800")
        
        # Data storage
        self.notes: List[AnkiNote] = []
        self.current_note_index = 0
        self.processed_notes: List[AnkiNote] = []
        
        # Card type descriptions
        self.card_types = {
            1: "Image + Audio (Visual recognition)",
            2: "Cloze Deletion (Fill in the blank)",
            3: "Prompt + Cloze (Grammar context)",
            4: "Scrambled Sentence (Word order)",
            5: "Reconstruction (Complete sentence)"
        }
        
        self.setup_gui()
        
    def setup_gui(self):
        """Initialize the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.input_file_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        
        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.input_file_var, width=50).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=self.browse_input_file).grid(row=0, column=2, pady=2)
        
        ttk.Label(file_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(file_frame, textvariable=self.output_file_var, width=50).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=self.browse_output_file).grid(row=1, column=2, pady=2)
        
        ttk.Button(file_frame, text="Load File", command=self.load_file).grid(row=2, column=1, pady=10)
        
        # Progress info
        self.progress_var = tk.StringVar(value="No file loaded")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=1, column=0, columnspan=2, pady=5)
        
        # Note display frame
        note_frame = ttk.LabelFrame(main_frame, text="Current Note", padding="5")
        note_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        note_frame.columnconfigure(1, weight=1)
        
        # Note content display
        self.setup_note_display(note_frame)
        
        # Card type selection
        card_frame = ttk.LabelFrame(main_frame, text="Card Type Selection", padding="5")
        card_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.card_type_vars = {}
        for i, (card_type, description) in enumerate(self.card_types.items()):
            var = tk.BooleanVar()
            self.card_type_vars[card_type] = var
            ttk.Checkbutton(card_frame, text=f"Type {card_type}: {description}", 
                           variable=var).grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # Generated content preview
        preview_frame = ttk.LabelFrame(main_frame, text="Generated Content Preview", padding="5")
        preview_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=10, width=80)
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Previous", command=self.previous_note).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Generate Preview", command=self.generate_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Accept & Next", command=self.accept_and_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Skip", command=self.skip_note).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save All", command=self.save_all).pack(side=tk.RIGHT, padx=5)
        
        # Initially disable controls
        self.toggle_controls(False)
        
    def setup_note_display(self, parent):
        """Setup the note display area"""
        # Word
        ttk.Label(parent, text="Word:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.word_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.word_var, font=("Arial", 14, "bold")).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Definitions
        ttk.Label(parent, text="Definitions:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.def_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.def_var, wraplength=400).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Example sentence
        ttk.Label(parent, text="Example:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.example_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.example_var, wraplength=400).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Translation
        ttk.Label(parent, text="Translation:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.translation_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.translation_var, wraplength=400).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Media info
        ttk.Label(parent, text="Media:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.media_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.media_var).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # Image preview (if available)
        self.image_label = ttk.Label(parent)
        self.image_label.grid(row=5, column=0, columnspan=2, pady=5)
        
    def browse_input_file(self):
        """Browse for input file"""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.input_file_var.set(filename)
            # Auto-generate output filename
            base_name = os.path.splitext(filename)[0]
            self.output_file_var.set(f"{base_name}_processed.txt")
    
    def browse_output_file(self):
        """Browse for output file"""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.output_file_var.set(filename)
    
    def load_file(self):
        """Load and parse the input file"""
        input_file = self.input_file_var.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Error", "Please select a valid input file")
            return
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip header lines (starting with #)
            data_lines = [line for line in lines if not line.strip().startswith('#') and line.strip()]
            
            self.notes = []
            for line in data_lines:
                fields = line.strip().split('\t')
                if len(fields) >= 1:  # At least word field
                    note = AnkiNote(fields)
                    self.notes.append(note)
            
            if not self.notes:
                messagebox.showerror("Error", "No valid notes found in file")
                return
            
            self.current_note_index = 0
            self.processed_notes = []
            self.update_display()
            self.toggle_controls(True)
            
            messagebox.showinfo("Success", f"Loaded {len(self.notes)} notes")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def update_display(self):
        """Update the display with current note information"""
        if not self.notes or self.current_note_index >= len(self.notes):
            return
        
        note = self.notes[self.current_note_index]
        
        # Update progress
        self.progress_var.set(f"Note {self.current_note_index + 1} of {len(self.notes)}")
        
        # Update note display
        self.word_var.set(note.word)
        self.def_var.set(f"{note.clean_definitions_1}\n{note.clean_definitions_2}")
        self.example_var.set(note.clean_sentence)
        self.translation_var.set(note.sentence_translation)
        
        # Update media info
        media_info = []
        if note.word_audio:
            media_info.append(f"Audio: {note.word_audio}")
        if note.sentence_audio:
            media_info.append(f"Sentence Audio: {note.sentence_audio}")
        if note.image:
            media_info.append(f"Image: {note.image}")
        self.media_var.set(" | ".join(media_info))
        
        # Update image preview (basic implementation)
        self.image_label.config(image='', text='')
        
        # Update suggested card types
        suggested_types = note.suggest_card_types()
        for card_type, var in self.card_type_vars.items():
            var.set(card_type in suggested_types)
        
        # Clear preview
        self.preview_text.delete(1.0, tk.END)
    
    def generate_preview(self):
        """Generate and display preview of content"""
        if not self.notes or self.current_note_index >= len(self.notes):
            return
        
        note = self.notes[self.current_note_index]
        
        # Get selected card types
        selected_types = [card_type for card_type, var in self.card_type_vars.items() if var.get()]
        
        if not selected_types:
            messagebox.showwarning("Warning", "Please select at least one card type")
            return
        
        # Generate content
        note.generate_content(selected_types)
        
        # Display preview
        self.preview_text.delete(1.0, tk.END)
        
        preview_text = f"Generated content for card types: {', '.join(map(str, selected_types))}\n\n"
        
        # Show generated fields
        output_fields = note.to_output_fields()
        field_names = [
            "Word", "Definitions 1", "Definitions 2", "Example Sentence",
            "Sentence Translation", "Word Audio", "Sentence Audio", "Image",
            "Cloze Sentence", "Cloze Sentence Pinyin", "Scrambled Sentence",
            "Scrambled Sentence Pinyin", "Reconstructed Sentence",
            "Reconstructed Sentence Pinyin", "Prompt", "Word Pinyin",
            "Example Sentence Pinyin"
        ]
        
        for i, (name, value) in enumerate(zip(field_names, output_fields)):
            if value:  # Only show non-empty fields
                preview_text += f"{name}: {value}\n"
        
        self.preview_text.insert(1.0, preview_text)
    
    def accept_and_next(self):
        """Accept current note and move to next"""
        if not self.notes or self.current_note_index >= len(self.notes):
            return
        
        note = self.notes[self.current_note_index]
        
        # Get selected card types
        selected_types = [card_type for card_type, var in self.card_type_vars.items() if var.get()]
        
        if not selected_types:
            messagebox.showwarning("Warning", "Please select at least one card type")
            return
        
        # Generate content
        note.generate_content(selected_types)
        
        # Add to processed notes
        self.processed_notes.append(note)
        
        # Move to next note
        self.next_note()
    
    def skip_note(self):
        """Skip current note without processing"""
        self.next_note()
    
    def next_note(self):
        """Move to next note"""
        if self.current_note_index < len(self.notes) - 1:
            self.current_note_index += 1
            self.update_display()
        else:
            messagebox.showinfo("Complete", "All notes processed!")
            self.toggle_controls(False)
    
    def previous_note(self):
        """Move to previous note"""
        if self.current_note_index > 0:
            self.current_note_index -= 1
            self.update_display()
    
    def save_all(self):
        """Save all processed notes to output file"""
        if not self.processed_notes:
            messagebox.showwarning("Warning", "No notes processed yet")
            return
        
        output_file = self.output_file_var.get()
        if not output_file:
            messagebox.showerror("Error", "Please specify an output file")
            return
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header
                f.write("#separator:tab\n")
                f.write("#html:true\n")
                f.write("#tags column:18\n")
                
                # Write notes
                for note in self.processed_notes:
                    fields = note.to_output_fields()
                    f.write('\t'.join(fields) + '\n')
            
            messagebox.showinfo("Success", f"Saved {len(self.processed_notes)} notes to {output_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def toggle_controls(self, enabled: bool):
        """Enable or disable controls based on file load state"""
        # This is a simplified implementation
        # In a full implementation, you'd iterate through all controls
        pass


def main():
    """Main application entry point"""
    if len(sys.argv) > 1:
        # Command line mode
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        if not output_file:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_processed.txt"
        
        print(f"Processing {input_file} -> {output_file}")
        
        # Load and process file
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip header lines
            data_lines = [line for line in lines if not line.strip().startswith('#') and line.strip()]
            
            notes = []
            for line in data_lines:
                fields = line.strip().split('\t')
                if len(fields) >= 1:
                    note = AnkiNote(fields)
                    # Auto-select all card types for command line mode
                    note.generate_content([1, 2, 3, 4, 5])
                    notes.append(note)
            
            # Write output
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("#separator:tab\n")
                f.write("#html:true\n")
                f.write("#tags column:18\n")
                
                for note in notes:
                    fields = note.to_output_fields()
                    f.write('\t'.join(fields) + '\n')
            
            print(f"Processed {len(notes)} notes successfully")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    
    else:
        # GUI mode
        root = tk.Tk()
        app = AnkiProcessorGUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()