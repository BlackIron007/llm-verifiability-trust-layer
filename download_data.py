import nltk
import os
import shutil

# This script should be run from the root of the project.

script_dir = os.path.dirname(os.path.abspath(__file__))

TARGET_DIR = os.path.join(script_dir, 'app', 'nltk_data')

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)
    print(f"Created directory: {TARGET_DIR}")

tokenizers_dir = os.path.join(TARGET_DIR, 'tokenizers')
if os.path.exists(tokenizers_dir):
    print("\nClearing old tokenizer data to ensure a clean download...")
    shutil.rmtree(tokenizers_dir)

print(f"\nDownloading 'punkt' and 'punkt_tab' tokenizers to: {TARGET_DIR}")
nltk.download('punkt', download_dir=TARGET_DIR)
nltk.download('punkt_tab', download_dir=TARGET_DIR)
print("\nDownload complete. It is recommended to commit the 'app/nltk_data' directory to version control.")