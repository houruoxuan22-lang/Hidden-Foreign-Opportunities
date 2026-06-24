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
            "source": "greenhouse"
        })

    return jobs
