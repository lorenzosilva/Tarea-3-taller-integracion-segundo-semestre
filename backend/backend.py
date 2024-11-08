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
from difflib import get_close_matches

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

# Define the base URL for the LLM API
# BASE_API_URL = "http://localhost:11434"
BASE_API_URL = "http://tormenta.ing.puc.cl"


# Define specific API endpoints
EMBEDDING_API_PATH = "/api/embed"
COMPLETION_API_PATH = "/api/generate"  # Primary endpoint
CHAT_API_PATH = "/api/chat"            # Fallback endpoint

# Construct full URLs by combining base URL with endpoint paths
EMBEDDING_API_URL = f"{BASE_API_URL}{EMBEDDING_API_PATH}"
COMPLETION_API_URL = f"{BASE_API_URL}{COMPLETION_API_PATH}"
CHAT_API_URL = f"{BASE_API_URL}{CHAT_API_PATH}"

# Define the list of selected movies
selected_movies = [
    'supergirl',
    'surfer_king',
    'surrogates',
    'suspect_zero',
    'sweeney_todd',
    'sweet_hereafter',
    'sweet_smell_of_success',
    'swingers',
    'swordfish',
    'synecdoche_new_york'
]

# Load FAISS index and metadata
INDEX_PATH = "vector_db.index"
METADATA_PATH = "metadata.json"
SCRIPTS_DIR = "scripts_chunks"  # Directory containing script chunks

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

# Validate that metadata contains only chunks from selected movies
for chunk in metadata:
    movie_name = chunk.split('_chunk_')[0]
    if movie_name not in selected_movies:
        logger.warning(f"Chunk {chunk} is from an unselected movie: {movie_name}")

class QueryRequest(BaseModel):
    query: str
    selected_movie: Optional[str] = None  # Optional field for selected movie

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
    payload = {
        "model": "nomic-embed-text",
        "input": text
    }
    logger.info(f"Calling Embedding API at {EMBEDDING_API_URL} with payload: {payload}")

    try:
        response = requests.post(EMBEDDING_API_URL, json=payload, timeout=None)
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

def get_relevant_movies(query: str, selected_movies: List[str], cutoff=0.6) -> List[str]:
    """
    Identifies which selected movies are mentioned in the query using fuzzy matching.
    """
    query_lower = query.lower()
    matched_movies = []

    # Exact matches
    for movie in selected_movies:
        movie_lower = movie.lower().replace('_', ' ').replace('-', ' ')
        if movie_lower in query_lower:
            matched_movies.append(movie)

    # Fuzzy matching if no exact matches
    if not matched_movies:
        movie_names = [m.replace('_', ' ').replace('-', ' ').lower() for m in selected_movies]
        query_processed = query_lower.replace(',', '').replace('.', '').lower()
        possible_matches = get_close_matches(query_processed, movie_names, n=1, cutoff=cutoff)

        if possible_matches:
            # Find the original movie name
            for movie, name in zip(selected_movies, movie_names):
                if name == possible_matches[0]:
                    matched_movies.append(movie)

    logger.info(f"Identified relevant movies from query: {matched_movies}")
    return matched_movies

def get_similar_fragments(embedding, top_k=20, relevant_movies: Optional[List[str]] = None):
    """
    Retrieves the top_k most similar script fragments based on the embedding.
    If relevant_movies is provided, filters the similar fragments to include only those from the relevant movies.
    """
    try:
        D, I = index.search(np.array([embedding]).astype('float32'), top_k)
        similar = [metadata[i] for i in I[0]]
        logger.info(f"Retrieved similar fragments: {similar}")

        if relevant_movies:
            # Filter similar fragments to include only those from relevant_movies
            filtered_similar = [chunk for chunk in similar if chunk.split('_chunk_')[0] in relevant_movies]
            logger.info(f"Filtered similar fragments based on relevant movies: {filtered_similar}")

            if not filtered_similar:
                logger.warning("No similar chunks found for the relevant movies.")
                # Optionally, fallback to random chunks or raise an exception
                raise HTTPException(status_code=404, detail="No relevant chunks found for the query.")

            # Limit to top 5 relevant chunks
            return filtered_similar[:5]
        else:
            # If no relevant movies, select one chunk per movie
            random_chunks = []
            for movie in selected_movies:
                # Find all chunks from this movie in the similar list
                movie_chunks = [chunk for chunk in similar if chunk.split('_chunk_')[0] == movie]
                if movie_chunks:
                    # Append the first chunk found for this movie
                    random_chunks.append(movie_chunks[0])
            logger.info(f"Randomly selected chunks from each movie: {random_chunks}")
            return random_chunks

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

