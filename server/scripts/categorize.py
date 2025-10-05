import os
from time import sleep
from groq import Groq
import instructor

from pydantic import BaseModel, Field
from typing import Dict, List, Any
from dotenv import load_dotenv

import json
import csv
import sqlite3

topics = [
    "Musculoskeletal System and Biomechanics",
    "Cardiovascular and Vascular Health",
    "Radiation Biology and DNA Damage",
    "Neuroscience and Sensory Systems",
    "Plant Gravitropism and Development",
    "Microbiology and Host-Microbe Interactions",
    "Genomics, Omics, and Data Science",
    "Cellular Stress and Homeostasis",
    "Immunity and Hematology",
    "Unique Biological Adaptations and Models"
]

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

client = instructor.from_groq(client, mode=instructor.Mode.JSON)

# Define the structured output schema
class PaperClassification(BaseModel):
    selected_categories: List[str] = Field(
        ...,
        description="A list of all relevant categories chosen from the provided 10 options."
    )
    reasoning: str = Field(
        ...,
        description="Short explanation for why these categories were selected."
    )

# Define the classification function
def classify_paper(title: str, abstract: str) -> PaperClassification | Any:
    prompt = f"""
You are a NASA space biology paper classifier.
Given the title and abstract of a scientific paper, select ALL relevant categories
from the following list:

{chr(10).join([f"{i+1}. {c}" for i, c in enumerate(topics)])}

Return your answer as JSON with keys:
- "selected_categories": array of category names
- "reasoning": short explanation

TITLE: {title}
ABSTRACT: {abstract}
"""
    # Use Instructor to enforce schema validation
    result = client.chat.completions.create(
        model='llama-3.1-8b-instant',  # currently working - llama-3.3-70b-versatile, llama3-8b-8192
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_retries=3,
        response_model=PaperClassification
    ) # type:ignore
    return result

# Database file
DB_FILE = "server/static/papers.db"

# Initialize connection
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Create table if it doesn’t exist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS classifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT UNIQUE,
        classification JSON
    )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized and table ensured.")

# Insert classification data
def store_classification(title: str, classification: Dict[str, Any]):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Convert classification dict to JSON string
    classification_json = json.dumps(classification, ensure_ascii=False)

    # Insert or replace (so you can reclassify a paper without duplicates)
    cur.execute("""
    INSERT INTO classifications (title, classification)
    VALUES (?, ?)
    ON CONFLICT(title) DO UPDATE SET classification = excluded.classification
    """, (title, classification_json))

    conn.commit()
    conn.close()
    print(f"✅ Stored classification for: {title}")

def read_columns(csv_file, col3_index=2, col7_index=6):
    """
    Reads only columns 3 and 7 (0-based index: 2 and 6) from a CSV file.
    Returns a list of tuples: (col3_value, col7_value)
    """
    results = []

    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        headers = next(reader)  # skip header row

        for row in reader:
            # Handle missing columns gracefully
            if len(row) > max(col3_index, col7_index):
                col3 = row[col3_index].strip()
                col7 = row[col7_index].strip()
                results.append((col3, col7))
    
    return results


# Example usage
if __name__ == "__main__":
    data = read_columns("server/static/data_pubmed.csv")
    init_db()

    for idx, (title, abstract) in enumerate(data[406:]):
        print(idx+406)
        try:
            classification = classify_paper(title, abstract)
            classification_result = classification.model_dump()["selected_categories"]
            store_classification(title, classification_result)
        except Exception as e:
            print(e)

        if (idx+178) % 25 == 0:
            sleep(40)