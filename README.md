THIS PROJECT STILL NEEDS SOME FINAL TOUCHs , BUT IT S WORKING 

-------------------------------------------------------------
FIRST: you need to download my Fakenewsclassifier model from kaggle : https://www.kaggle.com/models/lambarkiaymane/fakenewsclassifier

--->Then put the folder 'final_model' in airflow/scripts/

--->Then just build and run the docker-compose
(localHost port 8081:8080 to check the airflow web services)
--------------------------------------------------------------

⚠️WARNNING : you need to create your own dashboard in grafana at port "3000:3000"
and install the plugging for Cassandra.


Need to use your own reddit api credentiales





---

# Real-Time Fake News Detection on Reddit:

## A Modular Data Pipeline using Kafka, Spark, Cassandra, and Transformers

**Authors:** Lambarki Aymane, Bassa Mohamed
**Date:** *(today's date or project date)*

---

## Credits

This work was carried out by **Lambarki Aymane** and **Bassa Mohamed**, under the supervision of **Madame Zaidouni**.
It represents a capstone data engineering project showcasing real-time data ingestion, processing, and machine learning integration.

---

## Introduction

In the digital era, social media platforms have become primary sources of information. However, they are also vulnerable to the spread of misinformation and fake news. This project presents a modular, real-time data pipeline that detects fake news on Reddit. It integrates modern data engineering and machine learning tools to enable scalable ingestion, processing, classification, and visualization of Reddit data.

---

## Pipeline Overview

The pipeline is composed of several key components:

* **Reddit Producer:** Fetches Reddit posts using the Reddit API (PRAW).
* **Kafka Broker:** Acts as a message queue to handle streaming data.
* **Spark Consumer:** Processes and transforms the data before storing it.
* **Cassandra:** A NoSQL database for storing structured Reddit data.
* **Classification Service:** Applies a fine-tuned Transformer model (DistilRoBERTa) to detect fake news.
* **Airflow:** Orchestrates the end-to-end workflow.
* **Docker Compose:** Containerizes and connects all services.

---

## Reddit API Integration

The Reddit producer uses the `PRAW` (Python Reddit API Wrapper) library to connect to Reddit via OAuth2. The producer fetches posts based on predefined subreddits or keywords.

### Authentication

* Requires `client_id`, `client_secret`, and `user_agent`.
* Supports different scopes such as `read`, `submit`, and `identity`.

### Data Retrieved

* Post title, text (selftext), author, subreddit, upvotes, number of comments, timestamp.

### Streaming to Kafka

Each post is serialized as JSON and pushed to a Kafka topic named `reddit-posts`.

---

## Apache Kafka: Streaming Backbone

Kafka acts as the central messaging system to decouple data ingestion and processing.

### How Kafka Works

Kafka maintains topics partitioned across brokers. Producers write messages to a topic, and consumers read from it asynchronously.

### Producer-Consumer Setup

* **Producer:** Reddit script using `kafka-python`.
* **Consumer:** Spark Structured Streaming job.

### Docker Integration

Kafka is deployed with Zookeeper in Docker. Internal communication uses port 9092.

* **Monitoring and Logging:** Kafdrop UI allows tracking the status of Kafka topics and individual message flows.

---

## Apache Spark: Processing Layer

Spark Structured Streaming reads real-time data from Kafka, cleans and processes it.

### Kafka to Spark

* Spark session uses `readStream` with Kafka source.
* JSON values are deserialized and converted into structured DataFrames.

### Data Transformation

* Clean text using regex.
* Compute features: readability, word count, capitalization ratio.

---

## Cassandra: Scalable Storage

Apache Cassandra serves as the distributed, fault-tolerant database for storing the enriched Reddit posts. Its decentralized architecture allows for high availability and horizontal scalability, which makes it well-suited for handling streaming data workloads from Spark.

### Why Cassandra?

* **High Write Throughput:** Ideal for ingest-heavy applications like real-time Reddit pipelines.
* **Decentralized Design:** No single point of failure, ensuring continuous availability.
* **Time-series Friendly:** Efficient for storing timestamped post data.
* **Integration:** Native support via the `spark-cassandra-connector`.

### Integration with Spark

Spark Structured Streaming connects to Cassandra using the `spark-cassandra-connector` package. The connection parameters, including Cassandra host and port, are configured through Spark's session builder.

The `writeStream.foreachBatch()` method is used to write micro-batches of processed Reddit posts to Cassandra using the DataFrame API.

### Schema Design

The data is written to the Cassandra table `reddit.posts`.

### Write Logic

The write logic is defined in a `write_to_cassandra()` function. It checks if the micro-batch is non-empty and then appends the records to Cassandra.

This function is passed to the Spark Structured Streaming engine using:

```python
processed_df.writeStream \
    .foreachBatch(write_to_cassandra) \
    .outputMode("append") \
    .start()
```

### Post ID Logic

Each post is uniquely identified by a `post_id`. If the post includes a URL, it's used directly; otherwise, a hash of the title and text is generated:

```python
.withColumn("post_id", 
    when(col("url").isNull(), md5(concat(col("title"), col("text"))))
    .otherwise(col("url"))
)
```

---

## Fake News Classification

A separate service reads unclassified posts from Cassandra and classifies them using a Transformer model.

### Model

* **Model:** Fine-tuned `distilroberta-base`.
* **Features:** Text + handcrafted features.
* **Output:** Probability of being fake + label.

To learn more about the model, check:

* [Kaggle Notebook: Fake News Classifier](https://www.kaggle.com/code/lambarkiaymane/fakenewsclassifermodel)
* [Kaggle Model Page](https://www.kaggle.com/models/lambarkiaymane/fakenewsclassifier)

### Workflow

The classification service is responsible for inferring the probability that a Reddit post is fake news using a fine-tuned transformer model. This component runs as a separate Python script or service that interacts directly with Cassandra.

* **Querying Unlabeled Posts:** The service queries the `reddit.posts` table to retrieve entries where the `prob_fake` column is `NULL` or `-1.0`, indicating that the post has not yet been processed by the classifier. This is achieved using the Cassandra Python driver (`cassandra-driver`):

```sql
SELECT post_id, title, text FROM reddit.posts 
WHERE prob_fake = -1.0 ALLOW FILTERING;
```

* **Text Preprocessing:** Each post's title and text are preprocessed before inference. This may include:

  * Lowercasing
  * Removing special characters and excessive punctuation
  * Tokenization and truncation to a maximum sequence length

* **Model Inference:** The preprocessed inputs are passed through a fine-tuned `distilroberta-base` model. The model outputs a probability score (`prob_fake`) representing how likely the post is to be fake news:

```python
prob_fake = sigmoid(classifier([text, features]))
```

A binary prediction is derived using a threshold (e.g., 0.5):

```python
prediction = prob_fake > 0.5
```

* **Updating Cassandra:** For each processed post, the service writes back the `prob_fake` and `prediction` fields into the original Cassandra row. This ensures the post won't be reclassified again during future runs.

---

## Apache Airflow: Orchestration

Apache Airflow orchestrates the full data pipeline by defining and managing a Directed Acyclic Graph (DAG). Each node in the DAG represents a discrete task in the pipeline, ensuring proper execution order, fault tolerance, and monitoring capabilities.

### DAG Structure and Task Dependencies

The DAG defines the following four main tasks:

1. `PipeLine_Init_.py` – Initializes the environment by checking the health and connectivity of key components including Kafka, Cassandra, and Spark. A failure in this step prevents downstream tasks from executing.

2. `SparkConsumer.py` – Starts the Spark Structured Streaming job that reads data from the Kafka topic (`reddit-posts`), applies transformations, and writes the processed records to Cassandra.

3. `classification.py` – Queries unlabeled records (`prob_fake = -1.0`), performs text preprocessing, computes additional features, and uses a fine-tuned `distilroberta-base` model to predict the probability of fake news. Writes results back into Cassandra.

4. `Reddit_Producer.py` – Connects to Reddit using the `PRAW` library and retrieves fresh posts based on specified subreddits or keywords. Posts are serialized to JSON and pushed to Kafka.

---


