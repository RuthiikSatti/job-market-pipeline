with jobs as (
    select * from {{ ref('job_data_silver') }}
)

select
    full_location,
    count(*) as total_postings,
    avg(min_salary) as average_salary,
    min(min_salary) as lowest_salary,
    max(min_salary) as highest_salary
from jobs
where full_location is not null
group by full_location
order by total_postings desc
