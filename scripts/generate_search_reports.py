import json
import os
import re
from collections import defaultdict
from datetime import date


DATA_FILE = "data/jobs.json"
SEARCH_REPORT_DIR = "reports/search"


def load_jobs():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def job_text(job):
    fields = [
        job.get("title"),
        job.get("company"),
        job.get("location"),
        job.get("source"),
        job.get("source_type"),
        job.get("audience"),
        job.get("description"),
        job.get("skills"),
    ]
    return " ".join(safe_text(field) for field in fields).lower()


def normalize_for_search(value):
    text = safe_text(value).lower()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff+#.'-]+", " ", text)


def contains_keyword(text, keyword):
    keyword = keyword.lower().strip()

    if not keyword:
        return False

    # Chinese keywords do not need word boundaries.
    if any("\u4e00" <= char <= "\u9fff" for char in keyword):
        return keyword in text

    # Multi-word phrases should match as phrases.
    if " " in keyword:
        return keyword in text

    # Short English tokens like "ai" and "bi" must be exact words.
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None


def has_any(job, keywords):
    text = normalize_for_search(job_text(job))
    return any(contains_keyword(text, keyword) for keyword in keywords)


def title_has_any(job, keywords):
    text = normalize_for_search(job.get("title", ""))
    return any(contains_keyword(text, keyword) for keyword in keywords)


def location_has_any(job, keywords):
    text = normalize_for_search(job.get("location", ""))
    return any(contains_keyword(text, keyword) for keyword in keywords)


def format_date(value):
    if not value:
        return "Unknown"
    return str(value).split("T")[0]


def markdown_link(title, url):
    clean_title = str(title or "Untitled").replace("[", "(").replace("]", ")")
    if url:
        return f"[{clean_title}]({url})"
    return clean_title


def group_jobs_by_company(jobs):
    grouped = defaultdict(list)

    for job in jobs:
        company = job.get("company", "Unknown")
        grouped[company].append(job)

    return grouped


def is_mainland_china_job(job):
    source_type = job.get("source_type", "")
    audience = job.get("audience", "")
    location = safe_text(job.get("location")).lower()

    if audience == "china_based_job_seekers":
        return True

    if source_type in ["china_local_static", "china_company_career"]:
        return True

    if "hong kong" in location or "taiwan" in location:
        return False

    return "china" in location


def is_remote_job(job):
    return has_any(
        job,
        [
            "remote",
            "global remote",
            "worldwide",
            "work from home",
            "distributed",
        ],
    )


def is_internship_job(job):
    return has_any(
        job,
        [
            "intern",
            "internship",
            "graduate",
            "trainee",
            "entry level",
            "entry-level",
            "junior",
            "campus",
            "new grad",
            "实习",
            "校招",
            "应届",
            "管培",
        ],
    )


def build_report(title, jobs, description):
    today = date.today().isoformat()
    grouped_jobs = group_jobs_by_company(jobs)

    lines = []

    lines.append(f"# {title} - {today}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total matching jobs: {len(jobs)}")
    lines.append("- Source file: `data/jobs.json`")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(description)
    lines.append("")
    lines.append("## Jobs")
    lines.append("")

    if not jobs:
        lines.append("No matching jobs found.")
        lines.append("")
        return "\n".join(lines)

    for company, company_jobs in sorted(grouped_jobs.items()):
        lines.append(f"### {company}")
        lines.append("")

        for job in sorted(company_jobs, key=lambda item: safe_text(item.get("title")).lower()):
            title_text = markdown_link(job.get("title", "Untitled"), job.get("url", ""))
            location = job.get("location", "Unknown location")
            updated = format_date(job.get("posted_date", ""))
            source = job.get("source", "Unknown source")
            source_type = job.get("source_type", "Unknown source type")

            lines.append(f"- {title_text}")
            lines.append(f"  - Location: {location}")
            lines.append(f"  - Updated: {updated}")
            lines.append(f"  - Source: {source}")
            lines.append(f"  - Source type: {source_type}")
            lines.append("")

    return "\n".join(lines)


def write_report(filename, title, jobs, description):
    os.makedirs(SEARCH_REPORT_DIR, exist_ok=True)

    path = os.path.join(SEARCH_REPORT_DIR, filename)
    markdown = build_report(title, jobs, description)

    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)

    return path


