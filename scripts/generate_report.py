import json
from datetime import date
from collections import defaultdict


JOBS_FILE = "data/jobs.json"
REPORT_FILE = "reports/daily/latest.md"


def load_jobs():
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def group_jobs_by_company(jobs):
    grouped = defaultdict(list)

    for job in jobs:
        company = job.get("company", "Unknown")
        grouped[company].append(job)

    return grouped


def generate_markdown_report(jobs):
    today = date.today().isoformat()
    grouped_jobs = group_jobs_by_company(jobs)

    lines = []

    lines.append(f"# Daily Foreign Job Radar - {today}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total relevant jobs: {len(jobs)}")
    lines.append(f"- Companies tracked in this report: {len(grouped_jobs)}")
    lines.append("")
    skill_counts = {}

    for job in jobs:
        for skill in job.get("skills", []):
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

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

    for company, company_jobs in grouped_jobs.items():
        lines.append(f"### {company}")
        lines.append("")

        for job in company_jobs:
            title = job.get("title", "Untitled")
            location = job.get("location", "Unknown location")
            source = job.get("source", "Unknown source")
            url = job.get("url", "")

            if url:
                lines.append(f"- [{title}]({url})")
            else:
                lines.append(f"- {title}")

            lines.append(f"  - Location: {location}")
            lines.append(f"  - Source: {source}")
            lines.append("")

    return "\n".join(lines)


def save_report(markdown):
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(markdown)


def main():
    jobs = load_jobs()
    report = generate_markdown_report(jobs)
    save_report(report)

    print(f"Generated report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
