import os
import json
import time
from datetime import datetime
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# Configuration
API_URL = "http://localhost:11434/api/embeddings"  # Ollama's local API endpoint
MODEL = "nomic-embed-text:v1.5"  # Updated model name
LOG_FILE = "embedding_generation_log.txt"
MAX_RETRIES = 3
MAX_WORKERS = 10  # Number of concurrent threads

def log_message(message):
    """Logs a message with a timestamp to both the console and a log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as log_file:
        log_file.write(log_entry + "\n")

def generate_embedding(text, filename):
    """Generates an embedding for the given text using the local Ollama API."""
    payload = {
        "model": MODEL,
        "prompt": text
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log_message(f"Attempt {attempt} - Sending request for '{filename}' (Payload length: {len(text)} characters)")
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=30)
            
            if response.status_code == 200:
                response_json = response.json()
                embedding = response_json.get("embedding", [])
                if embedding:
                    log_message(f"Successfully received embedding for '{filename}' on attempt {attempt}")
                    return embedding  # Return the single embedding list
                else:
                    log_message(f"No embeddings found in response for '{filename}' on attempt {attempt}. Full response: {response_json}")
            elif response.status_code == 429:
                log_message(f"Rate limit reached for '{filename}' on attempt {attempt}. Retrying after delay.")
                time.sleep(5)  # Wait longer if rate-limited
            else:
                log_message(f"Error {response.status_code} for '{filename}' on attempt {attempt}: {response.text}")
        
        except requests.exceptions.Timeout:
            log_message(f"Timeout on attempt {attempt} for '{filename}'")
        except requests.exceptions.RequestException as e:
            log_message(f"Request exception on attempt {attempt} for '{filename}': {e}")
        except json.JSONDecodeError as e:
            log_message(f"JSON decoding error for '{filename}' on attempt {attempt}: {e}")
        
        # Wait before retrying (using a shorter wait time for general retries)
        time.sleep(2)
    
    log_message(f"Failed to generate embedding for '{filename}' after {MAX_RETRIES} attempts")
    return None

def save_embedding(embedding, output_file, filename):
    """Saves the embedding to a JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as ef:
            json.dump({"embedding": embedding}, ef)
        log_message(f"Embedding for '{filename}' saved to '{output_file}'")
    except Exception as e:
        log_message(f"Error saving embedding for '{filename}': {e}")

def process_file(file_path, filename, embeddings_dir):
    """Processes a single file to generate and save its embedding."""
    output_file = os.path.join(embeddings_dir, f"{filename}.json")
    
    # Skip processing if the .json file already exists
    if os.path.exists(output_file):
        log_message(f"Skipping '{filename}' as '{output_file}' already exists")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        log_message(f"Error reading '{filename}': {e}")
        return
    
    log_message(f"Processing '{filename}' (Payload length: {len(text)} characters)")
    embedding = generate_embedding(text, filename)
    
    if embedding:
        save_embedding(embedding, output_file, filename)
    else:
        log_message(f"Failed to generate embedding for '{filename}'")

def process_chunks_concurrently(chunks_dir, embeddings_dir, max_workers=MAX_WORKERS):
    """Processes text chunks concurrently to generate and save embeddings."""
    os.makedirs(embeddings_dir, exist_ok=True)
    log_message(f"Starting concurrent processing of scripts in '{chunks_dir}' with {max_workers} workers")
    
    # Collect all files to process
    files_to_process = [
        filename for filename in os.listdir(chunks_dir)
        if "chunk" in filename and filename.endswith('.txt')
    ]
    
    # Filter out files that already have embeddings
    files_to_process = [
        filename for filename in files_to_process
        if not os.path.exists(os.path.join(embeddings_dir, f"{filename}.json"))
    ]
    
    total_files = len(files_to_process)
    log_message(f"Total files to process: {total_files}")
    
    if total_files == 0:
        log_message("No new files to process. Exiting.")
        return
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_file, os.path.join(chunks_dir, filename), filename, embeddings_dir): filename
            for filename in files_to_process
        }
        
        for future in as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                future.result()
            except Exception as e:
                log_message(f"Unhandled exception for '{filename}': {e}")
    
    log_message("Concurrent embedding generation completed for all files.")

def main():
    # Clear previous log file
    try:
        open(LOG_FILE, 'w').close()
    except Exception as e:
        print(f"Error clearing log file: {e}")
        sys.exit(1)
    
    # Directories
    chunks_dir = 'scripts'
    embeddings_dir = 'embeddings'
    
    try:
        process_chunks_concurrently(chunks_dir, embeddings_dir)
    except KeyboardInterrupt:
        log_message("Process interrupted by user. Exiting gracefully...")
        sys.exit(0)

if __name__ == "__main__":
    main()
