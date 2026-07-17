# Hidden Foreign Opportunities

A daily AI-powered job radar that discovers hidden career opportunities from global companies and transforms them into structured job intelligence for job seekers.

## Why this project exists

Many foreign companies do not publish all of their job openings on domestic job platforms. For students and early-career job seekers, especially those interested in global companies, this creates a serious information gap.

This project aims to build an AI information worker that monitors global company career pages, extracts relevant job postings, and turns them into readable daily reports.

## What it does now

The current V1 system can:

- Fetch real job postings from Greenhouse-powered career pages
- Filter relevant jobs based on location and early-career keywords
- Save structured job data to JSON
- Generate a readable daily Markdown report
- Support multiple companies through a YAML configuration file

## Quick Preview

View the latest generated reports:

- Daily report: `reports/daily/latest.md`
- Weekly trend report: `reports/weekly/latest.md`

## Current workflow

```text
companies/companies.yaml
        ↓
run.py
        ↓
crawlers/real_fetcher.py
        ↓
data/jobs.json
        ↓
scripts/generate_report.py
        ↓
reports/daily/latest.md
```
## Project structure
Hidden-Foreign-Opportunities/
├── companies/
│   └── companies.yaml
├── crawlers/
│   ├── mock.py
│   └── real_fetcher.py
├── data/
│   └── jobs.json
├── reports/
│   └── daily/
│       └── latest.md
├── scripts/
│   └── generate_report.py
├── .gitignore
├── README.md
└── run.py

## How to run
Install dependencies:
pip install requests pyyaml
Run the job radar:
python3 run.py
The latest report will be generated at:
reports/daily/latest.md

## Company configuration
Companies are managed in:
companies/companies.yaml
Example:
- name: Stripe
  slug: stripe
  country: USA
  category: Tech
  ats: greenhouse
  priority: A
  Only companies with supported ATS configuration are currently fetched.

## Current data source support
| ATS        | Status    |
| ---------- | --------- |
| Greenhouse | Supported |
| Lever      | Supported |
| Workday    | Planned   |
| Ashby      | Planned   |

## Roadmap
- [x] Create company whitelist
- [x] Fetch real jobs from Greenhouse
- [x] Filter relevant jobs
- [x] Save results to JSON
- [x] Generate Markdown daily report
- [x] Load companies from YAML config
- [x] Add GitHub Actions for scheduled daily updates
- [x] Add Lever support
- [ ] Add Workday and Ashby support
- [x] Add basic skill extraction from job titles
- [x] Add description-based skill extraction
- [x] Improve skill extraction precision
- [ ] Add AI-powered semantic skill extraction
- [x] Add weekly skill trend analysis
- [ ] Add job seeker profile matching

## Example report
The generated daily report is available here:
reports/daily/latest.md

## Data notes

Job availability is based on whether a posting is listed on the public career page at the time of report generation. This project cannot guarantee whether a role is still actively hiring, already filled, or in late-stage recruitment.

Some roles may be located outside China. The current report may include China/APAC-relevant roles, global remote roles, and other international opportunities.

## Disclaimer
This project is for educational and research purposes. It only uses publicly available job posting data. Please respect each website's terms of service and robots.txt rules when extending the crawler.






