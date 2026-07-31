import re
import requests
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import urljoin, urlparse

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
EXCLUDE_KEYWORDS = [
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


CITY_PATTERNS = [
    (r"\bbased in sh\b|\bshanghai\b|上海", "Shanghai, China"),
    (r"\bbeijing\b|北京", "Beijing, China"),
    (r"\bshenzhen\b|深圳", "Shenzhen, China"),
    (r"\bguangzhou\b|广州", "Guangzhou, China"),
    (r"\bsuzhou\b|苏州", "Suzhou, China"),
    (r"\bhangzhou\b|杭州", "Hangzhou, China"),
    (r"\bnanjing\b|南京", "Nanjing, China"),
    (r"\bchengdu\b|成都", "Chengdu, China"),
    (r"\bchongqing\b|重庆", "Chongqing, China"),
    (r"\btianjin\b|天津", "Tianjin, China"),
    (r"\bwuhan\b|武汉", "Wuhan, China"),
    (r"\bqingdao\b|青岛", "Qingdao, China"),
    (r"\bxiamen\b|厦门", "Xiamen, China"),
    (r"\bningbo\b|宁波", "Ningbo, China"),
    (r"\bdalian\b|大连", "Dalian, China"),
    (r"\bxi'?an\b|西安", "Xi'an, China"),
    (r"\bhong kong\b|香港", "Hong Kong"),
    (r"\btaipei\b|\btaiwan\b|台湾|台北", "Taiwan"),
    
]
REGION_PATTERNS = [
    (r"\bsouthwest china\b", "Southwest China"),
    (r"\bgreater china\b", "Greater China"),
]


def normalize_text(text):
    return re.sub(r"[_\-/]+", " ", text.lower())


def extract_location(title, url, default_location="China", detail_text=""):
    
    title_url_text = normalize_text(f"{title} {url}")

    detail_text = detail_text or ""
    lower_detail = detail_text.lower()

    focused_parts = []
    for marker in ["location", "based in", "base location", "work location", "city"]:
        index = lower_detail.find(marker)
        if index != -1:
            focused_parts.append(lower_detail[max(0, index - 100): index + 300])

    focused_text = normalize_text(" ".join(focused_parts))

    # 1. Prefer specific city names from the job detail page.
    for pattern, location in CITY_PATTERNS:
        if re.search(pattern, focused_text):
            return location

    # 2. Then check specific city names from title and URL.
    for pattern, location in CITY_PATTERNS:
        if re.search(pattern, title_url_text):
            return location

    # 3. Only use broader region labels if no specific city is found.
    for pattern, location in REGION_PATTERNS:
        if re.search(pattern, focused_text) or re.search(pattern, title_url_text):
            return location

    return default_location

def fetch_detail_text(url, headers):
    try:
        res = requests.get(url, headers=headers, timeout=15)
    except Exception:
        return ""

    if res.status_code != 200:
        return ""

    soup = BeautifulSoup(res.text, "html.parser")
    return " ".join(soup.get_text(" ", strip=True).split())    


def looks_like_job_link(title, url):
    text = f"{title} {url}".lower()

    if len(title.strip()) < 4:
        return False

    if len(title.strip()) > 140:
        return False

    if any(keyword in text for keyword in EXCLUDE_KEYWORDS):
        return False


    return any(keyword in text for keyword in JOB_KEYWORDS)


def fetch_static_job_board(
    name,
    url,
    default_location="China",
    source_label="static_job_board",
    output_source_type="china_local_static",
    allowed_domains=None,
):
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
        allowed_domains = allowed_domains or []

        if allowed_domains:
            job_domain = urlparse(job_url).netloc.lower()
            if not any(domain in job_domain for domain in allowed_domains):
                continue

        if "europeanchamber.com.cn" in job_url and "/job-vacancies/" not in job_url:
            continue

        if "swisscham.com.cn" in job_url and "/jobs/" not in job_url:
            continue

        if not looks_like_job_link(title, job_url):
            continue

        if job_url in seen_urls:
            continue

        seen_urls.add(job_url)

        detail_text = fetch_detail_text(job_url, headers)
        location = extract_location(
            title=title,
            url=job_url,
            default_location=default_location,
            detail_text=detail_text,
        )

        jobs.append({
            "company": name,
            "title": title,
            "location": location,
            "posted_date": date.today().isoformat(),
            "source": source_label,
            "source_type": output_source_type,
            "audience": "china_based_job_seekers",
            "url": job_url,
            "description": detail_text[:1000],
        })

    print(f"{name}: {len(jobs)} China-local candidate jobs")

    return jobs