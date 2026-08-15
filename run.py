from datetime import datetime, timezone
import json
import yaml
from crawlers.china_local_fetcher import fetch_static_job_board
from scripts.weekly_trend import save_daily_snapshot, generate_weekly_trend_report, save_weekly_report
from crawlers.real_fetcher import fetch_greenhouse, fetch_lever, filter_relevant_jobs
from scripts.generate_report import generate_markdown_report, save_report
from scripts.skill_extractor import enrich_jobs_with_skills
from scripts.generate_search_reports import generate_search_reports
from scripts.generate_web_dashboard import generate_web_dashboard
from scripts.match_jobs import PROFILE_FILE, load_json, score_jobs


COMPANIES_FILE = "companies/companies.yaml"
JOBS_FILE = "data/jobs.json"


def load_companies():
    with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
        companies = yaml.safe_load(f)

    return companies or []

def job_identity(job):
    url = str(job.get("url") or "").strip().lower().rstrip("/")

    if url:
        return ("url", url)

    return (
        "fallback",
        str(job.get("company") or "").strip().lower(),
        str(job.get("title") or "").strip().lower(),
        str(job.get("location") or "").strip().lower(),
    )

def load_existing_jobs():
    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    return jobs if isinstance(jobs, list) else []


def apply_seen_metadata(jobs, existing_jobs, seen_at):
    existing_by_identity = {
        job_identity(job): job
        for job in existing_jobs
    }

    for job in jobs:
        previous = existing_by_identity.get(job_identity(job), {})

        job["first_seen"] = (
            previous.get("first_seen")
            or seen_at
        )
        job["last_seen"] = seen_at

    return jobs

def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)


def main():
    companies = load_companies()
    existing_jobs = load_existing_jobs()
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
        allowed_domains = company.get("allowed_domains", [])

        if source_type in ["static_job_board", "company_career_page"]:
            jobs = fetch_static_job_board(
                name=name,
                url=url,
                default_location=default_location,
                source_label=source_label,
                allowed_domains=allowed_domains,
                output_source_type=(
                    "china_company_career"
                    if source_type == "company_career_page"
                    else "china_local_static"
                ),
            )
            relevant_jobs = jobs

            

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

    seen_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    all_jobs = apply_seen_metadata(
        all_jobs,
        existing_jobs,
        seen_at,
    )

    save_jobs(all_jobs)
    profile = load_json(PROFILE_FILE)
    matched_jobs = score_jobs(all_jobs, profile)

    report = generate_markdown_report(all_jobs)
    save_report(report)
    generate_search_reports(all_jobs)
    generate_web_dashboard(matched_jobs, profile)
    save_daily_snapshot(all_jobs)

    weekly_report = generate_weekly_trend_report()
    save_weekly_report(weekly_report)

  

    print("=== JOB RADAR RUN COMPLETE ===")
    print(f"Total relevant jobs: {len(all_jobs)}")
    print("Saved jobs to data/jobs.json")
    print("Generated report at reports/daily/latest.md")
    print("Saved daily snapshot to data/history/")
    print("Generated weekly trend report at reports/weekly/latest.md")
    print("Generated searchable reports at reports/search/")
    print("Generated web dashboard at docs/index.html")


if __name__ == "__main__":
    main()
