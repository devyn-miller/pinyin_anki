#!/usr/bin/env python3
"""
Chinese Vocabulary Anki Deck Generator
A modular automation pipeline for converting CSV vocabulary into image-enhanced Anki decks
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import requests
import os
import shutil
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk, ImageGrab
import genanki
import random
import threading
from typing import Optional, List, Dict, Any
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('anki_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PexelsImageFetcher:
    """Module for fetching images from Pexels API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/v1/search"
        self.headers = {"Authorization": api_key}
        
    def search_images(self, query: str, per_page: int = 5) -> List[Dict]:
        """Search for images using Pexels API"""
        try:
            params = {
                "query": query,
                "per_page": per_page,
                "size": "medium"
            }
            
            response = requests.get(
                self.base_url, 
                headers=self.headers, 
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("photos", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching images for '{query}': {e}")
            return []
    
    def download_image(self, url: str, filepath: str) -> bool:
        """Download image from URL to local filepath"""
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded image: {filepath}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return False

class StateManager:
    """Manages pipeline state and CSV operations"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        self.current_index = 0
        self.load_csv()
        
    def load_csv(self):
        """Load CSV and ensure required columns exist"""
        try:
            self.df = pd.read_csv(self.csv_path)
            
            # Ensure required columns exist
            required_cols = ['simplified', 'pinyin', 'english_meaning', 'image_path', 'approved']
            for col in required_cols:
                if col not in self.df.columns:
                    if col == 'image_path':
                        self.df[col] = ''
                    elif col == 'approved':
                        self.df[col] = False
                    else:
                        raise ValueError(f"Required column '{col}' not found in CSV")
            
            logger.info(f"Loaded CSV with {len(self.df)} rows")
            
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise
    
    def save_csv(self):
        """Save current state to CSV"""
        try:
            self.df.to_csv(self.csv_path, index=False)
            logger.info("CSV saved successfully")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
    
    def get_current_word(self) -> Optional[Dict]:
        """Get current word data"""
        if self.current_index < len(self.df):
            return self.df.iloc[self.current_index].to_dict()
        return None
    
    def update_current_word(self, **kwargs):
        """Update current word with new data"""
        for key, value in kwargs.items():
            if key in self.df.columns:
                self.df.at[self.current_index, key] = value
        self.save_csv()
    
    def next_word(self) -> bool:
        """Move to next word, return True if successful"""
        self.current_index += 1
        return self.current_index < len(self.df)
    
    def get_progress(self) -> Dict:
        """Get current progress statistics"""
        total = len(self.df)
        processed = self.current_index
        approved = len(self.df[self.df['approved'] == True])
        
        return {
            'total': total,
            'processed': processed,
            'approved': approved,
            'remaining': total - processed
        }

class ImageApprovalGUI:
    """GUI for image approval workflow"""
    
    def __init__(self, master, state_manager: StateManager, image_fetcher: PexelsImageFetcher):
        self.master = master
        self.state_manager = state_manager
        self.image_fetcher = image_fetcher
        self.current_images = []
        self.current_image_index = 0
        self.media_dir = Path("media")
        self.media_dir.mkdir(exist_ok=True)
        
        self.setup_ui()
        self.load_next_word()
        
    def setup_ui(self):
        """Setup the GUI interface"""
        self.master.title("Chinese Vocabulary Image Approval")
        self.master.geometry("800x700")
        self.master.configure(bg='#f0f0f0')
        
        # Main frame
        main_frame = ttk.Frame(self.master, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="Loading...")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Word display frame
        word_frame = ttk.LabelFrame(main_frame, text="Current Word", padding="15")
        word_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.chinese_label = ttk.Label(
            word_frame, 
            text="", 
            font=("Arial Unicode MS", 48, "bold"),
            foreground="#2c3e50"
        )
        self.chinese_label.pack(pady=(0, 5))
        
        self.pinyin_label = ttk.Label(
            word_frame, 
            text="", 
            font=("Arial", 24),
            foreground="#7f8c8d"
        )
        self.pinyin_label.pack(pady=(0, 5))
        
        self.english_label = ttk.Label(
            word_frame, 
            text="", 
            font=("Arial", 16),
            foreground="#34495e"
        )
        self.english_label.pack()
        
        # Image frame
        image_frame = ttk.LabelFrame(main_frame, text="Image Preview", padding="15")
        image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.image_label = ttk.Label(image_frame, text="Loading images...")
        self.image_label.pack(expand=True)
        
        # Navigation frame
        nav_frame = ttk.Frame(image_frame)
        nav_frame.pack(pady=(10, 0))
        
        self.prev_img_btn = ttk.Button(
            nav_frame, 
            text="◀ Previous", 
            command=self.prev_image,
            state=tk.DISABLED
        )
        self.prev_img_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.image_counter_label = ttk.Label(nav_frame, text="")
        self.image_counter_label.pack(side=tk.LEFT, padx=10)
        
        self.next_img_btn = ttk.Button(
            nav_frame, 
            text="Next ▶", 
            command=self.next_image,
            state=tk.DISABLED
        )
        self.next_img_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left side buttons
        left_buttons = ttk.Frame(control_frame)
        left_buttons.pack(side=tk.LEFT)
        
        self.use_image_btn = ttk.Button(
            left_buttons, 
            text="✓ Use This Image", 
            command=self.use_current_image,
            state=tk.DISABLED
        )
        self.use_image_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.skip_word_btn = ttk.Button(
            left_buttons, 
            text="✗ Skip Word", 
            command=self.skip_word
        )
        self.skip_word_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Custom image buttons
        custom_buttons = ttk.Frame(control_frame)
        custom_buttons.pack(side=tk.LEFT, padx=(20, 0))
        
        self.custom_image_btn = ttk.Button(
            custom_buttons, 
            text="📁 Use Custom Image", 
            command=self.use_custom_image
        )
        self.custom_image_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.paste_image_btn = ttk.Button(
            custom_buttons, 
            text="📋 Paste Image", 
            command=self.paste_image_from_clipboard
        )
        self.paste_image_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_btn = ttk.Button(
            control_frame, 
            text="📦 Export Anki Deck", 
            command=self.export_deck
        )
        self.export_btn.pack(side=tk.RIGHT)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="green")
        self.status_label.pack(side=tk.LEFT)
        
    def update_progress(self):
        """Update progress display"""
        progress = self.state_manager.get_progress()
        self.progress_label.config(
            text=f"Progress: {progress['processed']}/{progress['total']} words processed, "
                 f"{progress['approved']} approved"
        )
        
        if progress['total'] > 0:
            self.progress_bar.config(value=(progress['processed'] / progress['total']) * 100)
        
    def load_next_word(self):
        """Load next word and fetch images"""
        word = self.state_manager.get_current_word()
        if not word:
            messagebox.showinfo("Complete", "All words have been processed!")
            self.export_btn.config(state=tk.NORMAL)
            return
        
        self.chinese_label.config(text=word['simplified'])
        self.pinyin_label.config(text=word['pinyin'])
        self.english_label.config(text=word['english_meaning'])
        
        self.update_progress()
        self.status_label.config(text="Fetching images...", foreground="orange")
        
        # Fetch images in separate thread
        threading.Thread(
            target=self.fetch_images, 
            args=(word['english_meaning'],),
            daemon=True
        ).start()
        
    def fetch_images(self, query: str):
        """Fetch images for current word"""
        self.current_images = self.image_fetcher.search_images(query)
        self.current_image_index = 0
        
        # Update UI in main thread
        self.master.after(0, self.update_image_display)
        
    def update_image_display(self):
        """Update image display"""
        if not self.current_images:
            self.image_label.config(text="No images found", image="")
            self.status_label.config(text="No images available", foreground="red")
            self.use_image_btn.config(state=tk.DISABLED)
            return
        
        # Load current image
        current_image = self.current_images[self.current_image_index]
        image_url = current_image['src']['medium']
        
        try:
            # Download and display image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Convert to PIL Image
            from io import BytesIO
            img = Image.open(BytesIO(response.content))
            
            # Resize to fit display
            img.thumbnail((400, 300), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Update display
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # Keep reference
            
            # Update navigation
            self.image_counter_label.config(
                text=f"{self.current_image_index + 1}/{len(self.current_images)}"
            )
            
            self.prev_img_btn.config(state=tk.NORMAL if self.current_image_index > 0 else tk.DISABLED)
            self.next_img_btn.config(state=tk.NORMAL if self.current_image_index < len(self.current_images) - 1 else tk.DISABLED)
            self.use_image_btn.config(state=tk.NORMAL)
            
            self.status_label.config(text="Ready", foreground="green")
            
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            self.image_label.config(text="Error loading image", image="")
            self.status_label.config(text="Error loading image", foreground="red")
    
    def prev_image(self):
        """Show previous image"""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.update_image_display()
    
    def next_image(self):
        """Show next image"""
        if self.current_image_index < len(self.current_images) - 1:
            self.current_image_index += 1
            self.update_image_display()
    
    def use_current_image(self):
        """Use current image for the word"""
        if not self.current_images:
            return
        
        word = self.state_manager.get_current_word()
        current_image = self.current_images[self.current_image_index]
        
        # Download image
        image_url = current_image['src']['medium']
        filename = f"{word['simplified']}_{self.state_manager.current_index}.jpg"
        filepath = self.media_dir / filename
        
        self.status_label.config(text="Downloading image...", foreground="orange")
        
        if self.image_fetcher.download_image(image_url, str(filepath)):
            # Update state
            self.state_manager.update_current_word(
                image_path=str(filepath),
                approved=True
            )
            
            self.status_label.config(text="Image saved", foreground="green")
            
            # Move to next word
            if self.state_manager.next_word():
                self.load_next_word()
            else:
                messagebox.showinfo("Complete", "All words have been processed!")
                self.export_btn.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Failed to download image", foreground="red")
    
    def skip_word(self):
        """Skip current word without image"""
        self.state_manager.update_current_word(approved=False)
        
        if self.state_manager.next_word():
            self.load_next_word()
        else:
            messagebox.showinfo("Complete", "All words have been processed!")
            self.export_btn.config(state=tk.NORMAL)
    
    def use_custom_image(self):
        """Allow user to select a custom image file"""
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Validate image
            with Image.open(file_path) as img:
                # Check if image is valid
                img.verify()
            
            # Process the custom image
            self.process_custom_image(file_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid image file: {e}")
            logger.error(f"Error validating custom image: {e}")
    
    def paste_image_from_clipboard(self):
        """Paste image from clipboard"""
        try:
            # Try to get image from clipboard
            clipboard_image = ImageGrab.grabclipboard()
            
            if clipboard_image is None:
                messagebox.showwarning("No Image", "No image found in clipboard.\n\nTip: Copy an image (Ctrl+C) before pasting.")
                return
            
            if not isinstance(clipboard_image, Image.Image):
                messagebox.showwarning("Invalid Content", "Clipboard content is not an image.\n\nPlease copy an image first.")
                return
            
            # Save clipboard image to temporary file
            word = self.state_manager.get_current_word()
            temp_filename = f"clipboard_{word['simplified']}_{self.state_manager.current_index}.png"
            temp_filepath = self.media_dir / temp_filename
            
            # Save with reasonable quality
            clipboard_image.save(temp_filepath, format='PNG', optimize=True)
            
            # Process the pasted image
            self.process_custom_image(str(temp_filepath), is_clipboard=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste image from clipboard: {e}")
            logger.error(f"Error pasting image from clipboard: {e}")
    
    def process_custom_image(self, image_path: str, is_clipboard: bool = False):
        """Process a custom image (from file or clipboard)"""
        try:
            word = self.state_manager.get_current_word()
            
            # Create final filename
            final_filename = f"{word['simplified']}_{self.state_manager.current_index}.jpg"
            final_filepath = self.media_dir / final_filename
            
            # Load and process image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (max 800x600 for efficiency)
                max_size = (800, 600)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save processed image
                img.save(final_filepath, format='JPEG', quality=85, optimize=True)
            
            # Update preview
            self.display_custom_image(final_filepath)
            
            # Update state
            self.state_manager.update_current_word(
                image_path=str(final_filepath),
                approved=True
            )
            
            # Show success message
            source_text = "clipboard" if is_clipboard else "file"
            self.status_label.config(text=f"Custom image from {source_text} saved", foreground="green")
            
            # Clean up temporary clipboard file
            if is_clipboard and image_path != str(final_filepath):
                try:
                    os.remove(image_path)
                except:
                    pass
            
            logger.info(f"Custom image processed: {final_filepath}")
            
            # Ask if user wants to continue or approve this image
            response = messagebox.askyesno(
                "Custom Image Added", 
                f"Custom image has been saved for '{word['simplified']}'.\n\n"
                "Do you want to continue to the next word?\n\n"
                "Click 'Yes' to continue, 'No' to stay on this word."
            )
            
            if response:
                # Move to next word
                if self.state_manager.next_word():
                    self.load_next_word()
                else:
                    messagebox.showinfo("Complete", "All words have been processed!")
                    self.export_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process custom image: {e}")
            logger.error(f"Error processing custom image: {e}")
    
    def display_custom_image(self, image_path: str):
        """Display the custom image in the preview"""
        try:
            # Load and display image
            img = Image.open(image_path)
            img.thumbnail((400, 300), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # Keep reference
            
            # Update navigation to show custom image
            self.image_counter_label.config(text="Custom Image")
            self.prev_img_btn.config(state=tk.DISABLED)
            self.next_img_btn.config(state=tk.DISABLED)
            self.use_image_btn.config(state=tk.DISABLED)  # Already processed
            
        except Exception as e:
            logger.error(f"Error displaying custom image: {e}")
    
    def export_deck(self):
        """Export approved words to Anki deck"""
        try:
            exporter = AnkiDeckExporter(self.state_manager.df)
            filename = exporter.export_deck()
            messagebox.showinfo("Success", f"Anki deck exported as: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export deck: {e}")

class AnkiDeckExporter:
    """Module for exporting Anki decks"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def export_deck(self) -> str:
        """Export approved words to .apkg file"""
        # Filter approved words
        approved_words = self.df[self.df['approved'] == True]
        
        if len(approved_words) == 0:
            raise ValueError("No approved words to export")
        
        # Create Anki model
        model = genanki.Model(
            random.randrange(1 << 30, 1 << 31),
            'Chinese Vocabulary with Images',
            fields=[
                {'name': 'Chinese'},
                {'name': 'Pinyin'},
                {'name': 'Image'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '''
                    <div style="font-family: Arial Unicode MS, serif; text-align: center;">
                        <div style="font-size: 48px; font-weight: bold; color: #2c3e50; margin: 20px 0;">
                            {{Chinese}}
                        </div>
                        <div style="font-size: 24px; color: #7f8c8d; margin: 10px 0;">
                            {{Pinyin}}
                        </div>
                    </div>
                    ''',
                    'afmt': '''
                    <div style="font-family: Arial Unicode MS, serif; text-align: center;">
                        <div style="font-size: 48px; font-weight: bold; color: #2c3e50; margin: 20px 0;">
                            {{Chinese}}
                        </div>
                        <div style="font-size: 24px; color: #7f8c8d; margin: 10px 0;">
                            {{Pinyin}}
                        </div>
                        <div style="margin: 20px 0;">
                            {{Image}}
                        </div>
                    </div>
                    ''',
                },
            ],
            css='''
            .card {
                font-family: Arial Unicode MS, serif;
                font-size: 20px;
                text-align: center;
                color: #2c3e50;
                background-color: #ecf0f1;
                padding: 20px;
            }
            img {
                max-width: 400px;
                max-height: 300px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            '''
        )
        
        # Create deck
        deck = genanki.Deck(
            random.randrange(1 << 30, 1 << 31),
            'Chinese Vocabulary'
        )
        
        # Add notes
        media_files = []
        for _, word in approved_words.iterrows():
            # Prepare image
            image_html = ""
            if word['image_path'] and os.path.exists(word['image_path']):
                image_filename = os.path.basename(word['image_path'])
                media_files.append(word['image_path'])
                image_html = f'<img src="{image_filename}" alt="Image for {word["simplified"]}">'
            
            # Create note
            note = genanki.Note(
                model=model,
                fields=[
                    word['simplified'],
                    word['pinyin'],
                    image_html
                ]
            )
            deck.add_note(note)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chinese_vocabulary_{timestamp}.apkg"
        
        # Export package
        package = genanki.Package(deck)
        package.media_files = media_files
        package.write_to_file(filename)
        
        logger.info(f"Exported {len(approved_words)} words to {filename}")
        return filename

class WorkflowController:
    """Main controller for the automation pipeline"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide initially
        
    def run(self):
        """Run the complete workflow"""
        try:
            # Get Pexels API key
            api_key = "EeP7WehuGtuiIdvrz4125UfkRqOhW8PQt7iL9drO5494JNbW06ShbRYd"
            if not api_key:
                return
            
            # Get CSV file
            csv_path = self.get_csv_file()
            if not csv_path:
                return
            
            # Initialize components
            state_manager = StateManager(csv_path)
            image_fetcher = PexelsImageFetcher(api_key)
            
            # Show main window
            self.root.deiconify()
            
            # Start GUI
            gui = ImageApprovalGUI(self.root, state_manager, image_fetcher)
            
            # Run main loop
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            messagebox.showerror("Error", f"Workflow failed: {e}")
    
    # def get_pexels_api_key(self) -> Optional[str]:
    #     """Get Pexels API key from user"""
    #     api_key = simpledialog.askstring(
    #         "API Key Required",
    #         "Please enter your Pexels API key:",
    #         show="*"
    #     )
        
        if not api_key:
            messagebox.showwarning("Warning", "API key is required to proceed.")
            return None
        
        return api_key
    
    def get_csv_file(self) -> Optional[str]:
        """Get CSV file path from user"""
        csv_path = filedialog.askopenfilename(
            title="Select Chinese Vocabulary CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not csv_path:
            messagebox.showwarning("Warning", "CSV file is required to proceed.")
            return None
        
        return csv_path

def main():
    """Main entry point"""
    try:
        controller = WorkflowController()
        controller.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application failed to start: {e}")

if __name__ == "__main__":
    main()