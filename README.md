# Job Market Pipeline

A data pipeline that pulls job listings from the Adzuna API every 30 minutes, streams them through Kafka, stores them in MinIO, loads into Snowflake, and transforms the data using dbt.

---

## How it works

1. `producer.py` calls the Adzuna API and pushes job listings into a Kafka topic
2. `consumer.py` reads from Kafka and saves each job as a JSON file in MinIO
3. `scheduler.py` runs `manual_bridge.py` every 10 minutes to move files from MinIO into Snowflake
4. Once in Snowflake, dbt cleans and transforms the data into Silver and Gold tables

```
Adzuna API → Kafka → MinIO → Snowflake → dbt (Silver → Gold)
```

---

## Requirements

- Python 3.12 specifically — 3.13+ breaks kafka-python and snowflake-connector-python
- Docker Desktop
- A Snowflake account (free trial is fine)
- Adzuna API credentials — sign up at https://developer.adzuna.com

---

## Running on a Virtual Machine

If you're running this on a VM (e.g. AWS EC2, Azure VM, or VirtualBox), make sure:

1. The VM has at least **4GB RAM** — Kafka and Zookeeper together use about 1.5-2GB
2. **Docker is installed** on the VM:
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose -y
   sudo usermod -aG docker $USER
   # log out and back in after this
   ```
3. **Python 3.12 is installed**:
   ```bash
   sudo apt install python3.12 python3.12-venv -y
   ```
4. Open the following ports in your VM's firewall/security group if you want to access the UIs from your local browser:
   - `9000` — Kafdrop
   - `9001` — MinIO console
   - `29092` — Kafka (if connecting externally)

5. In `producer.py` and `consumer.py`, `localhost` refers to the machine running Docker. If Docker and your Python scripts are on the same VM, this works as-is. If they're on different machines, replace `localhost` with the internal IP of the Docker host.

---

## Getting started

### 1. Clone and set up Python environment

```bash
git clone https://github.com/RuthiikSatti/job-market-pipeline.git
cd job-market-pipeline

# create venv with Python 3.12
py -3.12 -m venv .venv        # Windows
python3.12 -m venv .venv      # Linux/Mac VM

# activate it
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac VM

pip install -r requirements.txt
```

### 2. Create your .env file

```bash
copy .env.example .env    # Windows
cp .env.example .env      # Mac/Linux
```

Fill in the values:

```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password123
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account.region.aws
```

### 3. Set up Snowflake

Run this in your Snowflake worksheet:

```sql
CREATE DATABASE JOB_MARKET_DB;
CREATE SCHEMA JOB_MARKET_DB.BRONZE;

CREATE TABLE JOB_MARKET_DB.BRONZE.RAW_JOBS (
    raw_data VARIANT
);
```

### 4. Set up dbt

Create `~/.dbt/profiles.yml` on your machine:

```yaml
dbt_jobs:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: your_account.region.aws
      user: your_username
      password: your_password
      role: ACCOUNTADMIN
      database: JOB_MARKET_DB
      warehouse: COMPUTE_WH
      schema: SILVER
      threads: 1
```

Test it with `dbt debug` inside the `dbt_jobs` folder.

---

## Running it

You need 4 terminals open, all with the venv activated.

**Terminal 1 — start Docker**
```bash
docker-compose -f docker/docker-compose.yml up -d
```

**Terminal 2 — producer**
```bash
python producer/producer.py
```

**Terminal 3 — consumer**
```bash
python consumer/consumer.py
```

**Terminal 4 — scheduler**
```bash
python scheduler.py
```

Once data is flowing into Snowflake, run dbt:

```bash
cd dbt_jobs
dbt run
```

---

## Useful URLs

- Kafdrop (Kafka UI): http://localhost:9000
- MinIO console: http://localhost:9001 — login: `admin` / `password123`

---

## Querying in Snowflake

```sql
-- see cleaned job listings
SELECT * FROM JOB_MARKET_DB.SILVER.JOB_DATA_SILVER LIMIT 50;

-- top paying companies
SELECT * FROM JOB_MARKET_DB.GOLD.TOP_PAYING_COMPANIES ORDER BY average_min_salary DESC;
```

---

## Notes

- `.env` is not included in the repo — use `.env.example` as a template
- The `dag/` folder has an Airflow DAG that was part of the original design but scheduling is handled by `scheduler.py` instead
- `data/` and `logs/` are gitignored since they're generated locally
