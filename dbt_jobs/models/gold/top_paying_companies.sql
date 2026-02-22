with jobs as (
    select * from {{ ref('job_data_silver') }}
),

company_analysis as (
    select
        company_name,
        count(*) as total_postings,
        avg(min_salary) as average_min_salary,
        max(min_salary) as highest_salary
    from jobs
    group by 1
    having count(*) > 1  -- Only show companies with multiple listings for better data
)

select *
from company_analysis
order by average_min_salary desc
