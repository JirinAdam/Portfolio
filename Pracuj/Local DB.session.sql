SELECT title, salary_min, salary_max, monthly_max_salary
from nerd_jobs
where monthly_max_salary = salary_min
AND salary_min = 25200
