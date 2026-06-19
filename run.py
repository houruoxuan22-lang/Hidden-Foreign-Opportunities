from crawlers.real_fetcher import fetch_greenhouse

jobs = fetch_greenhouse("stripe")

for job in jobs[:5]:
    print(job)