def generate_index(report_results):
    today = date.today().isoformat()

    lines = []
    lines.append(f"# Searchable Job Reports - {today}")
    lines.append("")
    lines.append("This folder contains filtered job reports generated from `data/jobs.json`.")
    lines.append("")
    lines.append("## Quick Filters")
    lines.append("")

    for item in report_results:
        lines.append(
            f"- [{item['title']}]({item['filename']}) - {item['count']} jobs"
        )

    lines.append("")
    lines.append("## How to use")
    lines.append("")
    lines.append("Open the report that best matches your target location, role type, or job category.")
    lines.append("For more precise searching, use the browser search shortcut inside each report.")
    lines.append("")

    index_path = os.path.join(SEARCH_REPORT_DIR, "index.md")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return index_path


def generate_search_reports(jobs=None):
    if jobs is None:
        jobs = load_jobs()

    report_definitions = [
        {
            "filename": "mainland-china.md",
            "title": "Mainland China Foreign Employer Jobs",
            "description": "Jobs likely to be useful for China-based job seekers, including foreign employer roles in mainland China and China-local career sources.",
            "filter": is_mainland_china_job,
        },
        {
            "filename": "shanghai.md",
            "title": "Shanghai Jobs",
            "description": "Jobs with Shanghai-related location signals.",
            "filter": lambda job: location_has_any(job, ["shanghai", "上海"]),
        },
        {
            "filename": "beijing.md",
            "title": "Beijing Jobs",
            "description": "Jobs with Beijing-related location signals.",
            "filter": lambda job: location_has_any(job, ["beijing", "北京"]),
        },
        {
            "filename": "shenzhen.md",
            "title": "Shenzhen Jobs",
            "description": "Jobs with Shenzhen-related location signals.",
            "filter": lambda job: location_has_any(job, ["shenzhen", "深圳"]),
        },
        {
            "filename": "chengdu.md",
            "title": "Chengdu Jobs",
            "description": "Jobs with Chengdu-related location signals.",
            "filter": lambda job: location_has_any(job, ["chengdu", "成都"]),
        },
        {
            "filename": "chicago.md",
            "title": "Chicago Jobs",
            "description": "Jobs with Chicago-related location signals.",
            "filter": lambda job: location_has_any(job, ["chicago"]),
        },
        {
            "filename": "internships.md",
            "title": "Internships and Early-career Jobs",
            "description": "Jobs that look suitable for interns, new graduates, junior candidates, or early-career job seekers.",
            "filter": is_internship_job,
        },
        {
            "filename": "sales-business.md",
            "title": "Sales and Business Development Jobs",
            "description": "Jobs related to sales, account management, business development, partnerships, and client-facing growth roles.",
            "filter": lambda job: title_has_any(
                job,
                [
                    "sales",
                    "account executive",
                    "account manager",
                    "business development",                    
                    "partnership",
                    "customer success",
                    "client",
                    "revenue",
                ],
            ),
        },
        {
            "filename": "marketing.md",
            "title": "Marketing and Communications Jobs",
            "description": "Jobs related to marketing, communications, brand, content, events, PR, and growth.",
            "filter": lambda job: title_has_any(
                job,
                [
                    "marketing",
                    "communication",
                    "communications",
                    "brand",
                    "content",
                    "social media",
                    "event",
                    "events",
                    "pr",
                    "growth",
                ],
            ),
        },
        {
            "filename": "ai-data.md",
            "title": "AI and Data Jobs",
            "description": "Jobs related to AI, data, analytics, machine learning, business intelligence, and technical data work.",
            "filter": lambda job: title_has_any(
                job,
                [
                    "ai",
                    "artificial intelligence",
                    "machine learning",
                    "data",
                    "analytics",
                    "analyst",
                    "business intelligence",            
                    "sql",
                    "python",
                    "llm",
                ],
            ),
        },
        {
            "filename": "remote.md",
            "title": "Remote Jobs",
            "description": "Jobs with remote or distributed work signals.",
            "filter": is_remote_job,
        },
    ]

    report_results = []

    for report in report_definitions:
        filtered_jobs = [
            job for job in jobs
            if report["filter"](job)
        ]

        write_report(
            filename=report["filename"],
            title=report["title"],
            jobs=filtered_jobs,
            description=report["description"],
        )

        report_results.append(
            {
                "filename": report["filename"],
                "title": report["title"],
                "count": len(filtered_jobs),
            }
        )

    generate_index(report_results)

    return report_results


if __name__ == "__main__":
    results = generate_search_reports()
    for item in results:
        print(f"{item['filename']}: {item['count']} jobs")