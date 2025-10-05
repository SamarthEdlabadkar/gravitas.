import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import chromadb
from chromadb.utils import embedding_functions

from dotenv import load_dotenv
from groq import Groq
import instructor

import sqlite3
import json

# Initialize the Flask application
app = Flask(__name__)
load_dotenv()
# Enable Cross-Origin Resource Sharing (CORS)
# This is crucial to allow your React frontend (running on a different port)
# to communicate with this Flask backend.
CORS(app)

def generate_embeddings(query: str):
    ollama_embedder = embedding_functions.OllamaEmbeddingFunction(model_name="qwen3-embedding:4b")
    return ollama_embedder([query])

# --- API Endpoints ---

@app.route('/search', methods=['POST'])
def search():
    """
    Endpoint to handle the initial user search query from the homepage.
    It takes a search term and returns the initial knowledge graph data
    and a list of related publication IDs.
    """
    data = request.get_json() 
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    chroma_client = chromadb.PersistentClient("server/static/chroma")
    collection = chroma_client.get_collection(name="research_papers")
    
    embeddings = generate_embeddings(query=query)
    
    response = collection.query(
        query_embeddings=embeddings,
        n_results=25,
        include=["metadatas", "documents"]
    )

    # Connect to the database (creates it if not exists)
    conn = sqlite3.connect("server/static/papers.db")
    cursor = conn.cursor()

    # Fetch all results
    rows = cursor.fetchall()

    # Display results
    for row in rows:
        title, classification = row
        classification = json.loads(classification)

    data = []

    for idx in range(len(response["documents"][0])): #type: ignore
        cursor.execute(f"SELECT title, classification FROM classifications WHERE TITLE = '{response["metadatas"][0][idx]["title"]}'") #type:ignore
        row = cursor.fetchone()
        classifications = json.loads(row[1])
        data.append((response["documents"][0][idx], response["metadatas"][0][idx], classifications)) #type: ignore

    return jsonify(data)


@app.route('/kg_node/<node_id>', methods=['GET'])
def get_node_details(node_id):
    """
    Endpoint to fetch detailed information for a specific node
    when a user clicks on it in the knowledge graph.
    """
    # --- In a real application ---
    # 1. Query your database/knowledge graph for the specific node_id.
    # 2. Return its details, connections, and related publications.

    # Mock response for demonstration
    mock_node_details = {
        "id": node_id,
        "label": "Microgravity Effects",
        "details": "This node represents the physiological and psychological effects of living in a low-gravity environment.",
        "connections": ["node_1", "node_3", "node_4"],
        "related_publications": ["pub_001", "pub_005"]
    }

    return jsonify(mock_node_details)


@app.route('/summary', methods=['POST'])
def get_summary():
    """
    Endpoint to generate a summary based on a selected node or user path.
    This would be the place to call a language model (LLM).
    """
    data = request.get_json()
    doc_id = data.get("id") # Could be a node_id, a list of nodes, etc.

    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    client = instructor.from_groq(client, mode=instructor.Mode.JSON)


    if not doc_id:
        return jsonify({"error": "Context for summary is required"}), 400

    # --- In a real application ---
    # 1. Gather the data related to the context (e.g., from your KG).
    # 2. Format a prompt for your LLM.
    # 3. Return the generated summary from the LLM.

    

    return jsonify({"summary": ""})

@app.route('/status', methods=['GET'])
def status():
    """
    A simple status check endpoint to confirm the API is running.
    """
    return jsonify({"status": "API is running"})

# This block allows you to run the app directly from the command line
# using `python app.py`
if __name__ == '__main__':
    # Runs the app on http://127.0.0.1:5000
    app.run(debug=True, port=5000)