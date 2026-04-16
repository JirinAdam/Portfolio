select DISTINCT position_levels, count(*) as count
from job_offers
group by position_levels
order by count desc;