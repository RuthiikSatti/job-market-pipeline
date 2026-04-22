with jobs as (
    select * from {{ ref('job_data_silver') }}
)

select
    date_trunc('day', ingestion_time) as day,
    count(*) as postings_count,
    avg(min_salary) as average_salary,
    min(min_salary) as lowest_salary,
    max(min_salary) as highest_salary
from jobs
where min_salary is not null
group by 1
order by 1