def call_llm_api(prompt):
    """
    Attempts to call the /api/generate endpoint.
    If it fails with a 404 error, falls back to the /api/chat endpoint.
    """
    try:
        # Attempt to use the /api/generate endpoint with optimized parameters
        payload_generate = {
            # "model": "llama3.2",  # Corrected model name
            "model": "integra-LLM",  # Corrected model name
            "prompt": prompt,
            "stream": False,
            "temperature": 0.65,  # Slightly lowered to improve coherence
            "top_k": 50,          # Allows more varied token selection for richer responses
            "top_p": 0.9,         # Nucleus sampling for more natural response generation
            "max_tokens": 300     # Increased to allow longer, detailed answers
        }
        logger.info(f"Calling Completion API at {COMPLETION_API_URL} with payload: {payload_generate}")
        response = requests.post(COMPLETION_API_URL, json=payload_generate, timeout=None)
        logger.info(f"Received response from Completion API: Status Code {response.status_code}")
        response.raise_for_status()

        json_resp = response.json()
        answer = json_resp.get("response", "")
        if not answer:
            logger.error("Completion API did not return a response.")
            raise HTTPException(status_code=500, detail="Completion API did not return a response.")
        logger.info(f"Completion API Response Content: {answer}")
        return answer

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            logger.warning(f"Completion API not found (404). Attempting to use Chat API as fallback.")
            try:
                # Fallback to /api/chat with optimized parameters
                payload_chat = {
                    # "model": "llama3.2",  # Corrected model name
                    "model": "integra-LLM",  # Corrected model name
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "temperature": 0.65,
                    "top_k": 50,
                    "top_p": 0.9,
                    "max_tokens": 300
                }
                logger.info(f"Calling Chat API at {CHAT_API_URL} with payload: {payload_chat}")
                response_chat = requests.post(CHAT_API_URL, json=payload_chat, timeout=None)
                logger.info(f"Received response from Chat API: Status Code {response_chat.status_code}")
                response_chat.raise_for_status()

                json_resp_chat = response_chat.json()
                answer_chat = json_resp_chat.get("message", {}).get("content", "")
                if not answer_chat:
                    logger.error("Chat API did not return a response.")
                    raise HTTPException(status_code=500, detail="Chat API did not return a response.")
                logger.info(f"Chat API Response Content: {answer_chat}")
                return answer_chat

            except requests.exceptions.RequestException as e_chat:
                logger.error(f"Failed to call Chat API as fallback: {e_chat}")
                raise HTTPException(status_code=500, detail="Failed to call Chat API as fallback.")
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON response from Chat API.")
                raise HTTPException(status_code=500, detail="Invalid JSON response from Chat API.")

        else:
            logger.error(f"HTTP error occurred while calling Completion API: {http_err}")
            raise HTTPException(status_code=500, detail=f"Completion API HTTP error: {http_err}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Completion API request failed: {e}")
        raise HTTPException(status_code=500, detail="Completion API request failed.")
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response from Completion API.")
        raise HTTPException(status_code=500, detail="Invalid JSON response from Completion API.")

@app.post("/query")
def handle_query(request: QueryRequest):
    """
    Handles user queries by retrieving relevant script fragments and interacting with the LLM API.
    Always uses the /api/generate endpoint, with /api/chat as a fallback.
    """
    try:
        logger.info(f"Received query: '{request.query}' with selected_movie: '{request.selected_movie}'")

        # Step 1: If selected_movie is provided, use it; else, perform keyword extraction
        if request.selected_movie and request.selected_movie.lower().replace(' ', '_') in selected_movies:
            # Normalize movie name to match backend's selected_movies format
            normalized_movie = request.selected_movie.lower().replace(' ', '_')
            if normalized_movie in selected_movies:
                relevant_movies = [normalized_movie]
                logger.info(f"Using selected_movie: {relevant_movies}")
            else:
                logger.warning(f"Selected movie '{request.selected_movie}' is not in the list of selected_movies.")
                relevant_movies = []
        else:
            # Perform keyword extraction
            relevant_movies = get_relevant_movies(request.query, selected_movies)

        # Step 2: Get embedding of the query
        query_embedding = get_embedding(request.query)

        # Step 3: Retrieve similar fragments based on embedding and relevant_movies
        similar_fragments = get_similar_fragments(query_embedding, top_k=20, relevant_movies=relevant_movies)

        # Step 4: Prepare context
        context = prepare_context(similar_fragments)

        if not context:
            logger.error("No context available for the query.")
            raise HTTPException(status_code=500, detail="No context available for the query.")

        # Step 5: Ensure context length within LLM's context window
        context = truncate_context(context, max_tokens=2000)

        # Step 6: Call LLM API
        prompt = f"Context: {context}\n\nQuestion: {request.query}\nAnswer:"
        logger.info(f"Prepared prompt for LLM API: {prompt}")

        answer = call_llm_api(prompt)
        logger.info(f"Generated answer: {answer}")

        return {"answer": answer}

    except HTTPException as he:
        logger.error(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unhandled exception in /query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
