import json
from crawlers.real_fetcher import fetch_greenhouse, filter_relevant_jobs
from scripts.generate_report import generate_markdown_report, save_report


JOBS_FILE = "data/jobs.json"


def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)


def main():
    companies = ["stripe"]

    all_jobs = []

    for company in companies:
        print(f"Fetching jobs from {company}...")
        jobs = fetch_greenhouse(company)
        relevant_jobs = filter_relevant_jobs(jobs)
        all_jobs.extend(relevant_jobs)

    save_jobs(all_jobs)

    report = generate_markdown_report(all_jobs)
    save_report(report)

    print("=== JOB RADAR RUN COMPLETE ===")
    print(f"Total relevant jobs: {len(all_jobs)}")
    print("Saved jobs to data/jobs.json")
    print("Generated report at reports/daily/latest.md")


if __name__ == "__main__":
    main()