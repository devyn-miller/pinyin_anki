#!/usr/bin/env python3
"""
Excel to CSV Converter for Chinese Vocabulary
Converts existing Excel files to the format required by the Anki automation pipeline
"""

import pandas as pd
import re
import sys
import os
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk

class ExcelToCsvConverter:
    """Converts Excel vocabulary files to CSV format for Anki pipeline"""
    
    def __init__(self):
        self.df = None
        self.output_path = None
        
    def load_excel_file(self, file_path: str) -> bool:
        """Load Excel file and validate structure"""
        try:
            # Try reading the Excel file
            self.df = pd.read_excel(file_path)
            
            print(f"Loaded Excel file with {len(self.df)} rows and {len(self.df.columns)} columns")
            print(f"Columns found: {list(self.df.columns)}")
            
            # Display first few rows for verification
            print("\nFirst 5 rows:")
            print(self.df.head())
            
            return True
            
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            return False
    
    def clean_meaning_text(self, text: str) -> str:
        """Clean and format the meaning text"""
        if pd.isna(text):
            return ""
        
        # Convert to string
        text = str(text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove "det.:", "Audio:", and similar prefixes
        text = re.sub(r'^(det\.|Audio|adj\.|adv\.|n\.|v\.|prep\.):\s*', '', text, flags=re.IGNORECASE)
        
        # Remove asterisks and other markdown
        text = re.sub(r'\*+', '', text)
        
        # Clean up multiple definitions - take the first main definition
        if ',' in text:
            # Split by comma and take the first substantial definition
            parts = text.split(',')
            main_def = parts[0].strip()
            if len(main_def) > 2:  # Ensure it's not just "I" or "me"
                text = main_def
        
        return text.strip()
    
    def convert_to_pipeline_format(self) -> bool:
        """Convert the loaded Excel data to the required CSV format"""
        if self.df is None:
            print("No data loaded. Please load an Excel file first.")
            return False
        
        try:
            # Create output dataframe with required columns
            output_df = pd.DataFrame()
            
            # Map columns based on common patterns
            column_mapping = self.detect_column_mapping()
            
            if not column_mapping:
                print("Could not detect required columns in the Excel file.")
                return False
            
            # Extract data using detected mapping
            output_df['simplified'] = self.df[column_mapping['simplified']]
            output_df['pinyin'] = self.df[column_mapping['pinyin']]
            output_df['english_meaning'] = self.df[column_mapping['meaning']].apply(self.clean_meaning_text)
            
            # Add required columns for pipeline
            output_df['image_path'] = ''
            output_df['approved'] = False
            
            # Remove empty rows
            output_df = output_df.dropna(subset=['simplified', 'pinyin'])
            output_df = output_df[output_df['simplified'].str.strip() != '']
            
            # Remove duplicates based on simplified character
            output_df = output_df.drop_duplicates(subset=['simplified'], keep='first')
            
            self.df = output_df
            
            print(f"\nConverted to pipeline format:")
            print(f"Total words: {len(output_df)}")
            print("\nSample converted data:")
            print(output_df.head())
            
            return True
            
        except Exception as e:
            print(f"Error converting data: {e}")
            return False
    
    def detect_column_mapping(self) -> dict:
        """Detect which columns contain the required data"""
        columns = [col.lower() for col in self.df.columns]
        mapping = {}
        
        # Detect simplified column
        simplified_candidates = ['simplified', 'simple', 'simp', 'character', 'char']
        for candidate in simplified_candidates:
            for i, col in enumerate(columns):
                if candidate in col:
                    mapping['simplified'] = self.df.columns[i]
                    break
            if 'simplified' in mapping:
                break
        
        # If no simplified column found, try to use traditional or first column
        if 'simplified' not in mapping:
            traditional_candidates = ['traditional', 'trad', 'char']
            for candidate in traditional_candidates:
                for i, col in enumerate(columns):
                    if candidate in col:
                        mapping['simplified'] = self.df.columns[i]
                        break
                if 'simplified' in mapping:
                    break
        
        # If still not found, use first column
        if 'simplified' not in mapping and len(self.df.columns) > 0:
            mapping['simplified'] = self.df.columns[0]
        
        # Detect pinyin column
        pinyin_candidates = ['pinyin', 'pin', 'pronunciation', 'roman']
        for candidate in pinyin_candidates:
            for i, col in enumerate(columns):
                if candidate in col:
                    mapping['pinyin'] = self.df.columns[i]
                    break
            if 'pinyin' in mapping:
                break
        
        # Detect meaning column
        meaning_candidates = ['meaning', 'english', 'definition', 'translation', 'def']
        for candidate in meaning_candidates:
            for i, col in enumerate(columns):
                if candidate in col:
                    mapping['meaning'] = self.df.columns[i]
                    break
            if 'meaning' in mapping:
                break
        
        # Print detected mapping
        print(f"\nDetected column mapping:")
        for key, value in mapping.items():
            print(f"  {key}: {value}")
        
        # Validate mapping
        required_keys = ['simplified', 'pinyin', 'meaning']
        if not all(key in mapping for key in required_keys):
            print(f"\nError: Could not detect all required columns.")
            print(f"Required: {required_keys}")
            print(f"Found: {list(mapping.keys())}")
            return None
        
        return mapping
    
    def save_csv(self, output_path: str) -> bool:
        """Save the converted data to CSV"""
        try:
            self.df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"\nCSV saved successfully: {output_path}")
            return True
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False
    
    def interactive_convert(self):
        """Interactive conversion with file dialogs"""
        # Hide the root window
        root = tk.Tk()
        root.withdraw()
        
        # Get input file
        input_file = filedialog.askopenfilename(
            title="Select Excel file to convert",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        
        if not input_file:
            print("No file selected. Exiting.")
            return
        
        # Load and convert
        if not self.load_excel_file(input_file):
            messagebox.showerror("Error", "Failed to load Excel file")
            return
        
        if not self.convert_to_pipeline_format():
            messagebox.showerror("Error", "Failed to convert data")
            return
        
        # Get output file
        output_file = filedialog.asksaveasfilename(
            title="Save converted CSV as",
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if not output_file:
            print("No output file selected. Exiting.")
            return
        
        # Save
        if self.save_csv(output_file):
            messagebox.showinfo("Success", f"File converted successfully!\n\nOutput: {output_file}")
        else:
            messagebox.showerror("Error", "Failed to save CSV file")

def main():
    """Main function with command line interface"""
    converter = ExcelToCsvConverter()
    
    # Check if file path provided as argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        
        # Load file
        if not converter.load_excel_file(input_file):
            return
        
        # Convert
        if not converter.convert_to_pipeline_format():
            return
        
        # Generate output filename
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_converted.csv"
        
        # Save
        if converter.save_csv(str(output_file)):
            print(f"\n✅ Conversion complete!")
            print(f"📁 Output file: {output_file}")
            print(f"📊 Total words: {len(converter.df)}")
        
    else:
        # Interactive mode
        print("🔄 Starting interactive conversion...")
        converter.interactive_convert()

if __name__ == "__main__":
    main()