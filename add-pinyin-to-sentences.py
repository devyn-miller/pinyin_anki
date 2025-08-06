import pandas as pd
import re
import sys
import os
import csv

# Install pypinyin if not available
try:
    from pypinyin import pinyin, lazy_pinyin, Style
except ImportError:
    print("pypinyin not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypinyin"])
    from pypinyin import pinyin, lazy_pinyin, Style

def generate_pinyin(text):
    """Generate pinyin for Chinese text"""
    if not text.strip():
        return ""
    try:
        # Generate pinyin with tone marks
        pinyin_list = pinyin(text, style=Style.TONE)
        return ' '.join([item[0] for item in pinyin_list])
    except Exception as e:
        print(f"Error generating pinyin for '{text}': {e}")
        return ""

def process_csv(input_file, output_file):
    """Process the CSV file and add pinyin for sentences"""
    print(f"Reading CSV file: {input_file}")
    
    # Read the CSV file
    rows = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    if not rows:
        print("Error: CSV file is empty")
        return
    
    print(f"Read {len(rows)} rows from CSV file")
    
    # Create a new list for output rows
    output_rows = []
    
    # Process each row
    for i, row in enumerate(rows):
        if not row:  # Skip empty rows
            output_rows.append(row)
            continue
            
        try:
            # Check if this is a definition card or a sentence card
            # Definition cards have English in first column, sentence cards have Chinese
            is_definition_card = not any(u'\u4e00' <= c <= u'\u9fff' for c in row[0])
            
            if is_definition_card:
                # This is a definition card (English, Chinese, Pinyin, POS, Example, ...)
                # For definition cards, we need to add pinyin to the example sentence if present
                new_row = row.copy()
                
                # Check if there's an example sentence (usually in column 4)
                if len(row) > 4 and row[4] and any(u'\u4e00' <= c <= u'\u9fff' for c in row[4]):
                    example_sentence = row[4]
                    example_pinyin = generate_pinyin(example_sentence)
                    
                    # Add the pinyin after the example sentence
                    if len(new_row) > 5:
                        new_row.append(example_pinyin)
                    else:
                        # Ensure the row is long enough
                        while len(new_row) < 5:
                            new_row.append("")
                        new_row.append(example_pinyin)
                
                output_rows.append(new_row)
            else:
                # This is a sentence card (Chinese, English, Chinese word, Pinyin, POS, ...)
                # Get the Chinese sentence and generate pinyin for it
                chinese_sentence = row[0]
                sentence_pinyin = generate_pinyin(chinese_sentence)
                
                # Create a new row with the same content
                new_row = row.copy()
                
                # Add pinyin after the Chinese sentence translation
                if len(new_row) > 5:
                    new_row.append(sentence_pinyin)
                else:
                    # Ensure the row is long enough
                    while len(new_row) < 5:
                        new_row.append("")
                    new_row.append(sentence_pinyin)
                
                output_rows.append(new_row)
            
            # Print progress
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1} rows...")
                
        except Exception as e:
            print(f"Error processing row {i+1}: {e}")
            output_rows.append(row)  # Keep the original row in case of error
    
    # Save to new CSV file
    print(f"Saving to: {output_file}")
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(output_rows)
        print("Done!")
    except Exception as e:
        print(f"Error writing output file: {e}")

if __name__ == "__main__":
    input_file = "chiense two types - Chinese Vocabulary.csv"
    output_file = "chinese_vocab_with_pinyin.csv"
    
    process_csv(input_file, output_file)
