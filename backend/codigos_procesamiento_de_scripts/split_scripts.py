import os
from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_script(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(text)
    
    # Save chunks
    base = file_path.replace('_cleaned.txt', '')
    for i, chunk in enumerate(chunks):
        with open(f"{base}_chunk_{i}.txt", 'w', encoding='utf-8') as f:
            f.write(chunk)

if __name__ == "__main__":
    scripts_dir = 'scripts'
    for filename in os.listdir(scripts_dir):
        if filename.endswith('_cleaned.txt'):
            split_script(os.path.join(scripts_dir, filename))
    print("Script splitting completed.")
