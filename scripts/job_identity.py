import re
from urllib.parse import parse_qs, urlsplit


def job_identity(job):
    source = str(job.get("source") or "").strip().lower()
    company = str(job.get("company") or "").strip().lower()
    url = str(job.get("url") or "").strip()

    if source == "greenhouse" and url:
        query = parse_qs(urlsplit(url).query)
        gh_jid = str((query.get("gh_jid") or [""])[0]).strip()

        if gh_jid:
            return ("greenhouse", company, gh_jid)

    if source == "european_chamber" and url:
        path = urlsplit(url).path
        match = re.search(r"/job-vacancies/(\d+)(?:/|$)", path)

        if match:
            return ("european_chamber", company, match.group(1))

    if source == "sap_careers" and url:
        path = urlsplit(url).path
        match = re.search(r"/(\d+)/?$", path)

        if match:
            return ("sap_careers", company, match.group(1))

    normalized_url = url.lower().rstrip("/")

    if normalized_url:
        return ("url", normalized_url)

    return (
        "fallback",
        company,
        str(job.get("title") or "").strip().lower(),
        str(job.get("location") or "").strip().lower(),
    )

def deduplicate_jobs(jobs):
    seen = set()
    deduped_jobs = []

    for job in jobs:
        identity = job_identity(job)

        if identity in seen:
            continue

        seen.add(identity)
        deduped_jobs.append(job)

    return deduped_jobs
