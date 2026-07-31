import requests
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import urljoin


JOB_KEYWORDS = [
    "manager",
    "associate",
    "assistant",
    "specialist",
    "officer",
    "director",
    "consultant",
    "engineer",
    "analyst",
    "intern",
    "coordinator",
    "executive",
    "sales",
    "marketing",
    "operations",
    "finance",
    "hr",
    "human resources",
    "business development",
    "program",
    "project",
    "职位",
    "招聘",
    "实习",
    "经理",
    "专员",
    "主管",
    "助理",    
]
EXCLUDE_KEYWORDS =[ 
    "member directory",
    "members directory",
    "business directory",
    "board of directors",
    "governance",
    "executive committee",
    "working groups",
    "forums",
    "desks",
    "membership",
    "events",
    "news",
    "publications",
    "sponsorship",
    "contact",
    "about",
]



def looks_like_job_link(title, url):
    text = f"{title} {url}".lower()

    if len(title.strip()) < 4:
        return False

    if len(title.strip()) > 140:
        return False

    if any(keyword in text for keyword in EXCLUDE_KEYWORDS):
        return False


    return any(keyword in text for keyword in JOB_KEYWORDS)


def fetch_static_job_board(name, url, default_location="China", source_label="static_job_board"):
    print(f"Fetching China-local jobs from {name}...")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; HiddenForeignOpportunitiesBot/1.0; educational project)"
    }

    try:
        res = requests.get(url, headers=headers, timeout=20)
    except Exception as e:
        print(f"Failed to fetch {name}: {e}")
        return []

    if res.status_code != 200:
        print(f"Failed to fetch {name}: HTTP {res.status_code}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    jobs = []
    seen_urls = set()

    for link in soup.find_all("a", href=True):
        title = " ".join(link.get_text(" ", strip=True).split())
        job_url = urljoin(url, link.get("href", ""))

        if "europeanchamber.com.cn" in job_url and "/job-vacancies/" not in job_url:
            continue

        if "swisscham.com.cn" in job_url and "/jobs/" not in job_url:
            continue

        if not looks_like_job_link(title, job_url):
            continue

        if job_url in seen_urls:
            continue

        seen_urls.add(job_url)

        jobs.append({
            "company": name,
            "title": title,
            "location": default_location,
            "posted_date": date.today().isoformat(),
            "source": source_label,
            "source_type": "china_local_static",
            "audience": "china_based_job_seekers",
            "url": job_url,
            "description": "",
        })

    print(f"{name}: {len(jobs)} China-local candidate jobs")

    return jobs