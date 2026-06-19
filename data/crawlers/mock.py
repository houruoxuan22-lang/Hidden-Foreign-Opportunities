import json
from datetime import date

def fetch_jobs(company):
    return [
        {
            "company": company,
            "title": "Sample Role",
            "location": "Shanghai",
            "posted_date": str(date.today()),
            "source": "mock"
        }
    ]
