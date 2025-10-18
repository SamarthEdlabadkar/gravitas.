import chromadb

# --- 1. Connection Setup ---
# Initialize the ChromaDB client. 
# Use the appropriate client for your setup (Persistent, HTTP, or in-memory).
# Example for a persistent local database:
client = chromadb.PersistentClient(path="server\static\chroma") 

# --- 2. Get the Collection ---
# Replace 'your_collection_name' with the name of your target collection.
collection = client.get_collection(name="research_papers")

# --- 3. Define the Target ID ---
# Replace 'the_specific_vector_id' with the unique ID of the vector you want to retrieve.
# This ID should match the ID assigned during the vector creation/upload process.
target_id = "chunk_PMC4136787" 

# --- 4. Retrieve the Specific Vector Data ---
# Use .get() and include the 'embeddings' field.
# By setting 'ids', you retrieve only the specified vector.
result = collection.get(
    ids=[target_id],
    include=['embeddings', 'documents', 'metadatas'] 
)

# --- 5. Extract and Display the Vector ---
if result['ids']:
    print(f"✅ Successfully retrieved vector for ID: {result['ids'][0]}")
    
    # The actual vector is the first (and only) item in the 'embeddings' list
    specific_vector = result['embeddings'][0]
    
    print("-" * 30)
    print(f"Vector Dimension (Length): {len(specific_vector)}")
    print(f"First 20 components: {specific_vector[:20]}")

else:
    print(f"❌ Error: Vector with ID '{target_id}' not found.")