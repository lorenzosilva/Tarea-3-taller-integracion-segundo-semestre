import os
import json
import numpy as np
import faiss

def load_embeddings(embeddings_dir):
    vectors = []
    metadata = []
    for filename in os.listdir(embeddings_dir):
        if filename.endswith('.json'):
            with open(os.path.join(embeddings_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                vectors.append(data['embedding'])
                metadata.append(filename.replace('.json', ''))
    return np.array(vectors).astype('float32'), metadata

if __name__ == "__main__":
    embeddings_dir = 'embeddings'
    vectors, metadata = load_embeddings(embeddings_dir)
    
    dimension = 768  # As specified
    index = faiss.IndexFlatL2(dimension)
    index.add(vectors)
    
    # Save the index and metadata
    faiss.write_index(index, "vector_db.index")
    with open("metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f)
    
    print("Vector database created and saved.")
