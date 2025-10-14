"""sqlite_classifications_to_mongo.py

Read rows from a SQLite3 `classifications` table and upsert into MongoDB.

Expected table schema:
  - id INTEGER PRIMARY KEY
  - title TEXT
  - classification TEXT (JSON array or comma-separated string)

This script is minimal and uses environment variables:
  - MONGO_URI (default mongodb://localhost:27017)
  - MONGO_DB (default medosearch)
  - MONGO_COLLECTION (default classifications)
  - SQLITE_PATH (path to sqlite file, default server/static/chroma/chroma.sqlite3)
"""

from typing import List, Dict, Any
import os
import json
import sqlite3

from pymongo import MongoClient, UpdateOne
import dotenv

dotenv.load_dotenv()

SQLITE_PATH = os.environ.get('SQLITE_PATH', 'server/static/papers.db')
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB = os.environ.get('MONGO_DB', 'medosearch')
MONGO_COLLECTION = os.environ.get('MONGO_COLLECTION', 'classifications')


def parse_classification(value: Any) -> List[str]:
    """Parse classification field: accept JSON arrays, comma-separated strings, or already-lists."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode('utf-8')
        except Exception:
            value = str(value)

    if isinstance(value, str):
        s = value.strip()
        # try JSON first
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass

        # fallback: comma-separated
        parts = [p.strip() for p in s.split(',') if p.strip()]
        return parts

    # fallback
    return [str(value)]


def read_sqlite_rows(sqlite_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"SQLite file not found: {sqlite_path}")

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, title, classification FROM classifications")
    rows = []
    for r in cur.fetchall():
        rows.append({
            'id': r['id'],
            'title': r['title'],
            'classification': parse_classification(r['classification'])
        })

    conn.close()
    return rows


def upsert_rows(mongo_uri: str, db_name: str, collection_name: str, rows: List[Dict[str, Any]]) -> int:
    client = MongoClient(mongo_uri)
    coll = client[db_name][collection_name]
    ops = []
    count = 0
    for r in rows:
        _id = r.get('id')
        if _id is None:
            continue
        doc = {
            'title': r.get('title'),
            'classification': r.get('classification')
        }
        ops.append(UpdateOne({'_id': _id}, {'$set': doc}, upsert=True))
        if len(ops) >= 500:
            res = coll.bulk_write(ops)
            count += res.upserted_count + res.modified_count
            ops = []

    if ops:
        res = coll.bulk_write(ops)
        count += res.upserted_count + res.modified_count

    client.close()
    return count


def main():
    rows = read_sqlite_rows(SQLITE_PATH)
    print(f"Read {len(rows)} rows from {SQLITE_PATH}")
    count = upsert_rows(MONGO_URI, MONGO_DB, MONGO_COLLECTION, rows)
    print(f"Upserted/modified approx {count} docs into {MONGO_DB}.{MONGO_COLLECTION}")


if __name__ == '__main__':
    main()
