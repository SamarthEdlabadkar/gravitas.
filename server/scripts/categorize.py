#from bertopic import BERTopic
import csv
import pandas as pd

with open('server/static/publications.csv', mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)  # Automatically reads headers
    docs = []
    for row in reader:
        title = row['Title']
        link = row['Link']

        docs.append(title)

# # Create and fit the model
# topic_model = BERTopic(language="english")
# topics, probs = topic_model.fit_transform(docs)

# # Get an overview of topics
# print(topic_model.get_topic_info())

# # Show top keywords for topic 1
# topic_model.get_topic(1)

# topic_model.visualize_topics()

df = pd.DataFrame({
    "Document": docs,
    #"Topic": topics
})
df.to_csv("server/static/space_biology_topics.csv", index=False)