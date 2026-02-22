import os, requests, json, time
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()
producer = KafkaProducer(
    bootstrap_servers=['localhost:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"

def stream_job_data():
    params = {
        'app_id': APP_ID, 'app_key': APP_KEY,
        'results_per_page': 50,
        'what': 'data engineer analyst',
        'content-type': 'application/json'
    }
    print(f"🚀 {time.strftime('%H:%M:%S')} - Fetching data...")
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        jobs = response.json().get('results', [])
        for job in jobs:
            event = {
                'job_id': str(job.get('id')),
                'title': job.get('title'),
                'company': job.get('company', {}).get('display_name'),
                'salary': job.get('salary_min'),
                'location': job.get('location', {}).get('display_name'),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            producer.send('realtime_jobs', value=event)
        producer.flush()
        print(f"✅ Streamed {len(jobs)} jobs.")
    else:
        print(f"❌ Error {response.status_code}")

if __name__ == "__main__":
    while True:  # THIS IS THE CONTINUOUS LOOP
        stream_job_data()
        print("⏳ Sleeping for 30 minutes...")
        time.sleep(1800)
