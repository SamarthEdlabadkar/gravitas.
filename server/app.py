import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import chromadb
from chromadb.utils import embedding_functions

from pydantic import BaseModel, Field
from typing import List

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

class GeneratedSummary(BaseModel):
    summary: str = Field(
        ...,
        description="Five sentences describing the entire information"
    )

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
    doc_id = data.get("id")
    query = data.get("query")

    if not doc_id or not query:
        return jsonify({"error": "Context for summary is required"}), 400
    
    chroma_client = chromadb.PersistentClient("server/static/chroma")
    ollama_embedder = embedding_functions.OllamaEmbeddingFunction(model_name="qwen3-embedding:4b")

    if doc_id[:3] == "PMC":
        db = "research_papers"
    else:
        db = "osdr_experiments"

    collection = chroma_client.get_collection(name=db)
    response = collection.query(
        query_embeddings=ollama_embedder(["query"]),
        n_results=1,
        include=["metadatas", "documents"],
        ids=[f"chunk_{doc_id}"]
    )

    print(response)

    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    client = instructor.from_groq(client, mode=instructor.Mode.JSON)

    prompt: str = """
    Role and Goal: You are an expert academic research analyst. Your primary goal is to synthesize and summarize a research paper's core contribution based on its provided title, abstract, and publication date.

Structure & Content Requirements:

1.  Core Contribution : State the single most important finding or argument of the paper.
2.  Methodology/Approach : Briefly describe the primary method, model, or approach used to conduct the research.
3.  Key Findings : List the most significant results or conclusions.
4.  Significance and Context : Explain why this paper is important to its field and how the publication date might offer historical context.

Tone and Style: The summary must be objective, formal, and strictly academic. Do not use conversational language or qualifiers unless absolutely necessary. 

The summary should be 5 sentences in length.

Input Data:
    """

    result = client.chat.completions.create(
        model='llama-3.1-8b-instant',  # currently working - llama-3.3-70b-versatile, llama3-8b-8192
        messages=[
            {
                "role": "user",
                "content": prompt + str(response["documents"][0][0]) + "\n\n Query: query" # type:ignore
            }
        ],
        temperature=0.2,
        max_retries=3,
        response_model=GeneratedSummary
    ) # type:ignore

    summary = result.model_dump()['summary']

    return jsonify({"summary": summary})

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