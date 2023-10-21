import tweepy
import csv
import torch

from transformers import BertTokenizer, BertForSequenceClassification


# Authenticate with Twitter API
consumer_key = "z5Ww3mTPR4YBrZD40q6Kb2TQ4"
consumer_secret = "j55DMW2jkra7ojkQzJBueECsnNGZXKVqhlOJPUSFNmJQ9Gm1o6"
access_token = "848405441851908096-UAaxiujCSi02K2qWYNPNMFwi4AUAeKY"
access_token_secret = "wx6tfVIWsJYfmKae8W2e5YJfu0Yaiwjbt86Ir5HljCwpL"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Create API object
api = tweepy.API(auth)

# Define the keywords to search for
keywords = ["hplaptop", "hpprinter", "hp"]

# Load the pre-trained BERT model and tokenizer
model_name = 'bert-base-uncased'
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertForSequenceClassification.from_pretrained(model_name)

# Set device to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Collect tweets containing the keywords
tweets = []
for keyword in keywords:
    query = keyword + " -filter:retweets"  # Exclude retweets
    new_tweets = api.search_tweets(q=query, lang="en", count=100)
    tweets.extend(new_tweets)

# Store the tweet data in a CSV file
with open("tweets.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["User", "Text", "Sentiment"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for tweet in tweets:
        user = tweet.user.screen_name
        text = tweet.text

        # Tokenize the text and convert to input tensors
        inputs = tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=128,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        inputs = inputs.to(device)

        # Perform sentiment analysis using BERT
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits

        # Classify sentiment based on logits
        sentiment_label = "Positive" if logits[0][1] > logits[0][0] else "Negative"

        # Store the tweet data in the CSV file
        writer.writerow({"User": user, "Text": text, "Sentiment": sentiment_label})
