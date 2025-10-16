import csv
import os
import time
from typing import List
import chromadb
from google import genai
from chromadb.api.types import Documents, Embeddings
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Load environment variables (for GEMINI_API_KEY)
load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your environment or .env file.")

# ChromaDB Configuration
CHROMA_PATH = "server/static/chroma"
COLLECTION_NAME = "osdr_experiments"
CSV_FILE_PATH = "server/static/data_OSD.csv"

# Gemini Embedding Configuration
MODEL_NAME = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 2560 

# --- Custom Gemini Embedding Function for ChromaDB ---

class GeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """A custom EmbeddingFunction to use the Google Gemini API."""
    def __init__(self, api_key: str, model_name: str, output_dim: int):
        self.client = genai.Client(api_key=api_key)
        self.model = model_name
        self.output_dim = output_dim

    def __call__(self, input: Documents) -> Embeddings:
        """Generates embeddings for a list of documents (batching)."""
        embeddings_list: List[List[float]] = []
        
        try:
            # Removed 'task_type' to fix previous error.
            result = self.client.models.embed_content(
                model=self.model,
                contents=input, 
                config={
                    "output_dimensionality": self.output_dim 
                }
            )

            for embedding in result.embeddings:
                vector = embedding.values
                if len(vector) != self.output_dim:
                    raise ValueError(
                        f"Mismatch: Expected {self.output_dim} dims, got {len(vector)}."
                    )
                embeddings_list.append(vector)
            
            # DEBUG: Print success on embedding batch
            print(f"  -> Successfully generated {len(embeddings_list)} embeddings.")
            return embeddings_list

        except Exception as e:
            # Log the Quota error clearly
            print(f"❌ Error calling Gemini embedding API for batch of size {len(input)}: {e}")
            return [] 

# ----------------------------------------------------------------------
# --- Initialize ChromaDB and Embedder ---
# ----------------------------------------------------------------------

# Instantiate the custom Gemini embedder
gemini_embedder = GeminiEmbeddingFunction(
    api_key=GEMINI_API_KEY,
    model_name=MODEL_NAME,
    output_dim=EMBEDDING_DIMENSION
)

# Initialize ChromaDB Persistent Client
client = chromadb.PersistentClient(CHROMA_PATH)

# --- ACTION: Delete and Recreate the Collection ---
print(f"\n--- ChromaDB Setup ---")
try:
    client.delete_collection(name=COLLECTION_NAME)
    print(f"✅ Successfully deleted old collection: '{COLLECTION_NAME}'")
except ValueError as e:
    if "does not exist" in str(e):
        print(f"Collection '{COLLECTION_NAME}' did not exist, proceeding to create.")
    else:
        raise e
except Exception as e:
    print(f"Error during collection deletion: {e}")

# Create the new collection with the custom embedder
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=gemini_embedder 
)

print(f"Collection '{COLLECTION_NAME}' is ready (Initial Count: {collection.count()}).")

# ----------------------------------------------------------------------
# --- Process CSV and Add to ChromaDB ---
# ----------------------------------------------------------------------

print(f"\n--- Starting CSV Processing ---")

# Lists to hold batched data
ids: List[str] = []
documents: List[str] = []
metadatas: List[dict] = []
BATCH_SIZE = 50 
row_counter = 0

try:
    with open(CSV_FILE_PATH, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader, None) 
        
        if header is None:
             print("❌ Error: CSV file is empty.")
             exit()

        for i, row in enumerate(reader):
            row_counter = i + 1
            if not row or len(row) < 4: 
                print(f"Skipping row {row_counter}: Incomplete data.")
                continue
            
            try:
                osd_id = row[0]
                title = row[1]
                authors = row[2]
                description = row[3]
                link = f"https://osdr.nasa.gov/bio/repo/data/studies/{osd_id}"

                layer1_text = f"Title: {title}\nDescription: {description}"
                
                # Append to batches
                ids.append(f"chunk_{osd_id}")
                documents.append(layer1_text)
                metadatas.append({
                    "osd_id": osd_id,
                    "title": title,
                    "authors": authors,
                    "link": link
                })

                # Check if batch is full
                if len(ids) >= BATCH_SIZE:
                    print(f"Processing batch of {len(ids)} documents...")
                    collection.add(
                        ids=ids,
                        documents=documents,
                        metadatas=metadatas
                    )
                    
                    # --- ACTION: Introduce 60-second delay to respect API rate limit ---
                    print("⏸️ Quota delay: Sleeping for 60 seconds...")
                    time.sleep(60) # Pause for 1 minute after adding a batch
                    
                    # Reset batches
                    ids, documents, metadatas = [], [], []

            except IndexError:
                print(f"Skipping row {row_counter}: Data format error (missing column).")
            except Exception as e:
                print(f"Skipping row {row_counter}. Unexpected error: {e}")


        # Add any remaining documents (the final partial batch)
        if ids:
            print(f"Processing final batch of {len(ids)} documents...")
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            # Introduce a final delay
            time.sleep(1)

        # --- FINAL VERIFICATION ---
        final_count = collection.count()
        print(f"\n✅ Processing complete. Total rows in CSV: {row_counter}. Final ChromaDB count: {final_count}")

except FileNotFoundError:
    print(f"❌ Error: CSV file not found at {CSV_FILE_PATH}")
except Exception as e:
    print(f"❌ An unexpected critical error occurred: {e}") 