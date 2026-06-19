import requests

def fetch_greenhouse(company_slug):
    url = f"https://boards.greenhouse.io/{company_slug}/jobs?content=true"

    res = requests.get(url)
    data = res.json()

    jobs = []

    for job in data["jobs"]:
        jobs.append({
            "company": company_slug,
            "title": job["title"],
            "location": job.get("location", {}).get("name", ""),
            "posted_date": job.get("updated_at", ""),
            "source": "greenhouse"
        })

    return jobs
