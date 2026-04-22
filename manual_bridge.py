import os
import json
from minio import Minio
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# MinIO Config
client = Minio("localhost:9002", access_key="admin", secret_key="password123", secure=False)
BUCKET = "bronze"

# PostgreSQL Config
conn = psycopg2.connect(
    host=os.getenv('PG_HOST', 'localhost'),
    port=int(os.getenv('PG_PORT', 5432)),
    dbname=os.getenv('PG_DB', 'job_market_db'),
    user=os.getenv('PG_USER', 'postgres'),
    password=os.getenv('PG_PASSWORD', 'postgres')
)
cursor = conn.cursor()

def push_to_postgres():
    print("Connecting to MinIO...")
    # List all objects recursively to find jobs inside date folders
    objects = client.list_objects(BUCKET, recursive=True)

    count = 0
    for obj in objects:
        if obj.object_name.endswith('.json'):
            print(f"Processing {obj.object_name}...")
            response = client.get_object(BUCKET, obj.object_name)
            data = json.loads(response.read().decode('utf-8'))

            try:
                cursor.execute(
                    "INSERT INTO bronze.raw_jobs (raw_data) VALUES (%s)",
                    (json.dumps(data),)
                )
                count += 1
                print(f"Pushed to PostgreSQL: {obj.object_name}")
            except Exception as e:
                print(f"PostgreSQL Error: {e}")
                conn.rollback()

    conn.commit()
    print(f"Finished. Total rows pushed: {count}")

if __name__ == "__main__":
    push_to_postgres()
    cursor.close()
    conn.close()
