# pdf_to_csv.py
import pandas as pd
import tabula
import re

def extract_pdf_to_csv(pdf_path, output_csv="chinese_words.csv"):
    """Extract Chinese word data from PDF to CSV"""
    
    try:
        # Try to extract tables from all pages
        print("Extracting tables from PDF...")
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        
        all_data = []
        
        for table in tables:
            # Clean and process each table
            if len(table.columns) >= 4:  # Ensure we have enough columns
                # Rename columns based on the PDF structure
                table.columns = ['Traditional', 'Simplified', 'Pinyin', 'Meaning'][:len(table.columns)]
                
                # Clean the data
                for _, row in table.iterrows():
                    if pd.notna(row['Simplified']) and pd.notna(row['Pinyin']):
                        # Clean pinyin - remove file references and extra text
                        pinyin = str(row['Pinyin']).split(':')[0].strip()
                        pinyin = re.sub(r'\([^)]*\)', '', pinyin).strip()
                        
                        # Clean meaning - get first meaning if multiple
                        meaning = str(row['Meaning']).split(',')[0].strip()
                        
                        all_data.append({
                            'simplified': str(row['Simplified']).strip(),
                            'pinyin': pinyin,
                            'meaning': meaning,
                            'image_path': '',  # Will be filled later
                            'audio_path': '',  # Will be filled later
                            'approved': False  # For tracking image approval
                        })
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(all_data)
        
        # Remove duplicates based on simplified characters
        df = df.drop_duplicates(subset=['simplified'], keep='first')
        
        # Filter out invalid entries
        df = df[df['simplified'].str.len() > 0]
        df = df[df['pinyin'].str.len() > 0]
        
        # Save to CSV
        df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"Extracted {len(df)} words to {output_csv}")
        
        return df
        
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        # Fallback: manual extraction if tabula fails
        print("Trying manual extraction...")
        return manual_extraction_fallback(pdf_path, output_csv)

def manual_extraction_fallback(pdf_path, output_csv):
    """Fallback method for manual data entry if PDF extraction fails"""
    
    # Sample data from the PDF for demonstration
    sample_data = [
        {'simplified': '一', 'pinyin': 'yī', 'meaning': 'one', 'image_path': '', 'audio_path': '', 'approved': False},
        {'simplified': '在', 'pinyin': 'zài', 'meaning': 'in, at, on', 'image_path': '', 'audio_path': '', 'approved': False},
        {'simplified': '有', 'pinyin': 'yǒu', 'meaning': 'have, possess', 'image_path': '', 'audio_path': '', 'approved': False},
        {'simplified': '个', 'pinyin': 'gè', 'meaning': 'piece, item', 'image_path': '', 'audio_path': '', 'approved': False},
        {'simplified': '我', 'pinyin': 'wǒ', 'meaning': 'I, me', 'image_path': '', 'audio_path': '', 'approved': False},
        {'simplified': '苹果', 'pinyin': 'píngguǒ', 'meaning': 'apple', 'image_path': '', 'audio_path': '', 'approved': False},
        {'simplified': '香蕉', 'pinyin': 'xiāngjiāo', 'meaning': 'banana', 'image_path': '', 'audio_path': '', 'approved': False},
        {'simplified': '猫', 'pinyin': 'māo', 'meaning': 'cat', 'image_path': '', 'audio_path': '', 'approved': False},
        {'simplified': '狗', 'pinyin': 'gǒu', 'meaning': 'dog', 'image_path': '', 'audio_path': '', 'approved': False},
        {'simplified': '房子', 'pinyin': 'fángzi', 'meaning': 'house', 'image_path': '', 'audio_path': '', 'approved': False}
    ]
    
    df = pd.DataFrame(sample_data)
    df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"Created sample CSV with {len(df)} words")
    return df

if __name__ == "__main__":
    pdf_path = "/Users/devyn-tplink/Downloads/Appendix_Mandarin_Frequency_lists_1-1000.pdf"
    extract_pdf_to_csv(pdf_path)
