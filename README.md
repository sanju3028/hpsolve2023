# hpsolve2023
#Project done for hp solve 2023 final round

import csv
import tweepy
import re
from textblob import TextBlob
from py2neo import Graph
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Authenticate with Twitter API
consumer_key = "z5Ww3mTPR4YBrZD40q6Kb2TQ4"
consumer_secret = "j55DMW2jkra7ojkQzJBueECsnNGZXKVqhlOJPUSFNmJQ9Gm1o6"
access_token = "848405441851908096-UAaxiujCSi02K2qWYNPNMFwi4AUAeKY"
access_token_secret = "wx6tfVIWsJYfmKae8W2e5YJfu0Yaiwjbt86Ir5HljCwpL"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Create API object
api = tweepy.API(auth)

# Define the HP laptop models and HP printer models
laptop_models = ["HP Spectre", "HP Envy", "HP Pavilion"]
printer_models = ["HP LaserJet", "HP OfficeJet", "HP DeskJet"]

# Combine laptop models and printer models with keywords
keywords = ["HP laptops", "HP printers"] + laptop_models + printer_models

# Create a search query using OR operators
query = " OR ".join(keywords)

# Scrape tweets containing the keywords or hashtags
tweets = tweepy.Cursor(api.search_tweets, q=query, lang="en").items(1000)

# Preprocess and extract data from tweets
data = []
for tweet in tweets:
    # Preprocess the tweet text
    text = tweet.text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)  # Remove URLs
    text = re.sub(r"\@\w+|\#", "", text)  # Remove @ mentions and hashtags
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation

    # Perform sentiment analysis
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    sentiment_label = "Unknown"
    if sentiment > 0:
        sentiment_label = "Appreciation"
    elif sentiment < 0:
        sentiment_label = "Complaint"
    else:
        sentiment_label = "Neutral"

    # Extract the specific phrase or word related to sentiment
    phrase = ""
    if sentiment_label != "Neutral":
        phrase = str(blob.sentences[0])

    # Extract the complaint or feature mentioned in the tweet
    complaint = ""
    feature = ""
    if sentiment_label == "Complaint":
        complaint_keywords = ["problem", "issue", "error", "fault"]
        for keyword in complaint_keywords:
            if keyword in text:
                complaint = keyword
                match = re.search(rf"\b{keyword}\b(.+)", text)
                if match:
                    feature = match.group(1).strip()
                break

    # Tag the tweet with the respective HP product model
    tagged_model = ""
    for model in laptop_models + printer_models:
        if model.lower() in text:
            tagged_model = model
            break

    # Store the tweet data in a dictionary
    tweet_data = {
        "Tweet": tweet.text,
        "TweetLink": f'https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}',
        "user": tweet.user.screen_name,
        "Date": tweet.created_at.date(),
        "Month": tweet.created_at.strftime("%B"),
        "sentiment": sentiment_label,
        "model": tagged_model
    }
    data.append(tweet_data)

# Save the data to a CSV file
csv_filename = "twitter_data.csv"
csv_fields = ["Tweet", "TweetLink", "user", "Date", "Month", "sentiment", "model"]

with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=csv_fields)
    writer.writeheader()
    for tweet_data in data:
        writer.writerow(tweet_data)

print("Data saved to", csv_filename)

# Read the CSV file
df = pd.read_csv(csv_filename)

# Create a directed graph
graph = nx.DiGraph()

# Add nodes and edges to the graph
for _, row in df.iterrows():
    user = row['user']
    model = row['model']
    sentiment = row['sentiment']

    graph.add_node(user)
    graph.add_node(model)
    graph.add_edge(user, model, sentiment=sentiment)

# Visualize the graph
pos = nx.spring_layout(graph, seed=42)
plt.figure(figsize=(10, 8))
nx.draw_networkx(graph, pos, with_labels=True, node_color='lightblue', node_size=800, font_size=10, font_weight='bold', edge_color='gray', alpha=0.7)
edge_labels = nx.get_edge_attributes(graph, 'sentiment')
nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=8)
plt.title("Knowledge Graph")
plt.axis('off')
plt.tight_layout()
plt.show()

# Interactive loop for querying the knowledge graph
while True:
    print("Enter a query:")
    query = input("> ")

    if query == "exit":
        break

    results = []

    # Iterate over the graph nodes and find matching nodes
    for node in graph.nodes:
        if isinstance(node, str) and query.lower() in node.lower():
            related_nodes = [n for n in graph.neighbors(node)]
            for related_node in related_nodes:
                sentiment = graph[node][related_node]['sentiment']
                results.append((node, related_node, sentiment))

    if len(results) > 0:
        print(f"Results for query '{query}':")
        for result in results:
            node1, node2, sentiment = result
            if sentiment == "Complaint":
                print(f"{node1} complains about {node2}")
            elif sentiment == "Appreciation":
                print(f"{node1} appreciates {node2}")
    else:
        print(f"No results found for query '{query}'")
