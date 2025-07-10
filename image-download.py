# image_downloader.py - UPDATED WITH PEXELS API
import pandas as pd
import requests
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import urllib.request
from io import BytesIO
import time

class ImageApprovalGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chinese Word Image Approval - Pexels API")
        self.root.geometry("700x650")
        self.user_choice = None
        self.current_word = None
        self.setup_ui()
    
    def setup_ui(self):
        # Word info
        self.word_label = tk.Label(self.root, font=("Arial", 24, "bold"))
        self.word_label.pack(pady=10)
        
        self.pinyin_label = tk.Label(self.root, font=("Arial", 18))
        self.pinyin_label.pack(pady=5)
        
        self.meaning_label = tk.Label(self.root, font=("Arial", 16))
        self.meaning_label.pack(pady=5)
        
        # Image info
        self.image_info_label = tk.Label(self.root, font=("Arial", 12), fg="gray")
        self.image_info_label.pack(pady=5)
        
        # Image display area
        self.image_label = tk.Label(self.root)
        self.image_label.pack(pady=20)
        
        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.yes_button = tk.Button(button_frame, text="✓ Use This Image", 
                                   command=self.choose_yes, bg="#4CAF50", fg="white",
                                   font=("Arial", 12, "bold"), padx=20)
        self.yes_button.pack(side=tk.LEFT, padx=10)
        
        self.next_button = tk.Button(button_frame, text="→ Next Image", 
                                    command=self.choose_next, bg="#2196F3", fg="white",
                                    font=("Arial", 12, "bold"), padx=20)
        self.next_button.pack(side=tk.LEFT, padx=10)
        
        self.skip_button = tk.Button(button_frame, text="✗ Skip Word", 
                                    command=self.choose_skip, bg="#f44336", fg="white",
                                    font=("Arial", 12, "bold"), padx=20)
        self.skip_button.pack(side=tk.LEFT, padx=10)
    
    def show_image(self, image_url, word_data, photographer_info=""):
        """Display image and get user choice"""
        try:
            self.current_word = word_data
            
            # Update word information
            self.word_label.configure(text=word_data['simplified'])
            self.pinyin_label.configure(text=word_data['pinyin'])
            self.meaning_label.configure(text=word_data['meaning'])
            self.image_info_label.configure(text=photographer_info)
            
            # Download and display image
            response = requests.get(image_url, timeout=10)
            img = Image.open(BytesIO(response.content))
            
            # Resize image to fit window
            img.thumbnail((500, 400), Image.Resampling.LANCZOS)
            
            # Convert to tkinter format
            photo = ImageTk.PhotoImage(img)
            
            # Update display
            self.image_label.configure(image=photo)
            self.image_label.image = photo  # Keep a reference
            
            # Reset choice and show window
            self.user_choice = None
            self.root.deiconify()  # Show window
            
            # Wait for user choice
            self.root.wait_variable(self.user_choice)
            
            # Hide window
            self.root.withdraw()
            
            return self.user_choice
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            return 'skip'
    
    def choose_yes(self):
        self.user_choice = 'yes'
        self.root.quit()
    
    def choose_next(self):
        self.user_choice = 'next'
        self.root.quit()
    
    def choose_skip(self):
        self.user_choice = 'skip'
        self.root.quit()

class PexelsImageSearch:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/v1/search"
        self.headers = {
            "Authorization": api_key
        }
    
    def search_images(self, query, per_page=5, page=1):
        """Search for images using Pexels API"""
        try:
            params = {
                "query": query,
                "per_page": per_page,
                "page": page,
                "orientation": "square"  # Good for flashcards
            }
            
            response = requests.get(self.base_url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                images = []
                
                for photo in data.get('photos', []):
                    images.append({
                        'url': photo['src']['medium'],  # Good quality for cards
                        'photographer': photo['photographer'],
                        'photographer_url': photo['photographer_url'],
                        'alt': photo.get('alt', ''),
                        'id': photo['id']
                    })
                
                return images
            else:
                print(f"Pexels API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error searching Pexels: {e}")
            return []

def download_and_approve_images_pexels(csv_path="chinese_words.csv", pexels_api_key=None):
    """Download images with user approval using Pexels API"""
    
    if not pexels_api_key:
        print("❌ Error: Pexels API key is required!")
        print("Get your free API key at: https://www.pexels.com/api/")
        return
    
    # Create media directory
    os.makedirs("media", exist_ok=True)
    
    # Load CSV
    df = pd.read_csv(csv_path)
    
    # Initialize Pexels API and GUI
    pexels_api = PexelsImageSearch(pexels_api_key)
    gui = ImageApprovalGUI()
    gui.root.withdraw()  # Hide initially
    
    for index, row in df.iterrows():
        if row['approved']:  # Skip already approved words
            continue
            
        print(f"\n🔍 Processing: {row['simplified']} ({row['pinyin']})")
        
        # Search for images using English meaning
        search_query = row['meaning'].split(',')[0].strip()  # Use first meaning
        print(f"   Searching Pexels for: '{search_query}'")
        
        images = pexels_api.search_images(search_query, per_page=10)
        
        if not images:
            print(f"   ❌ No images found for '{search_query}'")
            df.at[index, 'approved'] = True  # Mark as processed
            continue
        
        image_saved = False
        for attempt, image_data in enumerate(images):
            try:
                photographer_info = f"📸 Photo by {image_data['photographer']} on Pexels"
                
                choice = gui.show_image(image_data['url'], row, photographer_info)
                
                if choice == 'yes':
                    # Save the image
                    response = requests.get(image_data['url'], timeout=15)
                    image_filename = f"{row['simplified']}_{index}.jpg"
                    image_path = os.path.join("media", image_filename)
                    
                    with open(image_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Update DataFrame
                    df.at[index, 'image_path'] = image_filename
                    df.at[index, 'approved'] = True
                    image_saved = True
                    print(f"   ✅ Saved image for {row['simplified']}")
                    break
                    
                elif choice == 'skip':
                    df.at[index, 'approved'] = True  # Mark as processed but no image
                    break
                # If 'next', continue to next image
                
            except Exception as e:
                print(f"   ⚠️ Error with image {attempt + 1}: {e}")
                continue
        
        if not image_saved and not df.at[index, 'approved']:
            df.at[index, 'approved'] = True  # Mark as processed
        
        # Save progress after each word
        df.to_csv(csv_path, index=False)
        
        # Be respectful to the API
        time.sleep(1)
    
    gui.root.destroy()
    print(f"\n🎉 Image approval complete! Updated {csv_path}")
    return df

if __name__ == "__main__":
    # Replace with your actual Pexels API key
    PEXELS_API_KEY = "EeP7WehuGtuiIdvrz4125UfkRqOhW8PQt7iL9drO5494JNbW06ShbRYd"
    
    download_and_approve_images_pexels(pexels_api_key=PEXELS_API_KEY)
