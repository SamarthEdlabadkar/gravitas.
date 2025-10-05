import chromadb
from chromadb.utils import embedding_functions

doc_id = "PMC3040128"

chroma_client = chromadb.PersistentClient("server/static/chroma")

chroma_client.delete_collection("research_papers")

# if doc_id[:3] == "PMC":
#     db = "research_papers"
# else:
#     db = "osdr_experiments"

# collection = chroma_client.get_collection(name=db)
# response = collection.query(
#     query_texts=[embedding_functions.OllamaEmbeddingFunction("qwen3-embedding:4b")],
#     n_results=1,
#     include=["metadatas", "documents"],
#     ids=[f"chunk_{doc_id}"]
# )