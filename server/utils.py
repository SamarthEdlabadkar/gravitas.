import math
import os
from typing import List, cast

import google.generativeai as genai

import dotenv
dotenv.load_dotenv()

# Embedding function using Google Gemini via google-generativeai SDK
def generate_embeddings(query: str) -> List[float]:
    """Embed a single query string (RAG-friendly, simple path).

    - Uses google.generativeai with model "models/gemini-embedding-001".
    - Returns a list[float] embedding; returns [] on failure or empty input.
    """
    # Fast no-op for blank inputs
    if not query or not query.strip():
        return []

    api_key = os.getenv("GEMINI_API_KEY")
    model_dim = int(os.getenv("GEMINI_EMBEDDING_DIM", 2560))
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment")

    model_name = "models/gemini-embedding-001"
    genai.configure(api_key=api_key)  # type: ignore[attr-defined]

    try:
        resp = genai.embed_content(model=model_name, content=query.strip(), output_dimensionality=model_dim)  # type: ignore[attr-defined]
        # Expected shape: { "embedding": { "values": [...] } }
        emb = resp.get("embedding") or {}
        vec = emb.get("values") if isinstance(emb, dict) else emb
        if not isinstance(vec, list):
            return []
        return cast(List[float], vec)
    except Exception as e:
        print(f" Error generating embedding for query (len={len(query)}): {e}")
        return []

# helper: cosine similarity
def cosine_similarity(a, b):
    if a is None or b is None:
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return -1.0
    return dot / (norm_a * norm_b)
