# Real-Time Job Market Data Pipeline
### A Data Engineering Project Report

---

## b) Abstract / Executive Summary

*(Placeholder — complete after the project is fully finished and results are available)*

*This section should summarize: what the pipeline does, the key tools used, what data was collected, and one or two findings from the Gold layer (e.g., top paying companies, most active hiring companies). Keep it to 150–200 words.*

---

## c) Introduction / Problem Statement

The job market is constantly shifting. Job postings go up and down daily, salaries vary widely across companies and locations, and it can be hard to get a clear picture of what the market looks like at any given moment. Most people searching for jobs rely on manual browsing, which only gives a snapshot of whatever they happen to search on that day.

The goal of this project was to build a pipeline that automatically collects job data over time, stores it, and makes it queryable — so you can start to answer questions like: which companies are hiring the most data engineers? What is the average advertised salary? How do salaries differ by location?

The specific focus was on data engineering and data analyst roles in the United States. These roles were chosen because they are relevant to the field of study and because the Adzuna API, which was used as the data source, provides reasonably detailed job listings for this category including salary estimates, company name, and location.

The pipeline was designed to run continuously — fetching new listings every 30 minutes, storing them in layers (raw, cleaned, aggregated), and keeping a historical record that grows over time. This approach mirrors what a real data engineering team might build inside a company to monitor external data sources.

---

## d) Tool Selection and Evaluation

Each tool in the pipeline was chosen for a specific reason. This section explains what each tool does, why it was selected over alternatives, and any trade-offs or issues encountered.

---

### Adzuna API — Data Source

Adzuna is a job aggregation platform that provides a free developer API. It was chosen because it offers structured JSON responses with the fields needed for this project: job title, company name, location, and salary estimate. The free tier allows up to 250 API calls per month, which is sufficient for a project running every 30 minutes over a short period.

Alternatives considered included the Indeed API (which no longer offers public access) and LinkedIn (which requires a partner agreement). Adzuna was the most accessible option that still returned meaningful salary data.

One limitation is that salary data is not always present — many job postings do not include a salary range, so `salary_min` can be null. This was handled in the Silver layer by filtering or treating nulls appropriately.

---

### Apache Kafka — Message Streaming

Kafka is an open-source distributed event streaming platform. It acts as a buffer between the producer (which fetches from the API) and the consumer (which writes to storage). The producer sends each job listing as a message to a Kafka topic called `realtime_jobs`, and the consumer reads from that topic independently.

The reason for using Kafka rather than writing directly to storage is decoupling. If the storage system (MinIO) is slow or temporarily unavailable, Kafka holds the messages so nothing is lost. It also makes the pipeline more extensible — you could add a second consumer later without touching the producer at all.

Kafka was run locally using the `confluentinc/cp-kafka:7.4.1` Docker image. Zookeeper was also required as Kafka's coordination service. Kafdrop, an open-source web UI, was added as a monitoring tool to visually inspect messages in the topic during development.

An alternative to Kafka for a smaller project would be RabbitMQ or even a simple database queue. Kafka was chosen here because it is the industry standard for real-time data pipelines and it was worth learning in a project context.

---

### MinIO — Object Storage (Bronze Layer)

MinIO is an S3-compatible object store that can be run locally using Docker. It was used as the Bronze layer — the landing zone for raw, unprocessed data. Each job listing is saved as an individual JSON file, organized into folders by date (`jobs/YYYY-MM-DD/job_<id>.json`).

The reason for using an object store rather than writing directly into a database is to preserve the raw data exactly as it was received. This is a principle from the Medallion Architecture — raw data should be kept untouched so that if transformation logic changes later, the original data can always be reprocessed.

MinIO was chosen over AWS S3 because it runs locally without any cloud account or cost. The S3-compatible API means the code could be switched to real S3 with minimal changes if needed.

---

### Snowflake — Data Warehouse

