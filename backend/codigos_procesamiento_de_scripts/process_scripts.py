import os
import re
from bs4 import BeautifulSoup

def clean_script(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove HTML tags if any
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text()
    
    # Remove special characters and irrelevant metadata
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\[.*?\]', '', text)  # Remove text within brackets
    
    # Save cleaned text
    with open(file_path.replace('.txt', '_cleaned.txt'), 'w', encoding='utf-8') as file:
        file.write(text)

if __name__ == "__main__":
    scripts_dir = 'scripts'
    for filename in os.listdir(scripts_dir):
        if filename.endswith('.txt'):
            clean_script(os.path.join(scripts_dir, filename))
    print("Script processing completed.")
