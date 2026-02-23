import os
import json
from minio import Minio
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

# MinIO Config
client = Minio("localhost:9002", access_key="admin", secret_key="password123", secure=False)
BUCKET = "bronze"

# Snowflake Config
conn = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse='COMPUTE_WH',
    database='JOB_MARKET_DB',
    schema='BRONZE'
)
cursor = conn.cursor()

def push_to_snowflake():
    print("Connecting to MinIO...")
    # List all objects recursively to find jobs inside date folders
    objects = client.list_objects(BUCKET, recursive=True)

    count = 0
    for obj in objects:
        if obj.object_name.endswith('.json'):
            print(f"Processing {obj.object_name}...")
            response = client.get_object(BUCKET, obj.object_name)
            data = json.loads(response.read().decode('utf-8'))

            # Format JSON for SQL insertion
            json_str = json.dumps(data).replace("'", "''")
            sql = f"INSERT INTO RAW_JOBS (raw_data) SELECT PARSE_JSON('{json_str}')"

            try:
                cursor.execute(sql)
                count += 1
                print(f"Pushed to Snowflake: {obj.object_name}")
            except Exception as e:
                print(f"Snowflake Error: {e}")

    # CRITICAL: Save the changes
    conn.commit()
    print(f"Finished. Total rows pushed: {count}")

if __name__ == "__main__":
    push_to_snowflake()
    cursor.close()
    conn.close()
