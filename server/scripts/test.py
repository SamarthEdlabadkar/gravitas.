import sqlite3

# Connect to the database (creates it if not exists)
conn = sqlite3.connect("server/static/papers.db")
cursor = conn.cursor()

# Example query: select title and classification
cursor.execute("SELECT title, classification FROM classifications")

# Fetch all results
rows = cursor.fetchall()

# Display results
for row in rows:
    title, classification = row
    print(f"Title: {title}\nClassification: {classification=}\n")

# Close connection
conn.close()
