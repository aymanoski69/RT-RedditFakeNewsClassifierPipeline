from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime
from config import CASSANDRA_PORT ,KEYSPACE , CASSANDRA_TABLE , KAFKA_BOOTSTRAP_SERVERS , KAFKA_TOPIC , CASSANDRA_HOST







# Define schema for incoming data
schema = StructType([
    StructField("title", StringType()),
    StructField("text", StringType()),
    StructField("author", StringType()),
    StructField("source", StringType()),
    StructField("url", StringType()),
    StructField("published_at", StringType()),
    StructField("category", StringType()),
    StructField("subreddit", StringType())   
])


# Create Spark session with Kafka and Cassandra support
spark = SparkSession.builder \
    .appName("NewsAPIFakeNewsClassifier") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
            "com.datastax.spark:spark-cassandra-connector_2.12:3.4.1") \
    .config("spark.cassandra.connection.host", CASSANDRA_HOST[0]) \
    .config("spark.cassandra.connection.port", CASSANDRA_PORT) \
    .getOrCreate()


# Read from Kafka topic
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "latest") \
    .load()


# Parse JSON from Kafka 'value', extract fields and prepare dataframe
processed_df = df.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*").withColumn(
    "post_id", 
    when(col("url").isNull(), md5(concat(col("title"), col("text"))))
    .otherwise(col("url"))
).withColumn(
    "created_utc",
    when(col("published_at").isNull(), current_timestamp())
    .otherwise(to_timestamp(col("published_at"), "yyyy-MM-dd'T'HH:mm:ss'Z'"))
).withColumn(
    "post_date", to_date(col("created_utc"))
).withColumn(
    "post_time", col("created_utc")
).withColumn(
    "subreddit", coalesce(col("subreddit"), lit("unknown"))  
).withColumn(
    "upvotes", lit(0)
).withColumn(
    "prob_fake", lit(-1.0) 
).select(
    "post_date", "post_time", "post_id", "title", "text",
    "author", "subreddit", "upvotes", "url", "prob_fake"
)



# Write each microbatch to Cassandra
def write_to_cassandra(batch_df, batch_id):
    count = batch_df.count()
    if count > 0:
        batch_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .options(table=CASSANDRA_TABLE, keyspace=KEYSPACE) \
            .mode("append") \
            .save()
        print(f"Wrote {count} records to Cassandra")



# Start streaming query with foreachBatch sink
cassandra_query = processed_df.writeStream \
    .foreachBatch(write_to_cassandra) \
    .outputMode("append") \
    .start()


spark.streams.awaitAnyTermination()
