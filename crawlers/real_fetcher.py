import requests


def fetch_greenhouse(company_slug):
    url = f"https://api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true"

    res = requests.get(url, timeout=20)

    if res.status_code != 200:
        print(f"Failed to fetch {company_slug}: HTTP {res.status_code}")
        return []

    try:
        data = res.json()
    except Exception:
        print(f"Failed to parse JSON for {company_slug}")
        print(res.text[:300])
        return []

    jobs = []

    for job in data.get("jobs", []):
        jobs.append({
            "company": company_slug,
            "title": job.get("title", ""),
            "location": job.get("location", {}).get("name", ""),
            "posted_date": job.get("updated_at", ""),
            "source": "greenhouse",
            "url": job.get("absolute_url", "")
        })

    return jobs


def filter_relevant_jobs(jobs):
    keywords = [
        "china",
        "shanghai",
        "hangzhou",
        "nanjing",
        "wuxi",
        "beijing",
        "shenzhen",
        "guangzhou",
        "hong kong",
        "remote",
        "intern",
        "internship",
        "graduate",
        "entry level",
        "associate",
        "junior"
    ]

    filtered_jobs = []

    for job in jobs:
        text = f"{job['title']} {job['location']}".lower()

        if any(keyword in text for keyword in keywords):
            filtered_jobs.append(job)

    return filtered_jobs
