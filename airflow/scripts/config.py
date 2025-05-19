# Cassandra
CASSANDRA_HOST=["cassandra"]
CASSANDRA_PORT="9042"
KEYSPACE="new"
CASSANDRA_TABLE="reddit_posts_by_date"

# Other config
CHECK_INTERVAL=20
PROCESS_LIMIT=50
TRUNCATE_IF_EXISTS=True

# Optional
subreddits = [
    "worldnews", "news", "breakingnews", "inthenews", "nottheonion", "fakenews",
    "usnews", "europe", "ukpolitics", "canada", "china", "india", "middleeast", "africa",
    "science", "technology", "futurology", "space", "climate", "health",
    "geopolitics", "politics", "economics", "conspiracy", "journalism"
]


# Kafka
KAFKA_BOOTSTRAP_SERVERS="kafka:9092"
KAFKA_TOPIC="reddit-posts"
