import pandas as pd
import io

# --- Data Loading ---
# To read your actual Excel file, uncomment the following line
# and replace 'your_file_name.xlsx' with your actual file path.

# You may need to install the 'openpyxl' library first:
# pip install openpyxl
df = pd.read_excel('/Users/devyn/Downloads/1000-most-common-chinese-words (1).xlsx')


# --- Data Cleaning ---

# 1. Identify columns that need to be forward-filled
# These are the columns that were originally part of the merged cells.
# Note: I'm using the column names from your original file.
columns_to_fill = ['序号\nNo.', '词\nWord', '拼音\nPinyin', '词类\nParts of Speech']

# 2. Forward-fill the missing values in the specified columns
# The .ffill() method propagates the last valid observation forward.
df[columns_to_fill] = df[columns_to_fill].ffill()

# 3. Clean up the data types
# The '序号\nNo.' column was read as a float because of the forward-filling,
# so we convert it back to an integer.
df['序号\nNo.'] = df['序号\nNo.'].astype(int)

# 4. Remove any rows that might be entirely empty or irrelevant
# A good way to do this is to drop rows where the 'Meaning' or 'Example' is missing.
df.dropna(subset=['词译文\nMeaning of the Word', '例句\nExample'], inplace=True)

# 5. Reset the DataFrame index for a clean look
df.reset_index(drop=True, inplace=True)

# --- Display Results ---

# Print the cleaned DataFrame to the console
print("--- Cleaned Chinese Vocabulary List ---")
print(df.to_string())

# To save the cleaned data to a new file, you would use one of the following:
df.to_csv('cleaned_chinese_vocab.csv', index=False)
df.to_excel('cleaned_chinese_vocab.xlsx', index=False)
print("\nSuccessfully saved the cleaned data.")
