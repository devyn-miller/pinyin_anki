#!/usr/bin/env python3
"""
Anki Card Converter - Convert Yomitan + ASB Player exports to enhanced 17-field format
Supports 5 distinct card types with intelligent suggestions and GUI interface
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import random
from typing import List, Dict, Optional, Tuple
import os
import sys

# Install pypinyin if not available
try:
    from pypinyin import pinyin, lazy_pinyin, Style
except ImportError:
    print("pypinyin not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypinyin"])
    from pypinyin import pinyin, lazy_pinyin, Style

class AnkiCardConverter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Anki Card Converter - Yomitan + ASB Player to 17-Field Format")
        self.root.geometry("1000x800")
        
        # Data storage
        self.input_data = []
        self.output_data = []
        self.current_index = 0
        self.input_file = None
        self.output_file = None
        
        # Card type variables
        self.card_types = {
            'type1': tk.BooleanVar(),  # Image + Audio
            'type2': tk.BooleanVar(),  # Function words
            'type3': tk.BooleanVar(),  # Complex grammar
            'type4': tk.BooleanVar(),  # Tricky word order
            'type5': tk.BooleanVar()   # Reconstruction
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the main UI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Button(file_frame, text="Select Input File", command=self.select_input_file).grid(row=0, column=0, padx=(0, 10))
        self.input_label = ttk.Label(file_frame, text="No file selected")
        self.input_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Button(file_frame, text="Select Output File", command=self.select_output_file).grid(row=1, column=0, padx=(0, 10))
        self.output_label = ttk.Label(file_frame, text="No output file selected")
        self.output_label.grid(row=1, column=1, sticky=tk.W)
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(1, weight=1)
        
        self.progress_label = ttk.Label(progress_frame, text="Progress: 0/0")
        self.progress_label.grid(row=0, column=0, padx=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Current item frame
        item_frame = ttk.LabelFrame(main_frame, text="Current Item", padding="5")
        item_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        item_frame.columnconfigure(1, weight=1)
        
        # Word and basic info
        ttk.Label(item_frame, text="Word:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.word_var = tk.StringVar()
        self.word_entry = ttk.Entry(item_frame, textvariable=self.word_var, width=20)
        self.word_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(item_frame, text="Pinyin:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.word_pinyin_var = tk.StringVar()
        self.word_pinyin_entry = ttk.Entry(item_frame, textvariable=self.word_pinyin_var, width=20)
        self.word_pinyin_entry.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        # Sentence
        ttk.Label(item_frame, text="Sentence:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.sentence_var = tk.StringVar()
        self.sentence_entry = ttk.Entry(item_frame, textvariable=self.sentence_var, width=50)
        self.sentence_entry.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E))
        
        # Sentence translation
        ttk.Label(item_frame, text="Translation:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        self.translation_var = tk.StringVar()
        self.translation_entry = ttk.Entry(item_frame, textvariable=self.translation_var, width=50)
        self.translation_entry.grid(row=2, column=1, columnspan=3, sticky=(tk.W, tk.E))
        
        # Audio files
        ttk.Label(item_frame, text="Audio Files:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10))
        self.audio_var = tk.StringVar()
        self.audio_label = ttk.Label(item_frame, textvariable=self.audio_var)
        self.audio_label.grid(row=3, column=1, columnspan=3, sticky=tk.W)
        
        # Image preview
        self.image_var = tk.StringVar()
        self.image_label = ttk.Label(item_frame, text="No image")
        self.image_label.grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # Card type selection
        card_frame = ttk.LabelFrame(main_frame, text="Card Types (Auto-suggested)", padding="5")
        card_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        card_descriptions = {
            'type1': 'Type 1: Image + Audio (concrete nouns)',
            'type2': 'Type 2: Function words/particles',
            'type3': 'Type 3: Complex grammar',
            'type4': 'Type 4: Tricky word order',
            'type5': 'Type 5: Sentence reconstruction'
        }
        
        for i, (key, desc) in enumerate(card_descriptions.items()):
            ttk.Checkbutton(card_frame, text=desc, variable=self.card_types[key]).grid(
                row=i, column=0, sticky=tk.W, pady=2
            )
        
        # Generated fields frame
        fields_frame = ttk.LabelFrame(main_frame, text="Generated Fields (Editable)", padding="5")
        fields_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        fields_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Create scrollable text areas for generated fields
        self.field_vars = {}
        field_labels = [
            ('cloze_sentence', 'Cloze Sentence'),
            ('scrambled_sentence', 'Scrambled Sentence'),
            ('prompt', 'Prompt'),
            ('sentence_pinyin', 'Sentence Pinyin')
        ]
        
        for i, (key, label) in enumerate(field_labels):
            ttk.Label(fields_frame, text=f"{label}:").grid(row=i, column=0, sticky=(tk.W, tk.N), padx=(0, 10))
            self.field_vars[key] = tk.StringVar()
            entry = ttk.Entry(fields_frame, textvariable=self.field_vars[key], width=60)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Previous", command=self.previous_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Skip", command=self.skip_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Save & Next", command=self.save_and_next).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Regenerate", command=self.regenerate_suggestions).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Export All", command=self.export_data).pack(side=tk.LEFT, padx=(0, 5))
        
    def select_input_file(self):
        """Select input .txt file"""
        filename = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.input_file = filename
            self.input_label.config(text=f"Input: {os.path.basename(filename)}")
            self.load_input_data()
    
    def select_output_file(self):
        """Select output .txt file"""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.output_file = filename
            self.output_label.config(text=f"Output: {os.path.basename(filename)}")
    
    def load_input_data(self):
        """Load and parse input data"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Skip header lines starting with #
            lines = [line for line in content.split('\n') if line.strip() and not line.startswith('#')]
            
            self.input_data = []
            for line in lines:
                fields = line.split('\t')
                if len(fields) >= 8:
                    self.input_data.append({
                        'word': fields[0],
                        'definitions1': fields[1],
                        'definitions2': fields[2],
                        'example_sentence': fields[3],
                        'sentence_translation': fields[4],
                        'word_audio': fields[5],
                        'sentence_audio': fields[6],
                        'image': fields[7] if len(fields) > 7 else ''
                    })
            
            self.current_index = 0
            self.progress_bar['maximum'] = len(self.input_data)
            self.update_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load input file: {str(e)}")
    
    def generate_pinyin(self, text: str) -> str:
        """Generate pinyin for Chinese text"""
        if not text.strip():
            return ""
        try:
            # Remove punctuation and generate pinyin
            chinese_chars = re.sub(r'[^\u4e00-\u9fff]', '', text)
            if not chinese_chars:
                return ""
            pinyin_result = lazy_pinyin(chinese_chars, style=Style.TONE)
            return ' '.join(pinyin_result)
        except:
            return ""
    
    def create_cloze_sentence(self, sentence: str, word: str) -> str:
        """Create cloze deletion by replacing target word with blanks"""
        if not sentence or not word:
            return sentence
        
        # Replace the word with blanks
        cloze = sentence.replace(word, '___')
        if cloze == sentence:  # Word not found exactly, try partial matches
            # Find the word in the sentence (handling multi-character words)
            for i in range(len(sentence) - len(word) + 1):
                if sentence[i:i+len(word)] == word:
                    cloze = sentence[:i] + '___' + sentence[i+len(word):]
                    break
        return cloze
    
    def create_scrambled_sentence(self, sentence: str) -> str:
        """Create scrambled sentence by randomizing word order"""
        if not sentence:
            return ""
        
        # Simple word segmentation - split by common punctuation and spaces
        words = []
        current_word = ""
        
        for char in sentence:
            if char in '，。！？；：、':
                if current_word:
                    words.append(current_word)
                    current_word = ""
                words.append(char)
            elif char.isspace():
                if current_word:
                    words.append(current_word)
                    current_word = ""
            else:
                current_word += char
        
        if current_word:
            words.append(current_word)
        
        # Simple scrambling - break into segments and shuffle
        segments = []
        current_segment = ""
        
        for word in words:
            if word in '，。！？；：、':
                if current_segment:
                    segments.append(current_segment.strip())
                    current_segment = ""
            else:
                current_segment += word + " "
        
        if current_segment:
            segments.append(current_segment.strip())
        
        # Shuffle segments and join with " / "
        if segments:
            random.shuffle(segments)
            return " / ".join(segments)
        else:
            # Fallback: just split by characters for very short sentences
            chars = [c for c in sentence if c.strip()]
            random.shuffle(chars)
            return " / ".join(chars)
    
    def generate_prompt(self, word: str, definition: str, sentence: str) -> str:
        """Generate a prompt for the word based on context"""
        if not word or not definition:
            return ""
        
        # Extract key concepts from definition
        key_concepts = []
        if "born" in definition.lower():
            key_concepts.append("birth/life")
        if "student" in definition.lower():
            key_concepts.append("education")
        if "grow" in definition.lower():
            key_concepts.append("growth")
        if "raw" in definition.lower():
            key_concepts.append("uncooked")
        
        if key_concepts:
            return f"Related to: {', '.join(key_concepts)}"
        else:
            # Fallback: use first part of definition
            first_part = definition.split('/')[0].strip()
            return f"Means: {first_part}"
    
    def suggest_card_types(self, data: Dict) -> None:
        """Suggest card types based on heuristics"""
        word = data['word']
        sentence = data['example_sentence']
        definition = data['definitions1']
        has_image = bool(data['image'].strip())
        
        # Reset all card types
        for var in self.card_types.values():
            var.set(False)
        
        # Type 1: Image + Audio (concrete nouns)
        concrete_indicators = ['person', 'thing', 'object', 'animal', 'food', 'place', 'building']
        if has_image or any(indicator in definition.lower() for indicator in concrete_indicators):
            self.card_types['type1'].set(True)
        
        # Type 2: Function words/particles
        function_words = ['的', '了', '在', '是', '和', '或', '但', '而', '如果', '要是', '也', '都', '还', '又']
        if len(word) <= 2 and word in function_words:
            self.card_types['type2'].set(True)
        
        # Type 3: Complex grammar (long sentences, complex structures)
        if len(sentence) > 15 and ('要是' in sentence or '如果' in sentence or '虽然' in sentence):
            self.card_types['type3'].set(True)
        
        # Type 4: Tricky word order
        if len(sentence) > 10 and len(sentence.split()) > 8:
            self.card_types['type4'].set(True)
        
        # Type 5: Reconstruction (rich, memorable sentences)
        if len(sentence) > 8 and len(sentence) < 25:
            self.card_types['type5'].set(True)
    
    def update_display(self):
        """Update the display with current item data"""
        if not self.input_data or self.current_index >= len(self.input_data):
            return
        
        data = self.input_data[self.current_index]
        
        # Update basic fields
        self.word_var.set(data['word'])
        self.sentence_var.set(data['example_sentence'])
        self.translation_var.set(data['sentence_translation'])
        
        # Update audio info
        audio_info = f"Word: {data['word_audio']}, Sentence: {data['sentence_audio']}"
        self.audio_var.set(audio_info)
        
        # Update image info
        if data['image'].strip():
            self.image_label.config(text=f"Image: {data['image']}")
        else:
            self.image_label.config(text="No image")
        
        # Generate pinyin
        word_pinyin = self.generate_pinyin(data['word'])
        sentence_pinyin = self.generate_pinyin(data['example_sentence'])
        self.word_pinyin_var.set(word_pinyin)
        
        # Generate other fields
        cloze = self.create_cloze_sentence(data['example_sentence'], data['word'])
        scrambled = self.create_scrambled_sentence(data['example_sentence'])
        prompt = self.generate_prompt(data['word'], data['definitions1'], data['example_sentence'])
        
        self.field_vars['cloze_sentence'].set(cloze)
        self.field_vars['scrambled_sentence'].set(scrambled)
        self.field_vars['prompt'].set(prompt)
        self.field_vars['sentence_pinyin'].set(sentence_pinyin)
        
        # Suggest card types
        self.suggest_card_types(data)
        
        # Update progress
        self.progress_label.config(text=f"Progress: {self.current_index + 1}/{len(self.input_data)}")
        self.progress_bar['value'] = self.current_index + 1
    
    def regenerate_suggestions(self):
        """Regenerate suggestions for current item"""
        if not self.input_data or self.current_index >= len(self.input_data):
            return
        
        data = self.input_data[self.current_index]
        
        # Regenerate scrambled sentence with different randomization
        scrambled = self.create_scrambled_sentence(data['example_sentence'])
        self.field_vars['scrambled_sentence'].set(scrambled)
        
        # Regenerate card type suggestions
        self.suggest_card_types(data)
    
    def previous_item(self):
        """Go to previous item"""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()
    
    def skip_item(self):
        """Skip current item"""
        if self.current_index < len(self.input_data) - 1:
            self.current_index += 1
            self.update_display()
    
    def save_and_next(self):
        """Save current item and go to next"""
        if not self.input_data or self.current_index >= len(self.input_data):
            return
        
        # Get current data
        data = self.input_data[self.current_index]
        
        # Create 17-field output
        output_row = self.create_output_row(data)
        self.output_data.append(output_row)
        
        # Move to next item
        if self.current_index < len(self.input_data) - 1:
            self.current_index += 1
            self.update_display()
        else:
            messagebox.showinfo("Complete", "All items processed!")
    
    def create_output_row(self, data: Dict) -> List[str]:
        """Create a 17-field output row based on current settings"""
        # Get selected card types
        selected_types = [k for k, v in self.card_types.items() if v.get()]
        
        # Conditional fields based on selected card types
        cloze_sentence = self.field_vars['cloze_sentence'].get() if 'type3' in selected_types else ''
        cloze_pinyin = self.generate_pinyin(cloze_sentence) if cloze_sentence else ''
        
        scrambled_sentence = self.field_vars['scrambled_sentence'].get() if 'type4' in selected_types else ''
        scrambled_pinyin = self.generate_pinyin(scrambled_sentence.replace(' / ', '')) if scrambled_sentence else ''
        
        reconstructed = data['example_sentence'] if 'type5' in selected_types else ''
        reconstructed_pinyin = self.field_vars['sentence_pinyin'].get() if 'type5' in selected_types else ''
        
        prompt = self.field_vars['prompt'].get() if any(t in selected_types for t in ['type1', 'type2']) else ''
        
        # Create the 17 fields in the correct order as shown in the Anki field mapping
        row = [
            data['word'],                           # 1. Word
            self.word_pinyin_var.get(),            # 2. Word_Pinyin
            data['definitions1'],                   # 3. Definitions 1
            data['definitions2'],                   # 4. Definitions 2
            data['example_sentence'],               # 5. Example Sentence
            self.field_vars['sentence_pinyin'].get(), # 6. Example_Sentence_Pinyin
            data['sentence_translation'],           # 7. Sentence Translation
            data['word_audio'],                     # 8. word_audio
            data['sentence_audio'],                 # 9. sentence_audio
            data['image'],                          # 10. image
            cloze_sentence,                         # 11. cloze_sentence
            cloze_pinyin,                          # 12. cloze_sentence_pinyin
            prompt,                                # 13. prompt
            scrambled_sentence,                    # 14. scrambled_sentence
            scrambled_pinyin,                      # 15. scrambled_sentence_pinyin
            reconstructed,                         # 16. reconstructed_sentence
            reconstructed_pinyin,                  # 17. reconstructed_sentence_pinyin
        ]
        
        return row
    
    def export_data(self):
        """Export all processed data to output file"""
        if not self.output_file:
            messagebox.showerror("Error", "Please select an output file first")
            return
        
        if not self.output_data:
            messagebox.showerror("Error", "No data to export")
            return
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # Write Anki import headers
                f.write("#separator:tab\n")
                f.write("#html:true\n")
                
                # Write data rows
                for row in self.output_data:
                    f.write('\t'.join(row) + '\n')
            
            messagebox.showinfo("Success", f"Exported {len(self.output_data)} rows to {self.output_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = AnkiCardConverter()
    app.run()