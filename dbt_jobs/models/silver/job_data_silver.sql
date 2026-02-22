with bronze_data as (
  select * from {{ source('adzuna', 'raw_jobs') }}
),

cleaned_jobs as (
  select
    raw_data:job_id::string as job_id,
    raw_data:title::string as job_title,
    raw_data:company::string as company_name,
    raw_data:salary::number as min_salary,
    raw_data:location::string as full_location,
    raw_data:timestamp::timestamp as ingestion_time
  from bronze_data
  where raw_data:title is not null
)

-- Deduplicate data based on job_id
select *
from cleaned_jobs
qualify row_number() over (partition by job_id order by ingestion_time desc) = 1
