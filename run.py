import json
import yaml

from crawlers.real_fetcher import fetch_greenhouse, fetch_lever, filter_relevant_jobs
from scripts.generate_report import generate_markdown_report, save_report


COMPANIES_FILE = "companies/companies.yaml"
JOBS_FILE = "data/jobs.json"


def load_companies():
    with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
        companies = yaml.safe_load(f)

    return companies or []


def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)


def main():
    companies = load_companies()

    all_jobs = []

    for company in companies:
        name = company.get("name")
        slug = company.get("slug")
        ats = company.get("ats")

        if not slug or not ats:
            print(f"Skipping {name}: unsupported or missing ATS config")
            continue

        print(f"Fetching jobs from {name} ({slug}) via {ats}...")

        if ats == "greenhouse":
            jobs = fetch_greenhouse(slug)
        elif ats == "lever":
            jobs = fetch_lever(slug)
        else:
            print(f"Skipping {name}: unsupported ATS type: {ats}")
            continue

        relevant_jobs = filter_relevant_jobs(jobs)

        for job in relevant_jobs:
            job["company"] = name

        all_jobs.extend(relevant_jobs)

        print(f"{name}: {len(relevant_jobs)} relevant jobs")

    save_jobs(all_jobs)

    report = generate_markdown_report(all_jobs)
    save_report(report)

    print("=== JOB RADAR RUN COMPLETE ===")
    print(f"Total relevant jobs: {len(all_jobs)}")
    print("Saved jobs to data/jobs.json")
    print("Generated report at reports/daily/latest.md")


if __name__ == "__main__":
    main()