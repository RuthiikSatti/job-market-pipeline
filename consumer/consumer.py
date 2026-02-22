import json
import os
import time
from kafka import KafkaConsumer
from minio import Minio
from io import BytesIO

# MinIO Client (Matches your Compose file)
MINIO_CLIENT = Minio(
    "localhost:9002",  # Note: Map to API port from compose
    access_key="admin",
    secret_key="password123",
    secure=False
)

BUCKET = "bronze"
if not MINIO_CLIENT.bucket_exists(BUCKET):
    MINIO_CLIENT.make_bucket(BUCKET)

# Kafka Consumer - Listening on host port 29092
consumer = KafkaConsumer(
    'realtime_jobs',
    bootstrap_servers=['localhost:29092'],
    auto_offset_reset='earliest',  # Gets all data from the beginning
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("👂 Consumer listening for jobs in Kafka...")

for message in consumer:
    data = message.value
    # Grouping by date for organization
    current_date = time.strftime('%Y-%m-%d')
    filename = f"jobs/{current_date}/job_{data['job_id']}.json"

    content = json.dumps(data).encode('utf-8')

    MINIO_CLIENT.put_object(
        BUCKET,
        filename,
        data=BytesIO(content),
        length=len(content),
        content_type='application/json'
    )
    print(f"💾 Saved to MinIO: {filename}")