Snowflake is a cloud-based analytical database. It was used to store the job data in a structured, queryable format after it was loaded from MinIO. The data is stored in a `VARIANT` column (Snowflake's semi-structured JSON type) in the Bronze schema, and then parsed into proper typed columns by dbt.

Snowflake was chosen over alternatives like PostgreSQL or BigQuery for a few reasons. It handles semi-structured JSON natively through its `PARSE_JSON` and colon-extraction syntax (`raw_data:title::string`), which made it well-suited for storing and querying the raw job listings. It also has a generous free trial and is widely used in data engineering roles, making it a useful tool to work with in a project context.

The main trade-off is that Snowflake is a paid cloud service. The free trial was sufficient for this project but a production version would incur costs based on compute usage.

---

### dbt (data build tool) — Transformation

dbt is a transformation tool that lets you write SQL models inside a project structure. It handles dependencies between models, runs them in the right order, and documents the lineage from raw data through to final tables.

Two models were written:

- **Silver model (`job_data_silver`)**: Takes the raw JSON from the Bronze table, parses each field into a typed column (string, number, timestamp), filters out records where the job title is null, and deduplicates based on `job_id` using a window function. This ensures each job only appears once even if it was ingested multiple times across fetches.

- **Gold model (`top_paying_companies`)**: Aggregates the Silver data by company name, calculating the total number of job postings, average minimum salary, and highest salary offered. Only companies with more than one listing are included, to avoid skew from single data points.

dbt was chosen because it brings software engineering practices (version control, testing, documentation) to SQL transformations. An alternative would be writing transformation scripts in Python directly, but dbt's structure and reusability made it more appropriate for a multi-layer pipeline.

---

### Docker — Infrastructure

All the infrastructure components (Kafka, Zookeeper, Kafdrop, MinIO) were run using Docker and defined in a single `docker-compose.yml` file. This made the setup reproducible — anyone with Docker installed can bring up the full stack with one command.

Docker was the natural choice here as all the tools used have official Docker images and running them locally without Docker would have required complex manual installation and configuration.

---

### Python 3.12 — Runtime

The pipeline scripts were written in Python 3.12. Python 3.13 was initially attempted but caused compatibility issues with two key packages: `kafka-python` and `snowflake-connector-python`, both of which had dependency conflicts on the newer version at the time of development. Python 3.12 resolved these issues and was used throughout the project.

---

## e) Planned Logic / Program Design

*(Placeholder — fill in with your original design sketches, flow diagrams, or pseudocode from before you started building)*

*This section should describe what you planned to build before you started coding. Include:*
- *A diagram or written description of the data flow*
- *Which tools you intended to use and why*
- *Any changes between the original plan and the final implementation (e.g., Airflow was originally planned for scheduling but was replaced by a Python scheduler due to Docker networking issues on Windows)*

---

## f) Documentation

*(Placeholder — complete once the project is fully running)*

*This section should include:*
- *Screenshots of the pipeline running (producer output, consumer output, Kafdrop showing messages, MinIO showing files, Snowflake showing rows)*
- *Output of `dbt run` showing models built successfully*
- *Sample query results from the Gold layer*
- *Any error messages encountered and how they were resolved*

---

## g) Conclusions

*(Placeholder — complete after running and evaluating the pipeline)*

*This section should reflect on:*
- *Whether the pipeline worked as intended*
- *What the data showed (any interesting findings from the Gold layer)*
- *What you would do differently or improve with more time*
- *What you learned from building it*

---

## h) References

Apache Kafka Documentation. (2024). *Introduction to Kafka*. Apache Software Foundation. https://kafka.apache.org/documentation/

Adzuna Developer API. (2024). *API Documentation*. Adzuna. https://developer.adzuna.com/overview

dbt Labs. (2024). *What is dbt?*. dbt Documentation. https://docs.getdbt.com/docs/introduction

MinIO Documentation. (2024). *MinIO Object Storage*. MinIO Inc. https://min.io/docs/minio/container/index.html

Snowflake Documentation. (2024). *Semi-Structured Data*. Snowflake Inc. https://docs.snowflake.com/en/user-guide/semistructured-intro

Confluent. (2024). *Apache Kafka on Docker*. Confluent Inc. https://docs.confluent.io/platform/current/installation/docker/installation.html

Databricks. (2024). *Medallion Architecture*. Databricks Inc. https://www.databricks.com/glossary/medallion-architecture

Docker Documentation. (2024). *Docker Compose Overview*. Docker Inc. https://docs.docker.com/compose/

Ozdemir, B. (2023). *Fundamentals of Data Engineering*. O'Reilly Media.
