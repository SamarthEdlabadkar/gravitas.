import csv
import json
from typing import List
import chromadb
from chromadb.utils import embedding_functions

# --- Initialize ChromaDB ---
client = chromadb.PersistentClient("server/static/chroma")
collection = client.get_or_create_collection(
    name="osdr_experiments"
)

ollama_embedder = embedding_functions.OllamaEmbeddingFunction(model_name="qwen3-embedding:4b")

with open("server/static/data_OSD.csv", newline='', encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    reader.__next__()
    
    for row in reader:
        osd_id = row[0]
        authors = row[2]
        link = f"https://osdr.nasa.gov/bio/repo/data/studies/{osd_id}"

        print(f"OSD ID: {osd_id}")
        print(f"Authors: {authors}")

        # Data to embed
        title = row[1]
        description = row[3]


        layer1_text = f"Title: {title}\nDescription: {description}"
        embeddings = ollama_embedder([layer1_text])
        

        collection.add(
            ids = [f"chunk_{osd_id}"],
            embeddings=ollama_embedder([layer1_text]),
            documents=[layer1_text],
            metadatas=[{
                "osd_id": osd_id,
                "title": title,
                "authors": authors,
                "link": link
            }]
        )

