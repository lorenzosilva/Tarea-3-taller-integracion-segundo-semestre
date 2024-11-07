# backend.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import requests
import faiss
import numpy as np
import json
import os
import logging
from datetime import datetime

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pregunta-peliculas.netlify.app"],  # Adjust if deploying to a different domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static images
app.mount("/images", StaticFiles(directory="public/images"), name="images")

# Load FAISS index and metadata
INDEX_PATH = "vector_db.index"
METADATA_PATH = "metadata.json"
SCRIPTS_DIR = "scripts_chunks"  # Updated to reflect your directory structure

if not os.path.exists(INDEX_PATH) or not os.path.exists(METADATA_PATH):
    logger.error("Vector database files not found.")
    raise FileNotFoundError("Vector database files not found.")

try:
    index = faiss.read_index(INDEX_PATH)
    with open(METADATA_PATH, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    logger.info("FAISS index and metadata loaded successfully.")
except Exception as e:
    logger.error(f"Error loading FAISS index or metadata: {e}")
    raise e

# Extract list of selected movies from metadata
selected_movies = list({filename.split('_chunk_')[0] for filename in metadata})
logger.info(f"Selected Movies: {selected_movies}")

class QueryRequest(BaseModel):
    query: str
    # Optional conversation history for chat interactions
    conversation_history: Optional[List[dict]] = None  # e.g., [{"role": "user", "content": "Hello"}, ...]

class StatusResponse(BaseModel):
    status: str
    available_movies: List[str]

class Movie(BaseModel):
    title: str
    description: str
    image_url: str

# Load movie descriptions from movies.json
MOVIES_JSON_PATH = "movies.json"

if not os.path.exists(MOVIES_JSON_PATH):
    logger.error("movies.json file not found.")
    raise FileNotFoundError("movies.json file not found.")

try:
    with open(MOVIES_JSON_PATH, 'r', encoding='utf-8') as f:
        movies_data = json.load(f)
    logger.info("Movies data loaded successfully.")
except Exception as e:
    logger.error(f"Error loading movies.json: {e}")
    raise e

@app.get("/status", response_model=StatusResponse)
def get_status():
    """
    Endpoint to check if the backend is running and retrieve the list of selected movies.
    """
    return {
        "status": "running",
        "available_movies": selected_movies
    }

@app.get("/movies", response_model=List[Movie])
def get_movies():
    """
    Endpoint to retrieve movie details including title, description, and image URL.
    """
    return movies_data

def get_embedding(text):
    """
    Calls the embedding API to get the embedding vector for the input text.
    """
    API_URL = "http://tormenta.ing.puc.cl/api/embed"  # Consider switching to HTTPS if required
    payload = {
        "model": "nomic-embed-text",
        "input": text
    }
    logger.info(f"Calling Embedding API at {API_URL} with payload: {payload}")

    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        logger.info(f"Received response from Embedding API: Status Code {response.status_code}")
        response.raise_for_status()
        embeddings = response.json().get("embeddings", [])
        if not embeddings:
            logger.error("No embeddings returned from embedding API.")
            raise HTTPException(status_code=500, detail="No embeddings returned.")
        logger.info("Embedding retrieved successfully.")
        return embeddings[0]
    except requests.exceptions.Timeout:
        logger.error("Embedding API request timed out.")
        raise HTTPException(status_code=500, detail="Embedding API request timed out.")
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while calling Embedding API: {http_err}")
        raise HTTPException(status_code=500, detail=f"Embedding API HTTP error: {http_err}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Embedding API request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding API request failed: {e}")
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response from Embedding API.")
        raise HTTPException(status_code=500, detail="Invalid JSON response from Embedding API.")

def get_similar_fragments(embedding, top_k=5):
    """
    Retrieves the top_k most similar script fragments based on the embedding.
    """
    try:
        D, I = index.search(np.array([embedding]).astype('float32'), top_k)
        similar = [metadata[i] for i in I[0]]
        logger.info(f"Retrieved similar fragments: {similar}")
        return similar
    except Exception as e:
        logger.error(f"FAISS search failed: {e}")
        raise HTTPException(status_code=500, detail=f"FAISS search failed: {e}")

def prepare_context(similar_fragments):
    """
    Constructs the context by reading the relevant script fragments.
    """
    context = ""
    for fragment in similar_fragments:
        script_filename = fragment  # No extra .txt appended
        script_path = os.path.join(SCRIPTS_DIR, script_filename)
        if os.path.exists(script_path):
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    fragment_text = f.read()
                    context += fragment_text + "\n"
                logger.info(f"Added fragment from {script_filename} to context.")
            except Exception as e:
                logger.error(f"Error reading script file {script_filename}: {e}")
        else:
            logger.warning(f"Script file {script_filename} not found.")
    return context



def truncate_context(context, max_tokens=2000):
    """
    Ensures the context length is within the LLM's context window.
    """
    tokens = len(context.split())
    if tokens > max_tokens:
        context = ' '.join(context.split()[:max_tokens])
        logger.info(f"Context truncated to {max_tokens} tokens.")
    return context

def call_llm_api(prompt, conversation_history=None):
    """
    Calls the appropriate LLM API endpoint based on the presence of conversation history.
    """
    try:
        if conversation_history:
            # Use the chat API endpoint
            api_url = "https://tormenta.ing.puc.cl/api/chat"  # Ensure correct protocol
            payload = {
                "model": "integra-LLM",
                "messages": conversation_history + [{"role": "user", "content": prompt}]
            }
            logger.info(f"Calling Chat API at {api_url} with payload: {payload}")
        else:
            # Use the generate API endpoint
            api_url = "http://tormenta.ing.puc.cl/api/generate"  # Consider switching to HTTPS if required
            payload = {
                "model": "integra-LLM",
                "prompt": prompt,
                "stream": False,  # Ensure streaming is disabled for simplicity
                "temperature": 0.1,  # Added parameter for faster, deterministic responses
                "top_k": 1,          # Added parameter to limit token options
                "max_tokens": 50     # Added parameter to limit response length
            }
            logger.info(f"Calling Generate API at {api_url} with payload: {payload}")

        response = requests.post(api_url, json=payload, timeout=600)  # Increased timeout to 10 minutes
        logger.info(f"Received response from LLM API: Status Code {response.status_code}")

        response.raise_for_status()

        if conversation_history:
            # Expecting a chat-like response
            json_resp = response.json()
            answer = json_resp.get("message", {}).get("content", "")
            logger.info(f"LLM Chat API Response Content: {answer}")
        else:
            # Expecting a completion-like response
            json_resp = response.json()
            answer = json_resp.get("response", "")
            logger.info(f"LLM Generate API Response Content: {answer}")

        if not answer:
            logger.error("LLM API did not return a response.")
            raise HTTPException(status_code=500, detail="LLM API did not return a response.")

        logger.info("LLM API responded successfully.")
        return answer

    except requests.exceptions.Timeout:
        logger.error("LLM API request timed out.")
        raise HTTPException(status_code=504, detail="LLM API request timed out.")
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while calling LLM API: {http_err}")
        raise HTTPException(status_code=500, detail=f"LLM API HTTP error: {http_err}")
    except requests.exceptions.RequestException as e:
        logger.error(f"LLM API request failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM API request failed: {e}")
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response from LLM API.")
        raise HTTPException(status_code=500, detail="Invalid JSON response from LLM API.")


@app.post("/query")
def handle_query(request: QueryRequest):
    """
    Handles user queries by retrieving relevant script fragments and interacting with the LLM API.
    Supports both chat and completion modes based on the presence of conversation history.
    """
    try:
        logger.info(f"Received query: '{request.query}' with conversation history: {request.conversation_history}")

        # Step 1: Get embedding of the query
        query_embedding = get_embedding(request.query)

        # Step 2: Retrieve similar fragments
        similar_fragments = get_similar_fragments(query_embedding, top_k=5)

        # Step 3: Prepare context
        context = prepare_context(similar_fragments)

        if not context:
            logger.error("No context available for the query.")
            raise HTTPException(status_code=500, detail="No context available for the query.")

        # Ensure context length within LLM's context window
        context = truncate_context(context, max_tokens=2000)

        # Step 4: Call LLM API
        prompt = f"Context: {context}\n\nQuestion: {request.query}\nAnswer:"

        logger.info(f"Prepared prompt for LLM API: {prompt}")

        answer = call_llm_api(prompt, conversation_history=request.conversation_history)

        logger.info(f"Generated answer: {answer}")

        return {"answer": answer}

    except HTTPException as he:
        logger.error(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unhandled exception in /query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
