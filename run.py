import json
import yaml
from crawlers.china_local_fetcher import fetch_static_job_board
from scripts.weekly_trend import save_daily_snapshot, generate_weekly_trend_report, save_weekly_report
from crawlers.real_fetcher import fetch_greenhouse, fetch_lever, filter_relevant_jobs
from scripts.generate_report import generate_markdown_report, save_report
from scripts.skill_extractor import enrich_jobs_with_skills


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
        source_type = company.get("source_type")
        url = company.get("url")
        default_location = company.get("default_location", "China")
        source_label = company.get("source_label", source_type or ats or "unknown")
        audience = company.get("audience", "global_job_seekers")

        if source_type in ["static_job_board", "company_career_page"]:
            jobs = fetch_static_job_board(
                name=name,
                url=url,
                default_location=default_location,
                source_label=source_label,
                output_source_type=(
        "china_company_career"
        if source_type == "company_career_page"
        else "china_local_static"
                ),
            )

            

        elif ats == "greenhouse":
            if not slug:
                print(f"Skipping {name}: missing Greenhouse slug")
                continue

            print(f"Fetching jobs from {name} ({slug}) via greenhouse...")
            jobs = fetch_greenhouse(slug)
            relevant_jobs = filter_relevant_jobs(jobs)

        elif ats == "lever":
            if not slug:
                print(f"Skipping jobs from {name} ({slug}) via lever...")
                continue

            print(f"Fetching jobs from {name} ({slug}) via lever...")
            jobs = fetch_lever(slug)
            relevant_jobs = filter_relevant_jobs(jobs)

        else:
            print(f"Skipping {name}: unsupported or missing source config")
            continue

        for job in relevant_jobs:
            job["company"] = name
            job["audience"] = audience

            if source_type in ["static_job_board", "company_career_page"]:
                job["source_type"] = (
                    "china_company_career"
                    if source_type == "company_career_page"
                    else "china_local_static"
                )
                job["source"] = source_label
                job["location"] = job.get("location") or default_location

        all_jobs.extend(relevant_jobs)

        print(f"{name}: {len(relevant_jobs)} relevant jobs")        
        
 
    all_jobs = enrich_jobs_with_skills(all_jobs)

    save_jobs(all_jobs)

    report = generate_markdown_report(all_jobs)
    save_report(report)
    save_daily_snapshot(all_jobs)

    weekly_report = generate_weekly_trend_report()
    save_weekly_report(weekly_report)

    save_daily_snapshot(all_jobs)

    weekly_report = generate_weekly_trend_report()
    save_weekly_report(weekly_report)

    print("=== JOB RADAR RUN COMPLETE ===")
    print(f"Total relevant jobs: {len(all_jobs)}")
    print("Saved jobs to data/jobs.json")
    print("Generated report at reports/daily/latest.md")
    print("Saved daily snapshot to data/history/")
    print("Generated weekly trend report at reports/weekly/latest.md")


if __name__ == "__main__":
    main()
