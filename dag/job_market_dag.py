from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from minio import Minio
from datetime import datetime, timedelta
import json
import os

# MinIO Config (Inside Docker network)
MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
BUCKET_NAME = "bronze"

def load_minio_to_snowflake():
    """Fetch files from MinIO and push to Snowflake."""
    client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
    snowflake_hook = SnowflakeHook(snowflake_conn_id='snowflake_default')

    # List all objects in jobs/ folder
    objects = client.list_objects(BUCKET_NAME, prefix='jobs/', recursive=True)

    for obj in objects:
        # Get the file content
        response = client.get_object(BUCKET_NAME, obj.object_name)
        data = json.loads(response.read().decode('utf-8'))

        # Push to Snowflake
        sql = f"INSERT INTO JOB_MARKET_DB.BRONZE.RAW_JOBS (raw_data) SELECT PARSE_JSON('{json.dumps(data).replace("'", "''")}')"
        snowflake_hook.run(sql)

        # Optional: Delete or move the file in MinIO after success
        print(f"Loaded {obj.object_name} to Snowflake")

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
        task_id='load_jobs_to_snowflake',
        python_callable=load_minio_to_snowflake
    )
