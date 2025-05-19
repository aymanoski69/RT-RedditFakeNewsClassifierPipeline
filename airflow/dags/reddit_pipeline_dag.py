from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 5, 16),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='reddit_fake_news_pipeline',
    default_args=default_args,
    schedule_interval='0 */6 * * *',  # ⏱ Run every 6 hours
    catchup=False,
    description='Reddit → Kafka → Spark → Classifier pipeline',
) as dag:

    init_pipeline = BashOperator(
        task_id='initialize_pipeline',
        bash_command='python /opt/airflow/scripts/PipeLine_Init_.py',
            
    )

    start_spark_consumer = BashOperator(
        task_id='run_spark_consumer',
        bash_command='python /opt/airflow/scripts/SparkConsumer.py',
        
    )

    run_classification = BashOperator(
        task_id='run_classification',
        bash_command='sleep 10 && python /opt/airflow/scripts/classification.py',
    )

    run_reddit_producer = BashOperator(
        task_id='run_reddit_producer',
        bash_command='sleep 20 && python /opt/airflow/scripts/Reddit_Producer.py',
    )
    

    # Define task dependencies  
    init_pipeline >> [start_spark_consumer , run_classification , run_reddit_producer]

    