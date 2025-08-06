import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageGrab
import os
import csv
import genanki
import uuid
import webbrowser

# -------- CONFIG --------
DECK_NAME = "Chinese School Vocab"
DECK_ID = int(uuid.uuid4()) >> 96
MODEL_ID = int(uuid.uuid4()) >> 96
IMAGE_DIR = "anki_media"
CSV_FILE = "anki_vocab.csv"
APKG_FILE = "chinese_vocab.apkg"
SOURCE_CSV = "your_source_vocab.csv"  # <--- Change to your actual file name

# -------- INIT --------
os.makedirs(IMAGE_DIR, exist_ok=True)

model = genanki.Model(
    MODEL_ID,
    'Image Vocab Model',
    fields=[
        {"name": "Characters"},
        {"name": "English"},
        {"name": "Pinyin"},
        {"name": "Image"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "<div style='font-size: 30px;'>{{Characters}}</div><br>{{Image}}",
            "afmt": "{{FrontSide}}<hr id='answer'><div style='font-size: 20px;'>{{English}}<br><i>{{Pinyin}}</i></div>",
        }
    ],
)

deck = genanki.Deck(DECK_ID, DECK_NAME)
media_files = []

# -------- LOAD FROM CSV --------
vocab = []
with open(SOURCE_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        english = row["CHINESE VOCABULARY"].strip()
        characters = row["CHARACTERS"].strip()
        pinyin = row["PINYIN"].strip()
        vocab.append((characters, english, pinyin))

# -------- OUTPUT CSV --------
with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Characters", "English", "Pinyin", "Image"])


# -------- FUNCTIONS --------
def sanitize_filename(word):
    return word.lower().replace(" ", "_") + ".jpg"

def save_image_and_add_card(img, characters, english, pinyin):
    filename = sanitize_filename(english)
    filepath = os.path.join(IMAGE_DIR, filename)
    img.save(filepath)
    media_files.append(filepath)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([characters, english, pinyin, f'<img src="{filename}">'])

    note = genanki.Note(
        model=model,
        fields=[characters, english, pinyin, f'<img src="{filename}">']
    )
    deck.add_note(note)

def paste_image():
    try:
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            ch, en, py = vocab[current_index]
            save_image_and_add_card(img, ch, en, py)
            next_word()
        else:
            print("No image in clipboard.")
    except Exception as e:
        print(f"Paste failed: {e}")

def upload_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp")])
    if file_path:
        img = Image.open(file_path)
        ch, en, py = vocab[current_index]
        save_image_and_add_card(img, ch, en, py)
        next_word()

def skip_word():
    next_word()

def open_image_search(query):
    url = f"https://www.google.com/search?tbm=isch&q={query} photo"
    webbrowser.open(url)

def next_word():
    global current_index
    current_index += 1
    if current_index >= len(vocab):
        finalize_and_exit()
    else:
        ch, en, _ = vocab[current_index]
        word_label.config(text=f"{ch} ({en})")
        canvas.delete("all")
        open_image_search(en)

def finalize_and_exit():
    genanki.Package(deck, media_files).write_to_file(APKG_FILE)
    print(f"\n✅ Anki deck saved: {APKG_FILE}")
    root.quit()


# -------- GUI --------
current_index = -1
root = tk.Tk()
root.title("Chinese Anki Image Builder")

word_label = tk.Label(root, text="", font=("Helvetica", 20))
word_label.pack(pady=10)

canvas = tk.Canvas(root, width=300, height=300, bg="white")
canvas.pack(pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack()

paste_btn = tk.Button(btn_frame, text="Paste Image (Ctrl+V)", command=paste_image)
paste_btn.grid(row=0, column=0, padx=10)

upload_btn = tk.Button(btn_frame, text="Upload Image", command=upload_image)
upload_btn.grid(row=0, column=1, padx=10)

skip_btn = tk.Button(btn_frame, text="Skip Word", command=skip_word)
skip_btn.grid(row=0, column=2, padx=10)

next_word()
root.mainloop()