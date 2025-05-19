# main_script.py
from cassandra.cluster import Cluster
import pandas as pd
import time
import os
from datetime import datetime
from model_handler import FakeNewsDetector  
from config import CASSANDRA_HOST , KEYSPACE ,CHECK_INTERVAL ,PROCESS_LIMIT


MODEL_PATH = os.path.abspath("/opt/airflow/scripts/final_model")


# Initialize model and Cassandra
detector = FakeNewsDetector(MODEL_PATH)
cluster = Cluster(CASSANDRA_HOST)
session = cluster.connect(KEYSPACE)




# Prepare the update statement
update_stmt = session.prepare("""
    UPDATE reddit_posts_by_date
    SET prob_fake = ?,
        prediction = ?,
        last_checked = toTimestamp(now())
    WHERE post_date = ?
    AND post_time = ?
    AND post_id = ?
""")



def get_recent_posts_today():
    """Get recent posts from today with all needed columns"""
    today = datetime.utcnow().date()
    rows = session.execute("""
        SELECT post_id, title, text, prob_fake, post_time 
        FROM reddit_posts_by_date
        WHERE post_date = %s
        LIMIT %s
    """, (today, PROCESS_LIMIT * 3))
    return pd.DataFrame(list(rows))



def process_posts():
    
    data = get_recent_posts_today()
    if data.empty:
        print("No recent posts found")
        return 0
    
    # Filter for unclassified posts (-1.0 or NULL)
    unclassified = data[data['prob_fake'].isin([None, -1.0])].head(PROCESS_LIMIT)
    if unclassified.empty:
        print("No unclassified posts in recent batch")
        return 0
    
    # Classify posts
    unclassified['combined_text'] = unclassified['title'].fillna('') + " " + unclassified['text'].fillna('')
    unclassified['prob_fake'] = unclassified['combined_text'].apply(detector.classify_text)
    unclassified = unclassified.dropna(subset=['prob_fake'])
    unclassified['prediction'] = unclassified['prob_fake'].apply(detector.get_prediction)
    
    # Update Cassandra
    today = datetime.utcnow().date()
    for _, row in unclassified.iterrows():
        try:
            # Ensure post_time is in correct format
            post_time = row['post_time']
            if isinstance(post_time, str):
                post_time = datetime.strptime(post_time, "%Y-%m-%d %H:%M:%S")
            
            session.execute(update_stmt, (
                float(row.prob_fake),
                row.prediction,
                today,
                post_time,
                row.post_id
            ))
        except Exception as e:
            print(f"Error updating post {row.post_id}: {str(e)}")
            print(f"Post time value: {row['post_time']} (type: {type(row['post_time'])})")
            continue
    
    return len(unclassified)

def continuous_classification():
    print("Starting classification service for time-based table...")
    try:
        while True:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{now}] Processing...")
            
            processed = process_posts()
            print(f"Successfully classified {processed} posts")
            
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping service...")
    finally:
        cluster.shutdown()

if __name__ == "__main__":
    continuous_classification()