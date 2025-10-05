import csv
import json
from typing import List
import chromadb
from chromadb.utils import embedding_functions

# --- Initialize ChromaDB ---
client = chromadb.PersistentClient("server/static/chroma")
collection = client.get_or_create_collection(
    name="research_papers"
)

ollama_embedder = embedding_functions.OllamaEmbeddingFunction(model_name="qwen3-embedding:4b")


# --- Helper: Sentence splitting (simple) ---
def split_sentences(text: str):
    sentences = text.split(".")
    return [s for s in sentences if s]

def join_sentences(sentences: List[str]):
    joints = []
    for i in range(len(sentences) // 5):
        joints += "".join(sentences[i:i+5])
    return joints


with open("server/static/extracted_article_data.csv", newline='', encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    reader.__next__()
    
    for row in reader:
        pmc_id = row[0]
        DOI = row[1]
        journal = row[3]
        year = row[4]
        authors = row[5]
        link = row[14]

        print(f"PMC ID: {pmc_id}")
        print(f"DOI: {DOI}")
        print(f"Journal: {journal}")
        print(f"Year: {year}")
        print(f"Authors: {authors}")
        print(f"Link: {link}")

        # Data to embed
        title = row[2]
        abstract = row[6]


        layer1_text = f"Title: {title}\nAbstract: {abstract}"
        embeddings = ollama_embedder([layer1_text])
        

        collection.add(
            ids = [f"chunk_{pmc_id}"],
            embeddings=ollama_embedder([layer1_text]),
            documents=[layer1_text],
            metadatas=[{
                "pmc_id": pmc_id,
                "title": title,
                "year": year,
                "journal": journal,
                "authors": json.dumps(authors),
                "link": link
            }]
        )

