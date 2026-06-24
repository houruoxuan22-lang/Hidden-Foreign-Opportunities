SKILL_KEYWORDS = {
    "AI": [
        "artificial intelligence",
        "machine learning",
        "generative ai",
        "genai",
        "ai product",
        "ai sales",
        "ai security"
    ],
    "LLM": [
        "llm",
        "large language model",
        "large language models",
        "prompt engineering",
        "rag"
    ],
    "Data": [
        "data analyst",
        "data analytics",
        "business intelligence",
        "dashboard",
        "reporting",
        "data-driven",
        "data analysis"
    ],
    "SQL": [
        "sql",
        "mysql",
        "postgresql",
        "database query"
    ],
    "Python": [
        "python",
        "pandas",
        "numpy"
    ],
    "Excel": [
        "excel",
        "spreadsheet",
        "vlookup",
        "pivot table"
    ],
    "Tableau": [
        "tableau"
    ],
    "Power BI": [
        "power bi",
        "powerbi"
    ],
    "CRM": [
        "crm",
        "salesforce crm",
        "hubspot"
    ],
    "Sales": [
        "account executive",
        "sales development",
        "business development",
        "enterprise sales",
        "sales strategy",
        "sales operations"
    ],
    "Marketing": [
        "growth marketing",
        "performance marketing",
        "campaign management",
        "brand marketing",
        "content marketing"
    ],
    "Product": [
        "product manager",
        "product management",
        "product strategy",
        "product operations",
        "product marketing"
    ],
    "Operations": [
        "operations associate",
        "business operations",
        "sales operations",
        "supply chain",
        "logistics",
        "procurement"
    ],
    "Finance": [
        "financial analyst",
        "financial planning",
        "accounting",
        "fp&a",
        "finance operations"
    ],
    "Consulting": [
        "consultant",
        "consulting",
        "strategy consultant",
        "management consulting"
    ],
    "Cross-border": [
        "cross-border",
        "cross border",
        "international expansion",
        "global markets",
        "regional market",
        "apac market"
    ],
    "English": [
        "english",
        "bilingual",
        "business english"
    ],
    "Japanese": [
        "japanese",
        "japan market",
        "japanese fluency"
    ],
    "Mandarin": [
        "mandarin",
        "chinese fluency",
        "china market"
    ],
    "Customer Success": [
        "customer success",
        "client success",
        "customer support",
        "customer experience",
        "account management"
    ],
    "Engineering": [
        "software engineer",
        "backend engineer",
        "frontend engineer",
        "full stack engineer",
        "security engineer",
        "infrastructure engineer"
    ],
    "Project Management": [
        "project management",
        "program management",
        "stakeholder management",
        "cross-functional coordination"
    ],
    "Communication": [
        "written communication",
        "verbal communication",
        "presentation skills",
        "executive communication"
    ],
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
        description = job.get("description", "")

        text = f"{title} {location} {source} {description}"

        job["skills"] = extract_skills_from_text(text)
        enriched_jobs.append(job)

    return enriched_jobs