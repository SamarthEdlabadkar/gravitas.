"""Simple chroma -> mongo exporter

This minimal script reads the ChromaDB persistent store at
`server/static/chroma`, extracts items from the `research_papers`
collection and upserts them into MongoDB at the default
`mongodb://localhost:27017` using a schema matching
`vectorizer_pubmed.py`'s metadata fields.

Run this script directly (no CLI args). Configure Mongo connection via
`MONGO_URI` env var if needed.
"""

from typing import List, Dict, Any

import os

import chromadb
from chromadb.config import Settings
from pymongo import MongoClient, UpdateOne
import dotenv

dotenv.load_dotenv()

CHROMA_PATH = "server/static/chroma"
CHROMA_COLLECTION = "osdr_experiments"
MONGO_URI = os.getenv('MONGODB_URI')
MONGO_DB = os.environ.get('MONGO_DB_NAME', 'Gravitas-DB')
MONGO_COLLECTION = os.environ.get('MONGO_COLLECTION_NAME', 'osdr_experiments')

def iter_collection(client: Any, collection_name: str, batch_size: int = 256) -> List[Dict[str, Any]]:
    collection = client.get_collection(name=collection_name)
    try:
        ids = collection.get()['ids']
    except Exception:
        try:
            ids = collection.list()['ids']
        except Exception as e:
            raise RuntimeError("Unable to list ids from Chroma collection: %s" % e)

    items: List[Dict[str, Any]] = []
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i : i + batch_size]
        result = collection.get(ids=batch_ids, include=['embeddings', 'documents', 'metadatas'])
        for idx, _id in enumerate(result.get('ids', [])):
            items.append({
                'id': _id,
                'embedding': result.get('embeddings', [None])[idx] ,
                'document': result.get('documents', [None])[idx] ,
                'metadata': result.get('metadatas', [None])[idx],
            })

    return items


try:
    import numpy as _np
except Exception:
    _np = None


def _sanitize_for_bson(obj: Any) -> Any:
    """Recursively convert objects not serializable by BSON (e.g. numpy arrays/scalars)
    into Python built-ins (lists, ints, floats, dicts).
    """
    # handle numpy arrays and objects exposing tolist()
    if _np is not None and isinstance(obj, _np.ndarray):
        return _sanitize_for_bson(obj.tolist())

    # objects exposing tolist (but not strings/bytes)
    if not isinstance(obj, (str, bytes, bytearray)) and hasattr(obj, 'tolist'):
        try:
            return _sanitize_for_bson(obj.tolist())
        except Exception:
            pass

    # numpy scalar types (e.g., np.float32)
    if _np is not None:
        if isinstance(obj, (_np.floating, _np.integer, _np.bool_)):
            try:
                return obj.item()
            except Exception:
                pass

    # dict -> sanitize keys and values
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            # ensure key is a string for Mongo
            key = k if isinstance(k, str) else str(k)
            new[key] = _sanitize_for_bson(v)
        return new

    # lists/tuples/sets -> list
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_bson(v) for v in obj]

    # fallback, return as-is
    return obj


def upsert_to_mongo(mongo_uri: str, db_name: str, collection_name: str, items: List[Dict[str, Any]]) -> int:
    client = MongoClient(mongo_uri)
    db = client[db_name]
    coll = db[collection_name]

    ops = []
    count = 0
    for item in items:
        # Map Chroma metadata to the schema used in vectorizer_pubmed.py
        metadata = item.get('metadata') or {}

        osdr_id = metadata.get('osd_id') or item.get('id')
        # skip items without an id
        if not osdr_id:
            continue
        title = metadata.get('title')
        authors = metadata.get('authors')
        link = metadata.get('link')
        embedding = item.get('embeddings')

        # The original vectorizer stored a combined text as document. Keep it if present.
        document = item.get('document')

        doc = {
            '_id': osdr_id,
            'osdr_id': osdr_id,
            'title': title,
            'authors': authors,
            'link': link,
            'document': document,
            'embedding': item.get('embedding'),
            'chroma_id': item.get('id'),
        }
        # Upsert by _id (osdr_id)
        # MongoDB doesn't allow updating the _id field, so remove it from the $set
        set_doc = doc.copy()
        set_doc.pop('_id', None)
        # sanitize values for BSON (convert numpy arrays/scalars, etc.)
        set_doc = _sanitize_for_bson(set_doc)
        ops.append(UpdateOne({'_id': osdr_id}, {'$set': set_doc}, upsert=True))

        if len(ops) >= 500:
            result = coll.bulk_write(ops)
            count += result.upserted_count + result.modified_count
            ops = []

    if ops:
        result = coll.bulk_write(ops)
        count += result.upserted_count + result.modified_count

    client.close()
    return count


def run_export():
    # initialize chromadb persistent client
    try:
        client = chromadb.PersistentClient(CHROMA_PATH)
    except TypeError:
        settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_PATH)
        client = chromadb.Client(settings=settings)

    items = iter_collection(client, CHROMA_COLLECTION, batch_size=256)
    print(f"Exporting from Chroma '{CHROMA_COLLECTION}' at {CHROMA_PATH} to MongoDB {MONGO_URI} {MONGO_DB}.{MONGO_COLLECTION}")

    # print(items[0])

    count = upsert_to_mongo(MONGO_URI, MONGO_DB, MONGO_COLLECTION, items)
    print(f"Done. Upserted/modified approx {count} documents.")


if __name__ == '__main__':
    run_export()

