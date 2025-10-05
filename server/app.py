from flask import Flask, jsonify, request
from flask_cors import CORS
import chromadb
from chromadb.utils import embedding_functions

# Initialize the Flask application
app = Flask(__name__)

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

    chroma_client = chromadb.Client()
    collection = chroma_client.get_collection(name="research_papers")
    
    embeddings = generate_embeddings(query=query)
    
    response = collection.query(
        query_embeddings=embeddings,
        n_results=15,
        include=["metadatas", "distances"]
    )

    print(response.items())

    # Mock response for demonstration
    mock_graph_data = {
        "nodes": [
            {"id": "center_node", "label": query, "type": "query"},
            {"id": "node_1", "label": "Human Physiology", "type": "topic"},
            {"id": "node_2", "label": "Microgravity Effects", "type": "topic"},
            {"id": "node_3", "label": "Cardiovascular System", "type": "sub_topic"},
        ],
        "links": [
            {"source": "center_node", "target": "node_1"},
            {"source": "center_node", "target": "node_2"},
            {"source": "node_2", "target": "node_3"},
        ]
    }
    mock_publications = [
        {"id": "pub_001", "title": "The Heart in Space", "authors": "J. Doe"},
        {"id": "pub_002", "title": "Bone Density Loss in Astronauts", "authors": "A. Smith"},
    ]

    return jsonify({
        "graphData": mock_graph_data,
        "publications": mock_publications
    })

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
    context = data.get('context') # Could be a node_id, a list of nodes, etc.

    if not context:
        return jsonify({"error": "Context for summary is required"}), 400

    # --- In a real application ---
    # 1. Gather the data related to the context (e.g., from your KG).
    # 2. Format a prompt for your LLM.
    # 3. Return the generated summary from the LLM.

    # Mock response for demonstration
    mock_summary = f"This is a generated summary about '{context}'. Research indicates a significant correlation between prolonged spaceflight and changes in the cardiovascular system. Key factors include fluid shifts and lack of gravitational load."

    return jsonify({"summary": mock_summary})

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