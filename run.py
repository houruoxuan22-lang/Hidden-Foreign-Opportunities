import json
from crawlers.real_fetcher import fetch_greenhouse, filter_relevant_jobs


companies = ["stripe"]

all_jobs = []

for company in companies:
    jobs = fetch_greenhouse(company)
    relevant_jobs = filter_relevant_jobs(jobs)
    all_jobs.extend(relevant_jobs)

print("=== RELEVANT JOBS REPORT ===")
print(f"Total relevant jobs: {len(all_jobs)}")

for job in all_jobs[:10]:
    print(job["company"], "-", job["title"], "-", job["location"])

with open("data/jobs.json", "w", encoding="utf-8") as f:
    json.dump(all_jobs, f, ensure_ascii=False, indent=2)

print("Saved to data/jobs.json")