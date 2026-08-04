import time

import requests


REQUEST_TIMEOUT = (10, 30)
MAX_ATTEMPTS = 3


def fetch_json(url, source_name):
    """Fetch JSON with retry and graceful failure."""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT,
            )

        except requests.exceptions.Timeout:
            print(
                f"{source_name}: request timed out "
                f"(attempt {attempt}/{MAX_ATTEMPTS})"
            )

        except requests.exceptions.RequestException as error:
            print(f"{source_name}: request failed: {error}")
            return None

        else:
            if response.status_code != 200:
                print(
                    f"{source_name}: HTTP {response.status_code}"
                )
                return None

            try:
                return response.json()

            except ValueError:
                print(f"{source_name}: failed to parse JSON")
                print(response.text[:300])
                return None

        if attempt < MAX_ATTEMPTS:
            wait_seconds = 2 ** (attempt - 1)
            print(
                f"{source_name}: retrying in "
                f"{wait_seconds} second(s)..."
            )
            time.sleep(wait_seconds)

    print(
        f"{source_name}: giving up after "
        f"{MAX_ATTEMPTS} attempts; continuing without this source"
    )
    return None


def fetch_greenhouse(company_slug):
    url = (
        f"https://api.greenhouse.io/v1/boards/"
        f"{company_slug}/jobs?content=true"
    )

    data = fetch_json(
        url,
        f"Greenhouse {company_slug}",
    )

    if not isinstance(data, dict):
        return []

    jobs = []

    for job in data.get("jobs", []):
        jobs.append(
            {
                "company": company_slug,
                "title": job.get("title", ""),
                "location": job.get("location", {}).get("name", ""),
                "posted_date": job.get("updated_at", ""),
                "source": "greenhouse",
                "url": job.get("absolute_url", ""),
                "description": job.get("content", ""),
            }
        )

    return jobs


def fetch_lever(company_slug):
    url = (
        f"https://api.lever.co/v0/postings/"
        f"{company_slug}?mode=json"
    )

    data = fetch_json(
        url,
        f"Lever {company_slug}",
    )

    if not isinstance(data, list):
        return []

    jobs = []

    for job in data:
        categories = job.get("categories", {}) or {}

        jobs.append(
            {
                "company": company_slug,
                "title": job.get("text", ""),
                "location": categories.get("location", ""),
                "posted_date": job.get("createdAt", ""),
                "source": "lever",
                "url": job.get("hostedUrl", ""),
                "description": (
                    job.get("descriptionPlain", "")
                    or job.get("description", "")
                ),
            }
        )

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
