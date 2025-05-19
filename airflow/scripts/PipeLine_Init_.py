from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from kafka.admin import KafkaAdminClient, NewTopic
from config import CASSANDRA_HOST , KEYSPACE , CASSANDRA_TABLE , KAFKA_BOOTSTRAP_SERVERS , KAFKA_TOPIC
import os 




TRUNCATE_IF_EXISTS = True  



#cassandra connection : 

cluster = Cluster(CASSANDRA_HOST)

session = cluster.connect()


# Create keyspace if it doesn't exist
session.execute(f"""
CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': '1'}}
""")


session.set_keyspace(KEYSPACE)

# Create table if it doesn't exist
session.execute(f"""
CREATE TABLE IF NOT EXISTS {CASSANDRA_TABLE} (
    post_date date,
    post_time timestamp,
    post_id text,
    author text,
    last_checked timestamp,
    prediction text,
    prob_fake float,
    subreddit text,
    text text,
    title text,
    upvotes int,
    url text,
    PRIMARY KEY (post_date, post_time, post_id)
)
WITH CLUSTERING ORDER BY (post_time DESC, post_id ASC)
AND bloom_filter_fp_chance = 0.01
AND caching = {{'keys': 'ALL', 'rows_per_partition': 'NONE'}}
AND cdc = false
AND comment = ''
AND compaction = {{'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy', 'max_threshold': '32', 'min_threshold': '4'}}
AND compression = {{'chunk_length_in_kb': '16', 'class': 'org.apache.cassandra.io.compress.LZ4Compressor'}}
AND crc_check_chance = 1.0
AND default_time_to_live = 0
AND gc_grace_seconds = 864000
AND max_index_interval = 2048
AND memtable_flush_period_in_ms = 0
AND min_index_interval = 128
AND speculative_retry = '99p';
""")

# Truncate table to start fresh
if TRUNCATE_IF_EXISTS:
    session.execute(f"TRUNCATE {CASSANDRA_TABLE};")
    print(f"Truncated table `{CASSANDRA_TABLE}` in keyspace `{KEYSPACE}`")

# Close connection
cluster.shutdown()
print("Cassandra initialization complete.")





admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

topic_list = [NewTopic(name=KAFKA_TOPIC, num_partitions=3, replication_factor=1)]
try:
    admin_client.create_topics(new_topics=topic_list, validate_only=False)
    print(f"✅ Topic '{KAFKA_TOPIC}' created.")
except Exception as e:
    print(f"⚠️ Topic '{KAFKA_TOPIC}' may already exist or error occurred: {e}")
