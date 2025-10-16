import csv
import os
import time
from typing import List, Dict, Tuple
import chromadb
from google import genai
from chromadb.api.types import Documents, Embeddings
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Load environment variables (ensure GEMINI_API_KEY is available)
load_dotenv()

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your environment or .env file.")

# ChromaDB Configuration
CHROMA_PATH = "server/static/chroma"
COLLECTION_NAME = "research_papers"
CSV_FILE_PATH = "server/static/data_pubmed.csv"

# Gemini Embedding Configuration
MODEL_NAME = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 2560 
BATCH_SIZE = 50 
DELAY_SECONDS = 60 # Pause for 1 minute to manage API quota

# --- Custom Gemini Embedding Function for ChromaDB ---

class GeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Custom EmbeddingFunction using the Google Gemini API with output dimension control."""
    def __init__(self, api_key: str, model_name: str, output_dim: int):
        self.client = genai.Client(api_key=api_key)
        self.model = model_name
        self.output_dim = output_dim

    def __call__(self, input: Documents) -> Embeddings:
        """Generates embeddings for a list of documents (batching)."""
        embeddings_list: List[List[float]] = []
        
        try:
            # Uses 'contents' (plural) and includes output_dimensionality
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
            
            print(f"  -> Successfully generated {len(embeddings_list)} embeddings.")
            return embeddings_list

        except Exception as e:
            # Log potential API errors (like Quota Exceeded)
            print(f"❌ Error calling Gemini embedding API for batch of size {len(input)}: {e}")
            return [] 

# --- Helper Function to Handle Deduplication and Insertion ---

def add_batch_to_chroma(
    ids: List[str], 
    documents: List[str], 
    metadatas: List[Dict], 
    collection: chromadb.Collection, 
    delay: int
) -> int:
    """
    Processes the current batch: enforces ID uniqueness (by keeping the last entry), 
    adds to ChromaDB, and applies rate limiting delay.
    """
    if not ids:
        return 0
        
    # --- DEDUPLICATION LOGIC: Use a dict to keep only the last occurrence of each ID ---
    unique_data: Dict[str, Tuple[str, Dict]] = {}
    for i in range(len(ids)):
        unique_data[ids[i]] = (documents[i], metadatas[i])
        
    unique_ids = list(unique_data.keys())
    unique_documents = [item[0] for item in unique_data.values()]
    unique_metadatas = [item[1] for item in unique_data.values()]

    # Reporting on deduplication
    duplicates_found = len(ids) - len(unique_ids)
    if duplicates_found > 0:
        print(f"⚠️ Warning: Removed {duplicates_found} local duplicates from this batch.")

    if unique_ids:
        print(f"Processing unique batch of {len(unique_ids)} documents...")
        collection.add(
            ids=unique_ids,
            documents=unique_documents,
            metadatas=unique_metadatas
        )
        
        # Quota Management: Pause after a successful API call
        print(f"⏸️ Batch completed. Quota delay: Sleeping for {delay} seconds...")
        time.sleep(delay) 
        
    return len(unique_ids)

# ----------------------------------------------------------------------
# --- Main Execution ---
# ----------------------------------------------------------------------

# Instantiate the custom Gemini embedder
gemini_embedder = GeminiEmbeddingFunction(
    api_key=GEMINI_API_KEY,
    model_name=MODEL_NAME,
    output_dim=EMBEDDING_DIMENSION
)

# Initialize ChromaDB Persistent Client
client = chromadb.PersistentClient(CHROMA_PATH)

# --- ACTION: Delete and Recreate the Collection to resolve conflicts ---
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
# --- Process CSV Data ---
# ----------------------------------------------------------------------

print(f"\n--- Starting CSV Processing ---")

# Lists to hold batched data
ids: List[str] = []
documents: List[str] = []
metadatas: List[dict] = []
row_counter = 0
total_added = 0

try:
    with open(CSV_FILE_PATH, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader, None)
        
        if header is None:
             print("❌ Error: CSV file is empty.")
             exit()

        for i, row in enumerate(reader):
            row_counter = i + 1
            # Check for sufficient columns
            if not row or len(row) < 15: 
                print(f"Skipping row {row_counter}: Incomplete data.")
                continue
            
            try:
                # Data extraction based on your CSV structure (0-indexed)
                pmc_id = row[0].strip()
                DOI = row[1].strip()
                title = row[2].strip()
                journal = row[3].strip()
                year = row[4].strip()
                authors = row[5].strip()
                abstract = row[6].strip()
                link = row[14].strip() # Link_Input

                # Ensure PMC_ID is not empty before processing
                if not pmc_id:
                    print(f"Skipping row {row_counter}: Empty PMC_ID.")
                    continue

                # Data to embed
                layer1_text = f"Title: {title}\nAbstract: {abstract}"
                
                # Append to batches
                ids.append(f"chunk_{pmc_id}")
                documents.append(layer1_text)
                metadatas.append({
                    "pmc_id": pmc_id,
                    "doi": DOI,
                    "title": title,
                    "year": year,
                    "journal": journal,
                    "authors": authors, 
                    "link": link
                })

                # Check if batch is full
                if len(ids) >= BATCH_SIZE:
                    added_count = add_batch_to_chroma(ids, documents, metadatas, collection, DELAY_SECONDS)
                    total_added += added_count
                    
                    # Reset batches
                    ids, documents, metadatas = [], [], []

            except IndexError:
                print(f"Skipping row {row_counter}: Data format error (missing column).")
            except Exception as e:
                print(f"Skipping row {row_counter}. Unexpected error: {e}")


        # Add any remaining documents (the final partial batch)
        if ids:
            added_count = add_batch_to_chroma(ids, documents, metadatas, collection, 1) # Short delay for final small batch
            total_added += added_count

        # --- FINAL VERIFICATION ---
        final_count = collection.count()
        print(f"\n✅ Processing complete.")
        print(f"Total rows read from CSV: {row_counter}")
        print(f"Total unique documents added to ChromaDB: {final_count} (Expected added count: {total_added})")

except FileNotFoundError:
    print(f"❌ Error: CSV file not found at {CSV_FILE_PATH}")
except Exception as e:
    print(f"❌ An unexpected critical error occurred: {e}")
