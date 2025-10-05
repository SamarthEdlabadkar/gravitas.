# import json
# import sqlite3

# # Connect to the database (creates it if not exists)
# conn = sqlite3.connect("server/static/papers.db")
# cursor = conn.cursor()

# # Example query: select title and classification
# cursor.execute("SELECT title, classification FROM classifications")

# # Fetch all results
# rows = cursor.fetchall()

# # Display results
# for row in rows:
#     title, classification = row
#     classification = json.loads(classification)
    

# # Close connection
# conn.close()

import chromadb
from chromadb.utils import embedding_functions

def generate_embeddings(query: str):
    ollama_embedder = embedding_functions.OllamaEmbeddingFunction(model_name="qwen3-embedding:4b")
    return ollama_embedder([query])


query = "spaceflight"

chroma_client = chromadb.PersistentClient(
    path="server/static/chroma"
)
collection = chroma_client.get_collection(name="research_papers")

embeddings = generate_embeddings(query=query)

response = collection.query(
    query_embeddings=embeddings,
    n_results=15,
    include=["metadatas", "documents"]
)

import pprint

pprint.pprint(response)
