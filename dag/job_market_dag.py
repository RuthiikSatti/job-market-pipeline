from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from minio import Minio
from datetime import datetime, timedelta
import json

# MinIO Config (Inside Docker network)
MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "bronze"

def load_minio_to_postgres():
    """Fetch files from MinIO and push to PostgreSQL."""
    client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')

    # List all objects in jobs/ folder
    objects = client.list_objects(BUCKET_NAME, prefix='jobs/', recursive=True)

    for obj in objects:
        response = client.get_object(BUCKET_NAME, obj.object_name)
        data = json.loads(response.read().decode('utf-8'))

        pg_hook.run(
            "INSERT INTO bronze.raw_jobs (raw_data) VALUES (%s)",
            parameters=(json.dumps(data),)
        )
        print(f"Loaded {obj.object_name} to PostgreSQL")

default_args = {
    'owner': 'architect',
    'depends_on_past': False,
    'start_date': datetime(2026, 2, 20),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'job_market_ingestion',
    default_args=default_args,
    schedule_interval='@hourly',
    catchup=False
) as dag:

    load_task = PythonOperator(
        task_id='load_jobs_to_postgres',
        python_callable=load_minio_to_postgres
    )
