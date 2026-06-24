import re


TITLE_SKILL_KEYWORDS = {
    "Sales": [
        "account executive",
        "sales development",
        "business development",
        "sales manager",
        "sales operations",
        "enterprise sales",
    ],
    "Engineering": [
        "software engineer",
        "backend engineer",
        "frontend engineer",
        "full stack engineer",
        "security engineer",
        "infrastructure engineer",
        "data engineer",
    ],
    "Product": [
        "product manager",
        "product management",
        "product operations",
        "product marketing",
    ],
    "Operations": [
        "operations associate",
        "business operations",
        "sales operations",
        "supply chain",
        "logistics",
        "procurement",
    ],
    "Marketing": [
        "growth marketing",
        "performance marketing",
        "brand marketing",
        "content marketing",
        "marketing manager",
    ],
    "Finance": [
        "financial analyst",
        "finance manager",
        "accounting",
        "fp&a",
        "finance operations",
    ],
    "Consulting": [
        "consultant",
        "strategy consultant",
        "management consulting",
    ],
    "Customer Success": [
        "customer success",
        "client success",
        "customer support",
        "customer experience",
        "account management",
    ],
    "Data": [
        "data analyst",
        "data scientist",
        "data engineer",
        "business intelligence",
        "analytics engineer",
    ],
    "AI": [
        "ai engineer",
        "ai product",
        "ai sales",
        "machine learning engineer",
        "ml engineer",
    ],
}


DESCRIPTION_SKILL_KEYWORDS = {
    "SQL": [
        "sql",
        "mysql",
        "postgresql",
        "database query",
    ],
    "Python": [
        "python",
        "pandas",
        "numpy",
    ],
    "Excel": [
        "excel",
        "spreadsheet",
        "vlookup",
        "pivot table",
    ],
    "Tableau": [
        "tableau",
    ],
    "Power BI": [
        "power bi",
        "powerbi",
    ],
    "CRM": [
        "crm",
        "salesforce crm",
        "hubspot",
    ],
    "LLM": [
    "large language model",
    "large language models",
    "prompt engineering",
    "retrieval augmented generation",
    "generative ai platform",
    "llm application",
    "llm applications",
    ],
    "Project Management": [
        "project management",
        "program management",
        "stakeholder management",
        "cross-functional coordination",
    ],
    "Communication": [
        "written communication",
        "verbal communication",
        "presentation skills",
        "executive communication",
    ],
    "English": [
        "business english",
        "english fluency",
        "fluent in english",
    ],
    "Japanese": [
        "japanese fluency",
        "fluent in japanese",
        "japan market",
    ],
    "Mandarin": [
        "mandarin",
        "chinese fluency",
        "china market",
    ],
    "Cross-border": [
        "cross-border",
        "cross border",
        "international expansion",
        "global markets",
        "apac market",
    ],
}


def contains_keyword(text, keyword):
    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
    return re.search(pattern, text.lower()) is not None


def extract_skills_from_text(title, description):
    matched_skills = []

    title_text = title.lower()
    description_text = description.lower()

    # Role/category signals: use title only to avoid boilerplate noise.
    for skill, keywords in TITLE_SKILL_KEYWORDS.items():
        if any(contains_keyword(title_text, keyword) for keyword in keywords):
            matched_skills.append(skill)

    # Tool/language/process signals: use title + description.
    full_text = f"{title_text} {description_text}"

    for skill, keywords in DESCRIPTION_SKILL_KEYWORDS.items():
        if any(contains_keyword(full_text, keyword) for keyword in keywords):
            matched_skills.append(skill)

    return matched_skills


def enrich_jobs_with_skills(jobs):
    enriched_jobs = []

    for job in jobs:
        title = job.get("title", "")
        description = job.get("description", "")

        job["skills"] = extract_skills_from_text(title, description)
        enriched_jobs.append(job)

    return enriched_jobs