import os
from collections import defaultdict
from datetime import date


REPORT_FILE = "reports/daily/latest.md"


def group_jobs_by_company(jobs):
    grouped = defaultdict(list)

    for job in jobs:
        company = job.get("company", "Unknown")
        grouped[company].append(job)

    return grouped


def format_date(date_text):
    if not date_text:
        return ""

    return date_text[:10]


def categorize_job(job):
    location = job.get("location", "").lower()
    title = job.get("title", "").lower()
    text = f"{title} {location}"

    china_apac_keywords = [
        "china",
        "shanghai",
        "beijing",
        "shenzhen",
        "guangzhou",
        "hong kong",
        "singapore",
        "japan",
        "tokyo",
        "apac",
        "asia",
        "india",
        "bengaluru",
        "bangalore",
        "australia",
        "sydney",
        "melbourne",
        "new zealand",
        "auckland",
        "korea",
        "seoul",
        "taiwan",
        "taipei",
        "thailand",
        "bangkok",
        "malaysia",
        "kuala lumpur",
        "indonesia",
        "jakarta",
        "philippines",
        "manila",
        "vietnam",
        "ho chi minh",
    ]

    remote_keywords = [
        "remote",
        "global remote",
        "worldwide",
    ]

    us_canada_keywords = [
        "us-remote",
        "u.s.",
        "united states",
        "new york",
        "san francisco",
        "seattle",
        "chicago",
        "austin",
        "boston",
        "denver",
        "canada",
        "toronto",
        "vancouver",
    ]

    other_international_keywords = [
        "mexico",
        "mexico city",
        "london",
        "uk",
        "germany",
        "berlin",
        "france",
        "paris",
        "netherlands",
        "amsterdam",
        "ireland",
        "dublin",
    ]

    if any(keyword in text for keyword in china_apac_keywords):
        return "China / APAC Relevant Jobs"

    if any(keyword in text for keyword in remote_keywords):
        return "Global Remote Jobs"

    if any(keyword in text for keyword in other_international_keywords):
        return "Other International Jobs"

    if any(keyword in text for keyword in us_canada_keywords):
        return "US / Canada Jobs"

    return "Other Relevant Jobs"


def generate_markdown_report(jobs):
    today = date.today().isoformat()
    grouped_jobs = group_jobs_by_company(jobs)

    sections = {
        "China / APAC Relevant Jobs": [],
        "Global Remote Jobs": [],
        "Other International Jobs": [],
        "US / Canada Jobs": [],
        "Other Relevant Jobs": [],
    }

    for job in jobs:
        category = categorize_job(job)
        sections[category].append(job)

    skill_counts = {}

    for job in jobs:
        for skill in job.get("skills", []):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

    lines = []

    lines.append(f"# Daily Foreign Job Radar - {today}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total relevant jobs: {len(jobs)}")
    lines.append(f"- Companies tracked in this report: {len(grouped_jobs)}")
    lines.append(f"- China / APAC relevant jobs: {len(sections['China / APAC Relevant Jobs'])}")
    lines.append(f"- Global remote jobs: {len(sections['Global Remote Jobs'])}")
    lines.append(f"- Other international jobs: {len(sections['Other International Jobs'])}")
    lines.append(f"- US / Canada jobs: {len(sections['US / Canada Jobs'])}")
    lines.append(f"- Other relevant jobs: {len(sections['Other Relevant Jobs'])}")
    lines.append("")

    lines.append("## Skill Signals")
    lines.append("")

    if skill_counts:
        for skill, count in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- {skill}: {count}")
    else:
        lines.append("- No skill signals detected.")

    lines.append("")

    lines.append("## Jobs")
    lines.append("")

    for section_name, section_jobs in sections.items():
        lines.append(f"### {section_name}")
        lines.append("")

        if not section_jobs:
            lines.append("No matching jobs found in this run.")
            lines.append("")
            continue

        section_grouped_jobs = group_jobs_by_company(section_jobs)

        for company, company_jobs in section_grouped_jobs.items():
            lines.append(f"#### {company}")
            lines.append("")

            for job in company_jobs:
                title = job.get("title", "Untitled")
                location = job.get("location", "Unknown location")
                source = job.get("source", "Unknown source")
                url = job.get("url", "")
                updated = format_date(job.get("posted_date", ""))
                status = "Listed on official career page at report generation"

                if url:
                    lines.append(f"- [{title}]({url})")
                else:
                    lines.append(f"- {title}")

                lines.append(f"  - Location: {location}")

                if updated:
                    lines.append(f"  - Updated: {updated}")

                lines.append(f"  - Source: {source}")
                lines.append(f"  - Status: {status}")
                lines.append("")

        lines.append("")

    return "\n".join(lines)


def save_report(markdown):
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(markdown)