import praw
from kafka import KafkaProducer
import os 
import json
import time
import re
from config import   KAFKA_BOOTSTRAP_SERVERS , KAFKA_TOPIC , subreddits






# Reddit API credentials

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

reddit = praw.Reddit(
    client_id= REDDIT_CLIENT_ID ,
    client_secret= REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)



# Kafka producer configuration
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)




# Track seen posts to avoid duplicates
seen_posts = set()

# basic text cleaner
def clean_text(text):
    text = re.sub(r'http\S+', '', text)  
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)  
    text = re.sub(r'[^\w\s.,!?\'\"-]', '', text)  
    return text.strip()

def fetch_posts():
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        

        for post in subreddit.new(limit=10):
            if post.id in seen_posts:
                continue

            # Only use body text
            body = clean_text(post.selftext or "")
            title= clean_text(post.title or "") 

            
            

            post_data = {
                "id": post.id,
                "title": title,
                "text": body,  
                "author": str(post.author),
                "subreddit": subreddit_name,
                "upvotes": post.score,
                "url": post.url,
                "created_utc": post.created_utc,
                "is_self": post.is_self,
                "num_comments": post.num_comments,
            }

            # Send to Kafka topic
            producer.send(KAFKA_TOPIC, post_data)
            seen_posts.add(post.id)
            

        time.sleep(2)  

if __name__ == "__main__":
    
    while True:
        fetch_posts()
        time.sleep(60)  
