import json
import os
from collections import Counter
from datetime import date, timedelta

from scripts.generate_report import categorize_job


HISTORY_DIR = "data/history"
WEEKLY_REPORT_FILE = "reports/weekly/latest.md"


def save_daily_snapshot(jobs):
    os.makedirs(HISTORY_DIR, exist_ok=True)

    today = date.today().isoformat()
    snapshot_file = os.path.join(HISTORY_DIR, f"{today}.json")

    with open(snapshot_file, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)


def load_weekly_snapshots(days=7):
    snapshots = []
    today = date.today()

    for i in range(days):
        current_date = today - timedelta(days=i)
        date_text = current_date.isoformat()
        snapshot_file = os.path.join(HISTORY_DIR, f"{date_text}.json")

        if not os.path.exists(snapshot_file):
            continue

        with open(snapshot_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        snapshots.append((date_text, jobs))

    return sorted(snapshots, key=lambda item: item[0])


def count_skills(jobs):
    counter = Counter()

    for job in jobs:
        for skill in job.get("skills", []):
            counter[skill] += 1

    return counter


def count_sections(jobs):
    counter = Counter()

    for job in jobs:
        section = categorize_job(job)
        counter[section] += 1

    return counter


def count_companies(jobs):
    counter = Counter()

    for job in jobs:
        company = job.get("company", "Unknown")
        counter[company] += 1

    return counter


def format_delta(delta):
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def generate_weekly_trend_report(days=7):
    snapshots = load_weekly_snapshots(days)

    lines = []
    today = date.today().isoformat()

    lines.append(f"# Weekly Job Trend Report - {today}")
    lines.append("")

    if not snapshots:
        lines.append("No historical job snapshots found yet.")
        return "\n".join(lines)

    first_date, first_jobs = snapshots[0]
    latest_date, latest_jobs = snapshots[-1]

    first_skill_counts = count_skills(first_jobs)
    latest_skill_counts = count_skills(latest_jobs)

    latest_section_counts = count_sections(latest_jobs)
    latest_company_counts = count_companies(latest_jobs)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Snapshot window: {first_date} to {latest_date}")
    lines.append(f"- Snapshot days available: {len(snapshots)}")
    lines.append(f"- Latest total relevant jobs: {len(latest_jobs)}")
    lines.append(f"- Change vs first available snapshot: {len(latest_jobs) - len(first_jobs)}")
    lines.append("")

    lines.append("## Skill Trend Signals")
    lines.append("")

    if latest_skill_counts:
        for skill, latest_count in latest_skill_counts.most_common(15):
            first_count = first_skill_counts.get(skill, 0)
            delta = latest_count - first_count
            lines.append(f"- {skill}: {latest_count} ({format_delta(delta)})")
    else:
        lines.append("- No skill signals detected.")

    lines.append("")

    lines.append("## Job Distribution by Section")
    lines.append("")

    for section, count in latest_section_counts.most_common():
        lines.append(f"- {section}: {count}")

    lines.append("")

    lines.append("## Top Companies in Latest Snapshot")
    lines.append("")

    for company, count in latest_company_counts.most_common(10):
        lines.append(f"- {company}: {count}")

    lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append("- Trend numbers are based on saved daily snapshots in `data/history/`.")
    lines.append("- A full weekly trend becomes more meaningful after several daily runs.")
    lines.append("- Job availability is based on whether postings are listed on public career pages at the time of generation.")

    return "\n".join(lines)


def save_weekly_report(markdown):
    os.makedirs(os.path.dirname(WEEKLY_REPORT_FILE), exist_ok=True)

    with open(WEEKLY_REPORT_FILE, "w", encoding="utf-8") as f:

        f.write(markdown)

        

