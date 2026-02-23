# Job Market Pipeline

A real-time data engineering pipeline that continuously collects job listings from the Adzuna API, streams them through Kafka, stores raw data in MinIO, loads into Snowflake, and transforms it using dbt — following the **Bronze → Silver → Gold** medallion architecture.

---

## Architecture

```
EVERY 30 MINUTES:

  Adzuna API
      │  50 job listings (JSON)
      ▼
  producer.py ──► Kafka (topic: realtime_jobs) ──► consumer.py
                                                         │
                                                         ▼
                                                  MinIO (bronze bucket)
                                               jobs/YYYY-MM-DD/job_<id>.json
                                                         │
                                              scheduler.py (every 10 min)
                                                         ▼
                                               Snowflake BRONZE.RAW_JOBS
                                                         │
                                                      dbt run
                                                         ▼
                                            Silver: cleaned + deduplicated
                                                         │
                                                         ▼
                                            Gold: top paying companies
```

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Data Source | Adzuna API | Live job listings |
| Streaming | Apache Kafka + Zookeeper | Message queue between producer and consumer |
| Kafka UI | Kafdrop | Visual inspection of Kafka topics |
| Raw Storage | MinIO (S3-compatible) | Bronze layer — stores raw JSON files |
| Data Warehouse | Snowflake | SQL analytics on job data |
| Scheduling | scheduler.py | Runs MinIO → Snowflake every 10 minutes |
| Transformation | dbt (dbt-snowflake) | Silver and Gold layer SQL models |
| Infrastructure | Docker + Docker Compose | Runs Kafka, Zookeeper, Kafdrop, MinIO locally |

---

## Prerequisites

- **Python 3.12** (required — newer versions have compatibility issues with kafka-python and snowflake-connector)
- **Docker Desktop** installed and running
- **Snowflake account** (free trial works)
- **Adzuna API credentials** — register free at https://developer.adzuna.com

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/RuthiikSatti/job-market-pipeline.git
cd job-market-pipeline
```

### 2. Create a virtual environment with Python 3.12

```bash
# Windows
py -3.12 -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your environment variables

Copy the example file and fill in your credentials:

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Then open `.env` and fill in your values:

```
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password123
SNOWFLAKE_USER=your_snowflake_username
SNOWFLAKE_PASSWORD=your_snowflake_password
SNOWFLAKE_ACCOUNT=your_account_id.region.aws
```

> **Note:** `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` match the values in `docker/docker-compose.yml`. Only change them if you update the compose file too.

---

### 5. Set up Snowflake

Log into your Snowflake account and run the following SQL to create the required database, schema, and table:

```sql
-- Create database and schemas
CREATE DATABASE JOB_MARKET_DB;
CREATE SCHEMA JOB_MARKET_DB.BRONZE;

-- Create the raw jobs table (stores JSON as a VARIANT column)
CREATE TABLE JOB_MARKET_DB.BRONZE.RAW_JOBS (
    raw_data VARIANT
);
```

---

### 6. Set up dbt

Navigate into the dbt project and set up your profile:

```bash
cd dbt_jobs
```

Create a dbt profile file at `~/.dbt/profiles.yml` (outside the repo):

```yaml
dbt_jobs:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: your_account_id.region.aws
      user: your_snowflake_username
      password: your_snowflake_password
      role: ACCOUNTADMIN
      database: JOB_MARKET_DB
      warehouse: COMPUTE_WH
      schema: SILVER
      threads: 1
```

Test the connection:

```bash
dbt debug
```

---

## Running the Pipeline

Open **4 separate terminals**, activate the venv in each, then run:

### Terminal 1 — Start Docker services

```bash
docker-compose -f docker/docker-compose.yml up -d
```

Verify all 4 containers are running:

```bash
docker ps
```

You should see: `zookeeper`, `kafka`, `kafdrop`, `minio`

### Terminal 2 — Start the Producer (Adzuna → Kafka)

```bash
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Mac/Linux

python producer/producer.py
```

Expected output:
```
🚀 13:00:00 - Fetching data...
✅ Streamed 50 jobs.
⏳ Sleeping for 30 minutes...
```

### Terminal 3 — Start the Consumer (Kafka → MinIO)

```bash
.venv\Scripts\activate
python consumer/consumer.py
```

Expected output:
```
👂 Consumer listening for jobs in Kafka...
💾 Saved to MinIO: jobs/2026-02-23/job_12345.json
💾 Saved to MinIO: jobs/2026-02-23/job_12346.json
...
```

### Terminal 4 — Start the Scheduler (MinIO → Snowflake, every 10 min)

```bash
.venv\Scripts\activate
python scheduler.py
```

Expected output:
```
⏰ 13:00:05 - Moving MinIO data to Snowflake...
✅ Pushed to Snowflake: jobs/2026-02-23/job_12345.json
🏁 Finished. Total rows pushed: 50
⏳ Waiting 10 minutes for next cycle...
```

---

## Running dbt Transformations

Once data is in Snowflake, run dbt to build the Silver and Gold layers:

```bash
cd dbt_jobs
dbt run
```

This creates two tables in Snowflake:
- `SILVER.job_data_silver` — cleaned, typed, deduplicated jobs
- `GOLD.top_paying_companies` — companies ranked by average salary

To verify:

```bash
dbt test
```

---

## Monitoring UIs

| UI | URL | What it shows |
|---|---|---|
| Kafdrop (Kafka) | http://localhost:9000 | Messages in the `realtime_jobs` topic |
| MinIO Console | http://localhost:9001 | Raw JSON files in the bronze bucket |

MinIO login: `admin` / `password123`

---

## Project Structure

```
job-market-pipeline/
├── producer/
│   └── producer.py          # Fetches from Adzuna API → publishes to Kafka
├── consumer/
│   └── consumer.py          # Reads from Kafka → saves to MinIO
├── dag/
│   └── job_market_dag.py    # Airflow DAG (reference only)
├── dbt_jobs/
│   ├── dbt_project.yml
│   └── models/
│       ├── sources.yml
│       ├── silver/
│       │   └── job_data_silver.sql    # Clean + deduplicate
│       └── gold/
│           └── top_paying_companies.sql  # Business insights
├── docker/
│   └── docker-compose.yml   # Kafka, Zookeeper, Kafdrop, MinIO
├── manual_bridge.py         # One-time MinIO → Snowflake load
├── scheduler.py             # Runs manual_bridge.py every 10 minutes
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── .gitignore
```

---

## Querying the Data in Snowflake

After dbt runs, you can query the Gold layer directly in Snowflake:

```sql
-- Top paying companies
SELECT * FROM JOB_MARKET_DB.GOLD.TOP_PAYING_COMPANIES
ORDER BY average_min_salary DESC
LIMIT 20;

-- All cleaned job listings
SELECT job_title, company_name, min_salary, full_location
FROM JOB_MARKET_DB.SILVER.JOB_DATA_SILVER
ORDER BY ingestion_time DESC;
```

---

## Notes

- `.env` is intentionally excluded from the repo — never commit real credentials
- `data/` and `logs/` folders are also gitignored — they are generated at runtime
- The `dag/` folder contains an Airflow DAG for reference; actual scheduling is handled by `scheduler.py`
- Python 3.12 is required — `kafka-python` and `snowflake-connector-python` have known issues with Python 3.13+
