#!/usr/bin/env python3
"""
Anki Card Type Generator
========================

A Python script to process .txt Anki decks exported from Yomitan + ASB Player,
transforming 8-field input into 17-field output for 5 distinct card types.

Requirements:
- Python 3.7+
- tkinter (usually included with Python)
- pypinyin: pip install pypinyin
- Pillow: pip install Pillow

Usage:
    python anki_card_generator.py

Features:
- GUI preview and edit interface for each row
- Automatic card type suggestions using heuristics
- Automated content generation for selected fields
- Manual approval/editing of generated content
- Preserves media filenames without modification
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter import font as tkFont
import os
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from PIL import Image, ImageTk
import pypinyin


@dataclass
class AnkiNote:
    """Represents a single Anki note with all 17 fields"""
    
    # Original 8 fields from input
    word: str = ""
    definitions_1: str = ""
    definitions_2: str = ""
    example_sentence: str = ""
    sentence_translation: str = ""
    word_audio: str = ""
    sentence_audio: str = ""
    image: str = ""
    
    # Additional 9 fields for card types
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
    selected_card_types: List[int] = field(default_factory=list)


class CardTypeHeuristics:
    """Heuristic engine for suggesting appropriate card types"""
    
    # Common Chinese function words and particles
    FUNCTION_WORDS = {
        '的', '了', '在', '是', '有', '和', '与', '或', '但', '而', '因为', '所以',
        '如果', '虽然', '但是', '然而', '不过', '可是', '却', '还是', '就是', '只是',
        '那么', '这么', '怎么', '为什么', '什么', '哪里', '哪儿', '怎样', '多少'
    }
    
    # Words that typically indicate concrete nouns
    CONCRETE_NOUN_INDICATORS = {
        '书', '车', '房', '桌', '椅', '门', '窗', '花', '树', '水', '火', '山', '河',
        '海', '天', '地', '人', '狗', '猫', '鸟', '鱼', '米', '菜', '肉', '蛋', '奶'
    }
    
    @staticmethod
    def suggest_card_types(note: AnkiNote) -> List[int]:
        """
        Analyze the note and suggest appropriate card types
        
        Returns:
            List of suggested card type numbers (1-5)
        """
        suggestions = []
        word = note.word.strip()
        sentence = note.example_sentence.strip()
        
        # Card 1: Picture + Audio Recognition
        # Suggest if word is a concrete noun or has an image
        if (note.image or 
            word in CardTypeHeuristics.CONCRETE_NOUN_INDICATORS or
            CardTypeHeuristics._is_concrete_noun(word)):
            suggestions.append(1)
        
        # Card 2: Basic Cloze Sentence
        # Good for function words or when other complex cards aren't suitable
        if word in CardTypeHeuristics.FUNCTION_WORDS:
            suggestions.append(2)
        
        # Card 3: Cloze + Prompt
        # Suggest for grammar patterns or complex usage
        if (CardTypeHeuristics._has_grammar_pattern(sentence) or
            len(word) > 1 and word not in CardTypeHeuristics.FUNCTION_WORDS):
            suggestions.append(3)
        
        # Card 4: Word Placement
        # Good for function words or when word order is important
        if (word in CardTypeHeuristics.FUNCTION_WORDS or
            CardTypeHeuristics._has_complex_word_order(sentence)):
            suggestions.append(4)
        
        # Card 5: Sentence Reconstruction
        # Suggest for memorable, short sentences
        if (len(sentence) <= 15 and  # Short sentences
            CardTypeHeuristics._is_memorable_sentence(sentence)):
            suggestions.append(5)
        
        # Ensure at least one card type is suggested
        if not suggestions:
            suggestions.append(2)  # Default to basic cloze
        
        return suggestions
    
    @staticmethod
    def _is_concrete_noun(word: str) -> bool:
        """Check if word is likely a concrete noun"""
        # Simple heuristic: single character words that aren't function words
        return len(word) == 1 and word not in CardTypeHeuristics.FUNCTION_WORDS
    
    @staticmethod
    def _has_grammar_pattern(sentence: str) -> bool:
        """Check if sentence contains common grammar patterns"""
        patterns = ['因为', '所以', '虽然', '但是', '如果', '就', '才', '都', '还', '也']
        return any(pattern in sentence for pattern in patterns)
    
    @staticmethod
    def _has_complex_word_order(sentence: str) -> bool:
        """Check if sentence has complex word order"""
        # Simple heuristic: sentences with multiple clauses or specific patterns
        return len(sentence) > 10 and ('，' in sentence or '、' in sentence)
    
    @staticmethod
    def _is_memorable_sentence(sentence: str) -> bool:
        """Check if sentence is memorable/suitable for reconstruction"""
        # Heuristic: not too complex, has clear structure
        return (len(sentence) <= 15 and 
                sentence.count('，') <= 1 and
                not sentence.startswith('这是'))


class ContentGenerator:
    """Generates content for various card types"""
    
    @staticmethod
    def generate_pinyin(text: str) -> str:
        """Generate pinyin for Chinese text"""
        try:
            # Convert to pinyin with tone marks
            pinyin_list = pypinyin.pinyin(text, style=pypinyin.TONE, heteronym=False)
            return ' '.join([item[0] for item in pinyin_list])
        except Exception as e:
            print(f"Error generating pinyin for '{text}': {e}")
            return text
    
    @staticmethod
    def generate_cloze_sentence(sentence: str, word: str) -> str:
        """Generate cloze sentence by replacing the word with ___"""
        if word in sentence:
            return sentence.replace(word, "___", 1)
        return sentence
    
    @staticmethod
    def generate_scrambled_sentence(sentence: str, word: str) -> str:
        """Generate scrambled sentence with word removed"""
        if word in sentence:
            # Remove the word and add it at the beginning with a blank space
            without_word = sentence.replace(word, "___", 1)
            return without_word
        return sentence
    
    @staticmethod
    def generate_prompt(word: str, sentence: str) -> str:
        """Generate helpful prompt for the word"""
        prompts = {
            '的': "Possessive particle, shows ownership or description",
            '了': "Aspect particle, indicates completed action",
            '在': "Preposition indicating location or ongoing action",
            '是': "Copula verb 'to be'",
            '有': "Verb 'to have' or existence",
            '和': "Conjunction meaning 'and'",
            '不': "Negation particle",
            '很': "Adverb meaning 'very'",
            '都': "Adverb meaning 'all' or 'both'",
            '也': "Adverb meaning 'also' or 'too'",
        }
        
        if word in prompts:
            return prompts[word]
        
        # Generic prompts based on word characteristics
        if len(word) == 1:
            return f"Single character word, pay attention to usage context"
        elif len(word) == 2:
            return f"Two-character word, common in modern Chinese"
        else:
            return f"Multi-character word, often compound meaning"
    
    @staticmethod
    def populate_card_fields(note: AnkiNote) -> AnkiNote:
        """Populate all generated fields based on selected card types"""
        
        # Always generate pinyin for word and sentence
        note.word_pinyin = ContentGenerator.generate_pinyin(note.word)
        note.example_sentence_pinyin = ContentGenerator.generate_pinyin(note.example_sentence)
        
        # Generate content based on selected card types
        if 2 in note.selected_card_types or 3 in note.selected_card_types:
            # Cloze sentence needed for cards 2 and 3
            note.cloze_sentence = ContentGenerator.generate_cloze_sentence(
                note.example_sentence, note.word
            )
            note.cloze_sentence_pinyin = ContentGenerator.generate_pinyin(note.cloze_sentence)
        
        if 3 in note.selected_card_types:
            # Prompt needed for card 3
            note.prompt = ContentGenerator.generate_prompt(note.word, note.example_sentence)
        
        if 4 in note.selected_card_types:
            # Scrambled sentence for card 4
            note.scrambled_sentence = ContentGenerator.generate_scrambled_sentence(
                note.example_sentence, note.word
            )
            note.scrambled_sentence_pinyin = ContentGenerator.generate_pinyin(note.scrambled_sentence)
        
        if 5 in note.selected_card_types:
            # Reconstructed sentence for card 5 (same as original)
            note.reconstructed_sentence = note.example_sentence
            note.reconstructed_sentence_pinyin = note.example_sentence_pinyin
        
        return note


class AnkiCardGUI:
    """Main GUI application for processing Anki cards"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Anki Card Type Generator")
        self.root.geometry("1000x800")
        
        # Data storage
        self.input_notes: List[AnkiNote] = []
        self.output_notes: List[AnkiNote] = []
        self.current_note_index = 0
        self.current_note: Optional[AnkiNote] = None
        
        # GUI variables
        self.card_type_vars = {i: tk.BooleanVar() for i in range(1, 6)}
        
        # Create GUI
        self.create_widgets()
        
        # Load custom fonts
        self.setup_fonts()
    
    def setup_fonts(self):
        """Setup custom fonts for better Chinese character display"""
        try:
            self.chinese_font = tkFont.Font(family="SimHei", size=12)
            self.chinese_large_font = tkFont.Font(family="SimHei", size=14, weight="bold")
        except:
            # Fallback fonts
            self.chinese_font = tkFont.Font(family="Arial Unicode MS", size=12)
            self.chinese_large_font = tkFont.Font(family="Arial Unicode MS", size=14, weight="bold")
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.file_label = ttk.Label(file_frame, text="No file selected")
        self.file_label.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(file_frame, text="Select Input File", 
                  command=self.select_input_file).grid(row=0, column=1, padx=(10, 0))
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="5")
        progress_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="No notes loaded")
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        # Navigation buttons
        nav_frame = ttk.Frame(progress_frame)
        nav_frame.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Button(nav_frame, text="Previous", 
                  command=self.previous_note).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(nav_frame, text="Next", 
                  command=self.next_note).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(nav_frame, text="Skip", 
                  command=self.skip_note).grid(row=0, column=2)
        
        # Note display frame
        note_frame = ttk.LabelFrame(main_frame, text="Current Note", padding="5")
        note_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        note_frame.columnconfigure(1, weight=1)
        
        # Create note display widgets
        self.create_note_display(note_frame)
        
        # Card type selection frame
        card_frame = ttk.LabelFrame(main_frame, text="Card Type Selection", padding="5")
        card_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.create_card_type_selection(card_frame)
        
        # Edit fields frame
        edit_frame = ttk.LabelFrame(main_frame, text="Edit Generated Fields", padding="5")
        edit_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        edit_frame.columnconfigure(1, weight=1)
        edit_frame.rowconfigure(0, weight=1)
        
        self.create_edit_fields(edit_frame)
        
        # Action buttons frame
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(action_frame, text="Generate Preview", 
                  command=self.generate_preview).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(action_frame, text="Accept & Continue", 
                  command=self.accept_note).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(action_frame, text="Save All", 
                  command=self.save_output).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(action_frame, text="Exit", 
                  command=self.root.quit).grid(row=0, column=3)
    
    def create_note_display(self, parent):
        """Create widgets for displaying note information"""
        
        # Word display
        ttk.Label(parent, text="Word:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.word_label = ttk.Label(parent, text="", font=self.chinese_large_font)
        self.word_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Definitions
        ttk.Label(parent, text="Definition 1:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.def1_label = ttk.Label(parent, text="", wraplength=400)
        self.def1_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(parent, text="Definition 2:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.def2_label = ttk.Label(parent, text="", wraplength=400)
        self.def2_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Example sentence
        ttk.Label(parent, text="Example:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.example_label = ttk.Label(parent, text="", font=self.chinese_font, wraplength=400)
        self.example_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Translation
        ttk.Label(parent, text="Translation:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.translation_label = ttk.Label(parent, text="", wraplength=400)
        self.translation_label.grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # Media info
        ttk.Label(parent, text="Audio:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.audio_label = ttk.Label(parent, text="")
        self.audio_label.grid(row=5, column=1, sticky=tk.W, pady=2)
        
        # Image display
        ttk.Label(parent, text="Image:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.image_label = ttk.Label(parent, text="")
        self.image_label.grid(row=6, column=1, sticky=tk.W, pady=2)
    
    def create_card_type_selection(self, parent):
        """Create card type selection checkboxes"""
        
        card_descriptions = {
            1: "Picture + Audio Recognition",
            2: "Cloze Sentence",
            3: "Cloze + Prompt",
            4: "Word Placement",
            5: "Sentence Reconstruction"
        }
        
        for i, (card_num, description) in enumerate(card_descriptions.items()):
            checkbox = ttk.Checkbutton(
                parent,
                text=f"Card {card_num}: {description}",
                variable=self.card_type_vars[card_num],
                command=self.on_card_type_change
            )
            checkbox.grid(row=i, column=0, sticky=tk.W, pady=2)
    
    def create_edit_fields(self, parent):
        """Create text fields for editing generated content"""
        
        # Create notebook for organized editing
        notebook = ttk.Notebook(parent)
        notebook.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Generated content tab
        gen_frame = ttk.Frame(notebook)
        notebook.add(gen_frame, text="Generated Content")
        
        # Create scrollable text area
        text_frame = ttk.Frame(gen_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.edit_text = scrolledtext.ScrolledText(
            text_frame,
            width=80,
            height=15,
            font=self.chinese_font,
            wrap=tk.WORD
        )
        self.edit_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Quick edit tab
        quick_frame = ttk.Frame(notebook)
        notebook.add(quick_frame, text="Quick Edit")
        
        # Add quick edit fields for common modifications
        self.create_quick_edit_fields(quick_frame)
    
    def create_quick_edit_fields(self, parent):
        """Create quick edit fields for common modifications"""
        
        # Pinyin override
        ttk.Label(parent, text="Word Pinyin:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.pinyin_entry = ttk.Entry(parent, width=30)
        self.pinyin_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Prompt override
        ttk.Label(parent, text="Custom Prompt:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.prompt_entry = ttk.Entry(parent, width=50)
        self.prompt_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Regenerate button
        ttk.Button(parent, text="Regenerate All", 
                  command=self.regenerate_content).grid(row=2, column=0, pady=10)
    
    def select_input_file(self):
        """Select and load input file"""
        
        file_path = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.load_input_file(file_path)
                self.file_label.config(text=f"Loaded: {os.path.basename(file_path)}")
                self.update_progress_display()
                self.load_current_note()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
    
    def load_input_file(self, file_path: str):
        """Load input file and parse into AnkiNote objects"""
        
        self.input_notes = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                fields = line.split('\t')
                if len(fields) < 8:
                    print(f"Warning: Line {line_num} has only {len(fields)} fields, skipping")
                    continue
                
                note = AnkiNote(
                    word=fields[0],
                    definitions_1=fields[1],
                    definitions_2=fields[2],
                    example_sentence=fields[3],
                    sentence_translation=fields[4],
                    word_audio=fields[5],
                    sentence_audio=fields[6],
                    image=fields[7]
                )
                
                # Apply heuristics to suggest card types
                note.selected_card_types = CardTypeHeuristics.suggest_card_types(note)
                
                self.input_notes.append(note)
        
        print(f"Loaded {len(self.input_notes)} notes from {file_path}")
        self.current_note_index = 0
        self.output_notes = []
    
    def update_progress_display(self):
        """Update progress display"""
        
        if self.input_notes:
            total = len(self.input_notes)
            current = self.current_note_index + 1
            completed = len(self.output_notes)
            
            self.progress_label.config(
                text=f"Note {current} of {total} (Completed: {completed})"
            )
        else:
            self.progress_label.config(text="No notes loaded")
    
    def load_current_note(self):
        """Load current note into GUI"""
        
        if not self.input_notes or self.current_note_index >= len(self.input_notes):
            return
        
        self.current_note = self.input_notes[self.current_note_index]
        
        # Update display labels
        self.word_label.config(text=self.current_note.word)
        self.def1_label.config(text=self.current_note.definitions_1)
        self.def2_label.config(text=self.current_note.definitions_2)
        self.example_label.config(text=self.current_note.example_sentence)
        self.translation_label.config(text=self.current_note.sentence_translation)
        
        # Update audio info
        audio_info = f"Word: {self.current_note.word_audio}, Sentence: {self.current_note.sentence_audio}"
        self.audio_label.config(text=audio_info)
        
        # Update image info
        if self.current_note.image:
            self.image_label.config(text=self.current_note.image)
            # TODO: Add image preview if file exists
        else:
            self.image_label.config(text="No image")
        
        # Update card type selections
        for i in range(1, 6):
            self.card_type_vars[i].set(i in self.current_note.selected_card_types)
        
        # Update quick edit fields
        self.pinyin_entry.delete(0, tk.END)
        self.prompt_entry.delete(0, tk.END)
        
        # Generate preview
        self.generate_preview()
    
    def on_card_type_change(self):
        """Handle card type selection change"""
        
        if self.current_note:
            self.current_note.selected_card_types = [
                i for i in range(1, 6) if self.card_type_vars[i].get()
            ]
            self.generate_preview()
    
    def generate_preview(self):
        """Generate preview of the current note"""
        
        if not self.current_note:
            return
        
        # Create a copy for preview
        preview_note = AnkiNote(
            word=self.current_note.word,
            definitions_1=self.current_note.definitions_1,
            definitions_2=self.current_note.definitions_2,
            example_sentence=self.current_note.example_sentence,
            sentence_translation=self.current_note.sentence_translation,
            word_audio=self.current_note.word_audio,
            sentence_audio=self.current_note.sentence_audio,
            image=self.current_note.image,
            selected_card_types=self.current_note.selected_card_types[:]
        )
        
        # Apply custom overrides
        if self.pinyin_entry.get():
            preview_note.word_pinyin = self.pinyin_entry.get()
        if self.prompt_entry.get():
            preview_note.prompt = self.prompt_entry.get()
        
        # Generate content
        preview_note = ContentGenerator.populate_card_fields(preview_note)
        
        # Display in text area
        self.display_note_preview(preview_note)
    
    def display_note_preview(self, note: AnkiNote):
        """Display note preview in text area"""
        
        self.edit_text.delete(1.0, tk.END)
        
        preview_text = f"""=== PREVIEW: {note.word} ===

Selected Card Types: {', '.join(map(str, note.selected_card_types))}

=== ORIGINAL FIELDS ===
Word: {note.word}
Definitions 1: {note.definitions_1}
Definitions 2: {note.definitions_2}
Example Sentence: {note.example_sentence}
Sentence Translation: {note.sentence_translation}
Word Audio: {note.word_audio}
Sentence Audio: {note.sentence_audio}
Image: {note.image}

=== GENERATED FIELDS ===
Word Pinyin: {note.word_pinyin}
Example Sentence Pinyin: {note.example_sentence_pinyin}
"""
        
        if note.cloze_sentence:
            preview_text += f"Cloze Sentence: {note.cloze_sentence}\n"
            preview_text += f"Cloze Sentence Pinyin: {note.cloze_sentence_pinyin}\n"
        
        if note.scrambled_sentence:
            preview_text += f"Scrambled Sentence: {note.scrambled_sentence}\n"
            preview_text += f"Scrambled Sentence Pinyin: {note.scrambled_sentence_pinyin}\n"
        
        if note.reconstructed_sentence:
            preview_text += f"Reconstructed Sentence: {note.reconstructed_sentence}\n"
            preview_text += f"Reconstructed Sentence Pinyin: {note.reconstructed_sentence_pinyin}\n"
        
        if note.prompt:
            preview_text += f"Prompt: {note.prompt}\n"
        
        preview_text += f"""
=== OUTPUT FORMAT (17 fields) ===
{note.word}	{note.definitions_1}	{note.definitions_2}	{note.example_sentence}	{note.sentence_translation}	{note.word_audio}	{note.sentence_audio}	{note.image}	{note.cloze_sentence}	{note.cloze_sentence_pinyin}	{note.scrambled_sentence}	{note.scrambled_sentence_pinyin}	{note.reconstructed_sentence}	{note.reconstructed_sentence_pinyin}	{note.prompt}	{note.word_pinyin}	{note.example_sentence_pinyin}
"""
        
        self.edit_text.insert(1.0, preview_text)
    
    def regenerate_content(self):
        """Regenerate content with current settings"""
        self.generate_preview()
    
    def accept_note(self):
        """Accept current note and move to next"""
        
        if not self.current_note:
            return
        
        # Apply custom overrides
        if self.pinyin_entry.get():
            self.current_note.word_pinyin = self.pinyin_entry.get()
        if self.prompt_entry.get():
            self.current_note.prompt = self.prompt_entry.get()
        
        # Generate final content
        final_note = ContentGenerator.populate_card_fields(self.current_note)
        
        # Add to output notes
        self.output_notes.append(final_note)
        
        # Move to next note
        self.next_note()
    
    def next_note(self):
        """Move to next note"""
        
        if self.current_note_index < len(self.input_notes) - 1:
            self.current_note_index += 1
            self.update_progress_display()
            self.load_current_note()
        else:
            messagebox.showinfo("Complete", "All notes have been processed!")
    
    def previous_note(self):
        """Move to previous note"""
        
        if self.current_note_index > 0:
            self.current_note_index -= 1
            self.update_progress_display()
            self.load_current_note()
    
    def skip_note(self):
        """Skip current note without processing"""
        
        if self.current_note_index < len(self.input_notes) - 1:
            self.current_note_index += 1
            self.update_progress_display()
            self.load_current_note()
        else:
            messagebox.showinfo("Complete", "Reached end of notes!")
    
    def save_output(self):
        """Save processed notes to output file"""
        
        if not self.output_notes:
            messagebox.showwarning("Warning", "No processed notes to save!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Output File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.write_output_file(file_path)
                messagebox.showinfo("Success", f"Saved {len(self.output_notes)} notes to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def write_output_file(self, file_path: str):
        """Write output notes to file in 17-field format"""
        
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            for note in self.output_notes:
                fields = [
                    note.word,
                    note.definitions_1,
                    note.definitions_2,
                    note.example_sentence,
                    note.sentence_translation,
                    note.word_audio,
                    note.sentence_audio,
                    note.image,
                    note.cloze_sentence,
                    note.cloze_sentence_pinyin,
                    note.scrambled_sentence,
                    note.scrambled_sentence_pinyin,
                    note.reconstructed_sentence,
                    note.reconstructed_sentence_pinyin,
                    note.prompt,
                    note.word_pinyin,
                    note.example_sentence_pinyin
                ]
                
                # Join with tabs and write
                f.write('\t'.join(fields) + '\n')


def main():
    """Main application entry point"""
    
    # Check dependencies
    try:
        import pypinyin
        from PIL import Image, ImageTk
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nPlease install required packages:")
        print("pip install pypinyin Pillow")
        return
    
    # Create and run GUI
    root = tk.Tk()
    app = AnkiCardGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()