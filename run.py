from crawlers.mock import fetch_jobs

companies = ["Siemens", "Bosch", "DHL"]

all_jobs = []

for c in companies:
    jobs = fetch_jobs(c)
    all_jobs.extend(jobs)

print("=== DAILY JOB REPORT ===")

for job in all_jobs:
    print(job["company"], "-", job["title"])
