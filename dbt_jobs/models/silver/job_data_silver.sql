with bronze_data as (
  select * from {{ source('adzuna', 'raw_jobs') }}
),

cleaned_jobs as (
  select
    raw_data->>'job_id' as job_id,
    raw_data->>'title' as job_title,
    raw_data->>'company' as company_name,
    (raw_data->>'salary')::numeric as min_salary,
    raw_data->>'location' as full_location,
    (raw_data->>'timestamp')::timestamp as ingestion_time
  from bronze_data
  where raw_data->>'title' is not null
),

deduplicated as (
  select *,
    row_number() over (partition by job_id order by ingestion_time desc) as rn
  from cleaned_jobs
)

select job_id, job_title, company_name, min_salary, full_location, ingestion_time
from deduplicated
where rn = 1
