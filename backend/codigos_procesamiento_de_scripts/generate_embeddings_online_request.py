import os
import requests
import json
import time
from datetime import datetime

API_URL = "http://tormenta.ing.puc.cl/api/embed"
MODEL = "nomic-embed-text"
LOG_FILE = "embedding_generation_log.txt"
MAX_RETRIES = 3

def log_message(message):
    """Logs a message with a timestamp to both the console and a log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(log_entry + "\n")

def generate_embedding(text, filename):
    payload = {
        "model": MODEL,
        "input": text
    }
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Log payload length for troubleshooting
            log_message(f"Attempt {attempt} - Sending request for {filename} (Payload length: {len(text)} characters)")
            
            # Send the request with a 20-second timeout
            response = requests.post(API_URL, json=payload, timeout=20)
            
            if response.status_code == 200:
                log_message(f"Successfully received embedding for {filename} on attempt {attempt}")
                return response.json().get("embeddings", [])
            elif response.status_code == 429:
                log_message(f"Rate limit reached for {filename} on attempt {attempt}. Retrying after delay.")
                time.sleep(5)  # Wait longer if rate-limited
            else:
                log_message(f"Error {response.status_code} for {filename} on attempt {attempt}: {response.text}")
        
        except requests.exceptions.Timeout:
            log_message(f"Timeout on attempt {attempt} for {filename}")
        except requests.exceptions.RequestException as e:
            log_message(f"Request exception on attempt {attempt} for {filename}: {e}")
        except json.JSONDecodeError as e:
            log_message(f"JSON decoding error for {filename} on attempt {attempt}: {e}")
        
        # Wait before retrying (using a shorter wait time for general retries)
        time.sleep(1)
    
    log_message(f"Failed to generate embedding for {filename} after {MAX_RETRIES} attempts")
    return None

def process_chunks(chunks_dir):
    embeddings_dir = 'embeddings'
    os.makedirs(embeddings_dir, exist_ok=True)

    log_message(f"Starting processing of scripts in {chunks_dir}")

    for filename in os.listdir(chunks_dir):
        if "chunk" in filename and filename.endswith('.txt'):
            # Determine the output JSON filename
            output_file = os.path.join(embeddings_dir, f"{filename}.json")

            # Skip processing if the .json file already exists
            if os.path.exists(output_file):
                log_message(f"Skipping {filename} as {output_file} already exists")
                continue

            file_path = os.path.join(chunks_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            log_message(f"Processing {filename}")
            embedding = generate_embedding(text, filename)

            if embedding:
                with open(output_file, 'w', encoding='utf-8') as ef:
                    json.dump({"embedding": embedding}, ef)
                log_message(f"Embedding for {filename} saved to {output_file}")
            else:
                log_message(f"Failed to generate embedding for {filename}")

            # Respect rate limit of 10 requests per second
            time.sleep(1)
    
    log_message("Embedding generation completed for all files.")

if __name__ == "__main__":
    # Clear previous log file
    open(LOG_FILE, 'w').close()
    process_chunks('scripts')
