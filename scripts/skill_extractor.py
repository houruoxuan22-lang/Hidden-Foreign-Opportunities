SKILL_KEYWORDS = {
    "AI": ["ai", "artificial intelligence", "machine learning", "ml"],
    "LLM": ["llm", "large language model", "generative ai", "genai"],
    "Data": ["data", "analytics", "analyst", "dashboard", "bi"],
    "SQL": ["sql"],
    "Python": ["python"],
    "Sales": ["sales", "account executive", "business development"],
    "Marketing": ["marketing", "growth", "campaign", "brand"],
    "Product": ["product manager", "product", "platform"],
    "Operations": ["operations", "ops", "supply chain", "logistics"],
    "Finance": ["finance", "financial", "accounting"],
    "Consulting": ["consulting", "consultant", "strategy"],
    "Cross-border": ["cross border", "cross-border", "global", "international"],
    "English": ["english", "bilingual", "japanese", "mandarin"],
    "Customer Success": ["customer success", "customer support", "client success"],
    "Engineering": ["engineer", "backend", "frontend", "software"],
}


def extract_skills_from_text(text):
    text = text.lower()
    matched_skills = []

    for skill, keywords in SKILL_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                matched_skills.append(skill)
                break

    return matched_skills


def enrich_jobs_with_skills(jobs):
    enriched_jobs = []

    for job in jobs:
        title = job.get("title", "")
        location = job.get("location", "")
        source = job.get("source", "")

        text = f"{title} {location} {source}"

        job["skills"] = extract_skills_from_text(text)
        enriched_jobs.append(job)

    return enriched_jobs