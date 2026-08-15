import json
import os
import re
import html
from datetime import date


DATA_FILE = "data/jobs.json"
OUTPUT_DIR = "docs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")


def load_jobs():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def format_date(value):
    if not value:
        return "Unknown"
    return str(value).split("T")[0]



def clean_description(value):
    text = safe_text(value)
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

NAVIGATION_NOISE_KEYWORDS = [
    # Chamber / association navigation noise
    "member directory",
    "about us",
    "chamber services",
    "useful links",
    "governance",
    "executive committee",
    "chapter board",
    "advertise with us",
    "articles of association",
    "former presidents",
    "supervisory board",
    "advisory council",
    "membership",
    "job vacancies join us",

    # SAP / company career page navigation noise
    "skip to main content",
    "view profile",
    "search by keyword",
    "search by location",
    "show more options",
    "loading...",
    "work area all",
    "career status all",
    "country all",
    "select how often",
    "to receive",
    "job alert",
    "create alert",
    "language deutsch",
    "english global",
    "français france",
    "日本語",
    "简体中文",
]

JOB_DETAIL_SIGNALS = [
    "responsibilities",
    "requirements",
    "qualifications",
    "what you will do",
    "what you'll do",
    "you will",
    "job description",
    "skills",
    "experience",
    "role",
    "职位描述",
    "岗位职责",
    "任职要求",
    "工作职责",
]


def looks_like_navigation_text(text):
    normalized = safe_text(text).lower()

    if not normalized:
        return False

    noise_hits = sum(
        1 for keyword in NAVIGATION_NOISE_KEYWORDS
        if keyword in normalized
    )

    has_job_detail_signal = any(
        signal in normalized
        for signal in JOB_DETAIL_SIGNALS
    )

    if has_job_detail_signal:
        return False

    # General rule: many navigation signals and no JD signal.
    if noise_hits >= 3:
        return True

    # SAP career pages often expose navigation text instead of JD body.
    sap_navigation_patterns = [
        "skip to main content",
        "view profile",
        "search by keyword",
        "search by location",
        "show more options",
        "work area all",
        "career status all",
        "select how often",
    ]

    sap_hits = sum(
        1 for pattern in sap_navigation_patterns
        if pattern in normalized
    )

    if sap_hits >= 2:
        return True

    # Repeated language selector text is usually page chrome, not job description.
    if normalized.count("language") >= 2 and "view profile" in normalized:
        return True

    return False


def clean_dashboard_description(value):
    text = clean_description(value)

    if looks_like_navigation_text(text):
        return ""

    return text


def human_source_type(value):
    mapping = {
        "ats_api": "Official ATS",
        "greenhouse": "Official ATS",
        "lever": "Official ATS",
        "china_local_static": "China-local job board",
        "china_company_career": "Company career page",
        "static_job_board": "Public job board",
    }

    raw_value = safe_text(value).strip()
    key = raw_value.lower()

    return mapping.get(key, raw_value or "Unknown source type")



def normalize_job(job):
    title = safe_text(job.get("title")) or "Untitled"
    company = safe_text(job.get("company")) or "Unknown company"
    location = safe_text(job.get("location")) or "Unknown location"
    source = safe_text(job.get("source")) or "Unknown source"
    source_type = (
    safe_text(job.get("source_type"))
    or safe_text(job.get("ats"))
    or "ats_api"
    )
    audience = safe_text(job.get("audience")) or "unknown"
    url = safe_text(job.get("url"))
    posted_date = format_date(job.get("posted_date"))
    description = clean_dashboard_description(job.get("description"))

    raw_match_score = job.get("match_score")

    if isinstance(raw_match_score, (int, float)):
        match_score = int(raw_match_score)
    else:
        match_score = None

    match_label = safe_text(job.get("match_label")).strip()

    good_fit = job.get("good_fit", [])
    if not isinstance(good_fit, list):
        good_fit = []

    good_fit = [
        safe_text(reason).strip()
        for reason in good_fit
        if safe_text(reason).strip()
    ]

    watch_out = job.get("watch_out", [])
    if not isinstance(watch_out, list):
        watch_out = []

    watch_out = [
        safe_text(reason).strip()
        for reason in watch_out
        if safe_text(reason).strip()
    ]

    search_text = " ".join(
        [
            title,
            company,
            location,
            source,
            source_type,
            audience,
            description,
        ]
    ).lower()

    return {
        "title": title,
        "company": company,
        "location": location,
        "source": source,
        "source_type": source_type,
        "source_type_label": human_source_type(source_type),
        "audience": audience,
        "url": url,
        "posted_date": posted_date,
        "description": description[:500],
        "match_score": match_score,
        "match_label": match_label,
        "good_fit": good_fit,
        "watch_out": watch_out,
        "search_text": search_text,
    }

def deduplicate_normalized_jobs(jobs):
    seen = set()
    deduped_jobs = []

    for job in jobs:
        url = safe_text(job.get("url")).strip().lower().rstrip("/")

        if url:
            key = ("url", url)
        else:
            key = (
                "fallback",
                safe_text(job.get("company")).strip().lower(),
                safe_text(job.get("title")).strip().lower(),
                safe_text(job.get("location")).strip().lower(),
            )

        if key in seen:
            continue

        seen.add(key)
        deduped_jobs.append(job)

    return deduped_jobs

def build_dashboard_html(jobs, profile=None):
    today = date.today().isoformat()
    if not isinstance(profile, dict):
        profile = {}
    profile_name = (
        safe_text(profile.get("profile_name")).strip()
        or "Default matching profile"
    )

    profile_description = (
        safe_text(profile.get("description")).strip()
        or "This dashboard currently uses a default matching profile."
    )

    target_locations = profile.get("target_locations", [])
    if not isinstance(target_locations, list):
        target_locations = []


    target_role_areas = profile.get("target_role_areas", [])
    if not isinstance(target_role_areas, list):
        target_role_areas = []

    def build_profile_chips(values):
        chips = []

        for value in values:
            clean_value = safe_text(value).strip()

            if not clean_value:
                continue

            chips.append(
                '<span class="profile-chip">'
                f'{html.escape(clean_value)}'
                '</span>'
            )

        if not chips:
            return '<span class="profile-empty">Not specified</span>'

        return "".join(chips)

    profile_name_html = html.escape(profile_name)
    profile_description_html = html.escape(profile_description)
    profile_locations_html = build_profile_chips(target_locations)
    profile_roles_html = build_profile_chips(target_role_areas)

    skill_keywords = profile.get("skill_keywords", [])

    if not isinstance(skill_keywords, list):
        skill_keywords = []

    profile_editor_data = dict(profile)

    profile_editor_data["profile_name"] = profile_name
    profile_editor_data["target_locations"] = target_locations
    profile_editor_data["target_role_areas"] = target_role_areas
    profile_editor_data["skill_keywords"] = skill_keywords

    profile_editor_data.setdefault(
        "career_stage",
        "early_career",
    )

    profile_editor_data.setdefault(
        "remote_preference",
        "preferred",
    )

    profile_editor_json = json.dumps(
        profile_editor_data,
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")


    scoring = profile.get("scoring", {})
    if not isinstance(scoring, dict):
        scoring = {}

    def format_score_points(value):
        if not isinstance(value, (int, float)):
            return "Not configured"

        if value > 0:
            return f"+{value}"

        return str(value)

    def build_score_rules(rules, point_class):
        rows = []

        for label, scoring_key in rules:
            value = scoring.get(scoring_key)

            if not isinstance(value, (int, float)):
                continue

            rows.append(
                '<div class="score-rule">'
                f'<span class="score-rule-label">{html.escape(label)}</span>'
                f'<strong class="score-rule-points {point_class}">'
                f'{html.escape(format_score_points(value))}'
                '</strong>'
                '</div>'
            )

        if not rows:
            return '<p class="profile-empty">No scoring rules configured.</p>'

        return "".join(rows)

    positive_score_rules = [
        ("Target location match", "location_match"),
        ("Preferred role match", "role_match"),
        ("Early-career signal", "early_career_match"),
        ("Matched skills — maximum", "skill_match_max"),
        ("Remote-friendly location", "remote_match"),
    ]

    risk_score_rules = [
        ("Region-restricted remote role", "restricted_remote_penalty"),
        ("Location outside current targets", "location_mismatch_penalty"),
        ("Seniority signal in job title — each", "title_risk_penalty"),
        ("Experience-risk requirement — each", "risk_keyword_penalty"),
        ("Specialized qualification requirement — each", "strong_exclude_penalty"),
    ]

    positive_score_rules_html = build_score_rules(
        positive_score_rules,
        "positive",
    )

    risk_score_rules_html = build_score_rules(
        risk_score_rules,
        "negative",
    )

    normalized_jobs = deduplicate_normalized_jobs(
        [normalize_job(job) for job in jobs]
    )

    jobs_json = json.dumps(normalized_jobs, ensure_ascii=False)
    jobs_json = jobs_json.replace("</", "<\\/")

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Hidden Foreign Opportunities</title>
  <style>
    :root {
      --bg: #f6f8fa;
      --card: #ffffff;
      --text: #1f2328;
      --muted: #656d76;
      --border: #d0d7de;
      --accent: #0969da;
      --accent-soft: #ddf4ff;
      --badge: #f6f8fa;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }

    header {
      background: var(--card);
      border-bottom: 1px solid var(--border);
      padding: 28px 24px;
    }

    .container {
      width: min(1180px, 100%);
      margin: 0 auto;
      padding: 24px;
    }

    h1 {
      margin: 0 0 8px;
      font-size: 32px;
    }

    .subtitle {
      color: var(--muted);
      margin: 0;
      max-width: 760px;
    }

    .stats {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 18px;
    }

    .stat {
      background: var(--badge);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 14px;
      color: var(--muted);
    }

    .stat strong {
      color: var(--text);
    }

    .profile-panel {
      margin-bottom: 18px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      overflow: hidden;
    }

    .profile-panel summary {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 16px 18px;
      cursor: pointer;
      font-weight: 650;
    }

    .profile-panel summary:hover {
      background: var(--badge);
    }

    .profile-summary-name {
      color: var(--muted);
      font-size: 13px;
      font-weight: 500;
    }

    .profile-summary-actions {
      display: inline-flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
    }

    .profile-edit-button {
      padding: 6px 11px;
      background: var(--accent-soft);
      border-color: var(--accent);
      color: var(--accent);
      font-size: 12px;
    }

    .profile-editor-dialog {
      width: min(720px, calc(100vw - 32px));
      max-height: 88vh;
      padding: 0;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: var(--card);
      color: var(--text);
      box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22);
      overflow: auto;
    }

    .profile-editor-dialog::backdrop {
      background: rgba(15, 23, 42, 0.55);
    }

    .profile-editor-header {
      position: sticky;
      top: 0;
      z-index: 2;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      padding: 20px;
      border-bottom: 1px solid var(--border);
      background: var(--card);
    }

    .profile-editor-header h2 {
      margin: 0;
      font-size: 20px;
    }

    .profile-editor-header p {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    .profile-editor-close {
      flex: 0 0 auto;
      width: 36px;
      height: 36px;
      padding: 0;
      border-radius: 50%;
      font-size: 24px;
      line-height: 1;
    }

    .profile-editor-form {
      padding: 20px;
    }

    .profile-editor-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }

    .profile-editor-field {
      display: flex;
      flex-direction: column;
      gap: 7px;
    }

    .profile-editor-field > span {
      font-size: 13px;
      font-weight: 650;
    }

    .profile-editor-field small {
      color: var(--muted);
      font-size: 12px;
    }

    .profile-editor-wide {
      grid-column: 1 / -1;
    }

    .profile-editor-field textarea {
      width: 100%;
      min-width: 0;
      resize: vertical;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 11px 12px;
      background: #fff;
      color: var(--text);
      font: inherit;
      line-height: 1.5;
    }

    .profile-editor-field textarea:focus,
    .profile-editor-field input:focus,
    .profile-editor-field select:focus {
      outline: 2px solid var(--accent-soft);
      border-color: var(--accent);
    }

    .profile-editor-notice {
      margin: 18px 0 0;
      padding: 11px 13px;
      border-left: 3px solid var(--accent);
      background: var(--accent-soft);
      color: var(--muted);
      font-size: 13px;
    }

    .profile-editor-actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 20px;
    }

    .profile-editor-primary {
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
    }

    .profile-editor-primary:disabled {
      cursor: not-allowed;
      opacity: 0.5;
    }

    .profile-content {
      padding: 0 18px 18px;
      border-top: 1px solid var(--border);
    }

    .profile-description {
      margin: 14px 0;
      color: var(--muted);
      font-size: 14px;
      max-width: 900px;
    }

    .profile-group {
      margin-top: 14px;
    }

    .profile-group-title {
      margin: 0 0 8px;
      font-size: 13px;
      font-weight: 650;
    }

    .profile-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .profile-chip {
      display: inline-flex;
      align-items: center;
      padding: 4px 9px;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--badge);
      color: var(--muted);
      font-size: 12px;
    }

    .profile-empty {
      color: var(--muted);
      font-size: 13px;
    }

    .score-details {
      margin-top: 18px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--badge);
      overflow: hidden;
    }

    .score-details summary {
      justify-content: flex-start;
      padding: 13px 14px;
      font-size: 14px;
      font-weight: 650;
    }

    .score-details-content {
      padding: 0 14px 14px;
      border-top: 1px solid var(--border);
      background: var(--card);
    }

    .score-intro {
      margin: 13px 0;
      color: var(--muted);
      font-size: 13px;
    }

    .score-columns {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .score-column {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
    }

    .score-column h3 {
      margin: 0 0 10px;
      font-size: 14px;
    }

    .score-rule {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      padding: 7px 0;
      border-top: 1px solid var(--border);
      font-size: 13px;
    }

    .score-rule:first-of-type {
      border-top: 0;
      padding-top: 0;
    }

    .score-rule-label {
      color: var(--muted);
    }

    .score-rule-points {
      flex: 0 0 auto;
      font-size: 13px;
    }

    .score-rule-points.positive {
      color: #116329;
    }

    .score-rule-points.negative {
      color: #9a6700;
    }

    .score-levels {
      margin-top: 14px;
    }

    .score-level-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .score-level {
      display: inline-flex;
      align-items: center;
      padding: 5px 9px;
      border: 1px solid var(--border);
      border-radius: 999px;
      color: var(--muted);
      font-size: 12px;
    }

    .score-disclaimer {
      margin: 14px 0 0;
      padding: 10px 12px;
      border-left: 3px solid var(--accent);
      background: var(--accent-soft);
      color: var(--muted);
      font-size: 13px;
    }
    .filters {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
      margin-bottom: 18px;
      overflow: hidden;
    }

    .filter-grid {
      display: grid;
      grid-template-columns:repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
    }

    .filter-grid input[type="search"] {
      grid-column: span 2;
    }

    input,
    select {
      width: 100%;
      min-width: 0;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 11px 12px;
      font-size: 14px;
      background: #fff;
      color: var(--text);
    }

    .quick-buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }

    button {
      border: 1px solid var(--border);
      background: #fff;
      color: var(--text);
      border-radius: 999px;
      padding: 8px 12px;
      cursor: pointer;
      font-size: 13px;
    }
    .share-status {
      color: var(--muted);
      font-size: 13px;
      align-self: center;
      padding: 8px 0;
    }

    button:hover,
    button.active {
      border-color: var(--accent);
      background: var(--accent-soft);
      color: var(--accent);
    }

    .result-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin: 18px 0;
      color: var(--muted);
    }

    .jobs {
      display: grid;
      gap: 14px;
    }

    .job-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px;
    }

    .job-title {
      font-size: 18px;
      font-weight: 650;
      margin: 0 0 10px;
      overflow-wrap: anywhere;
    }

    .job-title a {
      color: var(--accent);
      text-decoration: none;
    }

    .job-title a:hover {
      text-decoration: underline;
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
    }

    .badge {
      background: var(--badge);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 4px 8px;
      color: var(--muted);
      font-size: 12px;
      max-width: 100%;
      overflow-wrap: anywhere;
    }

    .description {
      color: var(--muted);
      margin: 10px 0 0;
      font-size: 14px;
      overflow-wrap: anywhere;
    }
    .match-panel {
      margin-top: 12px;
      padding: 12px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--badge);
    }

    .match-header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }

    .match-score {
      display: inline-flex;
      align-items: center;
      border: 1px solid #1f883d;
      border-radius: 999px;
      background: #dafbe1;
      color: #116329;
      padding: 4px 9px;
      font-size: 13px;
      font-weight: 700;
    }

    .match-label {
      color: var(--muted);
      font-size: 13px;
      font-weight: 600;
    }

    .match-reason {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 13px;
      overflow-wrap: anywhere;
    }

    .match-reason strong {
      color: var(--text);
    }

    .match-reason.watch-out strong {
      color: #9a6700;
    }

    .empty {
      background: var(--card);
      border: 1px dashed var(--border);
      border-radius: 14px;
      padding: 32px;
      text-align: center;
      color: var(--muted);
    }

    footer {
      color: var(--muted);
      font-size: 13px;
      margin-top: 28px;
      padding-bottom: 30px;
    }

    @media (max-width: 900px) {
      header {
        padding: 22px 0;
      }

      .container {
        padding: 16px;
      }

      h1 {
        font-size: 26px;
      }

      .subtitle {
        font-size: 14px;
      }

      .filter-grid {
        grid-template-columns: 1fr;
      }

      .filter-grid input[type="search"] {
        grid-column: span 1;
      }

      .result-bar {
        align-items: flex-start;
        flex-direction: column;
        gap: 8px;
      }

      .job-card {
        padding: 16px;
      }

      .job-title {
        font-size: 17px;
      }
}

@media (max-width: 560px) {

    .profile-summary-actions {
    width: 100%;
    justify-content: space-between;
  }

  .profile-editor-dialog {
    width: calc(100vw - 20px);
    max-height: 92vh;
  }

  .profile-editor-header,
  .profile-editor-form {
    padding: 16px;
  }

  .profile-editor-grid {
    grid-template-columns: 1fr;
  }

  .profile-editor-wide {
    grid-column: auto;
  }

  .profile-editor-actions {
    flex-direction: column-reverse;
  }

  .profile-editor-actions button {
    width: 100%;
  }
  .score-columns {
    grid-template-columns: 1fr;
  }

  .score-rule {
    gap: 8px;
  }
  .stats {
    display: grid;
    grid-template-columns: 1fr;
  }

  .stat {
    width: 100%;
  }

  .quick-buttons {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  button {
    width: 100%;
    padding: 10px 12px;
  }

  .meta {
    gap: 6px;
  }

  .badge {
    border-radius: 10px;
  }

  .description {
    font-size: 13px;
  }
}
  </style>
</head>
<body>
  <header>
    <div class="container">
      <h1>Hidden Foreign Opportunities</h1>
      <p class="subtitle">
       Search and filter foreign-company job opportunities from official career pages,
       public ATS sources, and China-local job boards.
       Always verify job details on the official posting page before applying.
      </p>
      <div class="stats">
        <div class="stat"><strong id="totalJobs">0</strong> total jobs</div>
        <div class="stat"><strong id="visibleJobs">0</strong> visible now</div>
        <div class="stat">Generated: <strong>__GENERATED_DATE__</strong></div>
      </div>
    </div>
  </header>

  <main class="container">
      <details class="profile-panel">
        <summary>
          <span>Current matching profile</span>
          <span
            id="currentProfileName"
          class="profile-summary-name"
          >
          __PROFILE_NAME__
         </span>

           <button
              id="openProfileEditor"
              class="profile-edit-button"
              type="button"
            >
              Customize profile
            </button>
          </span>
        </summary>

        <div class="profile-content">
        <p class="profile-description">
          __PROFILE_DESCRIPTION__
        </p>

        <div class="profile-group">
          <p class="profile-group-title">Target role areas</p>

          <div
           id="currentProfileLocations"
           class="profile-chips"
          >
          __PROFILE_LOCATIONS__
          </div>
        <div
          id="currentProfileRoles"
          class="profile-chips"
        >
          __PROFILE_ROLES__
        </div>
        </div>

            <details class="score-details">
      <summary>How the match score is calculated</summary>

      <div class="score-details-content">
        <p class="score-intro">
          The score starts at 0 and combines matching signals with possible
          risk deductions. Scores are limited to a range of 0–100.
        </p>

        <div class="score-columns">
          <section class="score-column">
            <h3>Fit signals</h3>
            __POSITIVE_SCORE_RULES__
          </section>

          <section class="score-column">
            <h3>Possible deductions</h3>
            __RISK_SCORE_RULES__
          </section>
        </div>

        <div class="score-levels">
          <p class="profile-group-title">Score labels</p>

          <div class="score-level-list">
            <span class="score-level">75–100 · Strong match</span>
            <span class="score-level">55–74 · Potential match</span>
            <span class="score-level">35–54 · Worth exploring</span>
            <span class="score-level">0–34 · Low match</span>
          </div>
        </div>

        <p class="score-disclaimer">
          Match scores estimate alignment with this default profile.
          They are not hiring predictions or guarantees of interview or offer success.
          Always review the full job description before applying.
        </p>
      </div>
    </details>
      </div>
    </details>

    <dialog
      id="profileEditorDialog"
      class="profile-editor-dialog"
      aria-labelledby="profileEditorTitle"
    >
      <div class="profile-editor-header">
        <div>
          <h2 id="profileEditorTitle">Customize matching profile</h2>
          <p>
            Adjust the profile used to evaluate and prioritize job opportunities.
          </p>
        </div>

        <button
          id="closeProfileEditor"
          class="profile-editor-close"
          type="button"
          aria-label="Close profile editor"
        >
          ×
        </button>
      </div>

      <form id="profileEditorForm" class="profile-editor-form">
        <div class="profile-editor-grid">
          <label class="profile-editor-field profile-editor-wide">
            <span>Profile name</span>

            <input
              id="profileNameInput"
              type="text"
              maxlength="100"
            />
          </label>

          <label class="profile-editor-field">
            <span>Career stage</span>

            <select id="profileCareerStageSelect">
              <option value="early_career">Early career</option>
              <option value="mid_career">Mid career</option>
              <option value="senior">Senior</option>
              <option value="any">Any career stage</option>
            </select>
          </label>

          <label class="profile-editor-field">
            <span>Remote preference</span>

            <select id="profileRemotePreferenceSelect">
              <option value="preferred">Remote preferred</option>
              <option value="accepted">Remote accepted</option>
              <option value="not_preferred">On-site preferred</option>
              <option value="any">No preference</option>
            </select>
          </label>

          <label class="profile-editor-field profile-editor-wide">
            <span>Target locations</span>

            <textarea
              id="profileLocationsInput"
              rows="3"
              placeholder="Shanghai, Beijing, Shenzhen, Remote"
            ></textarea>

            <small>Separate locations with commas.</small>
          </label>

          <label class="profile-editor-field profile-editor-wide">
            <span>Target role areas</span>

            <textarea
              id="profileRolesInput"
              rows="3"
              placeholder="Marketing, Customer Success, Operations"
            ></textarea>

            <small>Separate role areas with commas.</small>
          </label>

          <label class="profile-editor-field profile-editor-wide">
            <span>Skills and keywords</span>

            <textarea
              id="profileSkillsInput"
              rows="4"
              placeholder="English, Marketing, CRM, Excel"
            ></textarea>

            <small>
              These keywords are used by the browser-side scoring engine when calculating Match Scores.
            </small>
          </label>
        </div>

        <p class="profile-editor-notice">
           Changes are applied to Match Scores immediately
           and saved in this browser.
        </p>

        <div class="profile-editor-actions">
        <button
          id="resetProfileEditor"
          type="button"
        >
          Reset to default
        </button>

        <button
          id="cancelProfileEditor"
          type="button"
        >
          Cancel
        </button>

        <button
          id="applyProfileEditor"
          class="profile-editor-primary"
          type="submit"
        >
          Apply profile
         </button>
        </div>
      </form>
    </dialog>

    <section class="filters">

      <div class="filter-grid">
        <input id="searchInput" type="search" placeholder="Search title, company, city, skill, source..." />

        <select id="locationSelect">
          <option value="">All locations</option>
        </select>

        <select id="companySelect">
          <option value="">All companies</option>
        </select>

        <select id="sourceSelect">
          <option value="">All sources</option>
        </select>

        <select id="categorySelect">
          <option value="">All categories</option>
          <option value="mainland">Mainland China</option>
          <option value="remote">Remote</option>
          <option value="internship">Internship / Early-career</option>
          <option value="sales">Sales / Business</option>
          <option value="marketing">Marketing / Communications</option>
          <option value="ai_data">AI / Data</option>
        </select>

        <select id="matchSelect">
          <option value="">All match scores</option>
          <option value="75">Strong matches (75+)</option>
          <option value="55">Potential or better (55+)</option>
          <option value="35">Worth exploring or better (35+)</option>
        </select>

        <select id="freshnessSelect">
          <option value="">All dates</option>
          <option value="7">Updated in last 7 days</option>
          <option value="14">Updated in last 14 days</option>
          <option value="30">Updated in last 30 days</option>
        </select>

        <select id="sortSelect">
          <option value="updated_desc">Newest first</option>
          <option value="match_desc">Best Match first</option>
          <option value="updated_asc">Oldest first</option>
          <option value="company">Company A-Z</option>
          <option value="title">Title A-Z</option>
        </select>
      </div>

      <div class="quick-buttons">
        <button data-category="mainland">Mainland China</button>
        <button data-location="Shanghai">Shanghai</button>
        <button data-location="Beijing">Beijing</button>
        <button data-location="Chicago">Chicago</button>
        <button data-category="internship">Internships</button>
        <button data-category="remote">Remote</button>
        <button data-freshness="7">Last 7 days</button>
        <button id="clearFilters">Clear filters</button>
        <button id="copyLinkButton">Copy current link</button>
        <span id="shareStatus" class="share-status" aria-live="polite"></span>
      </div>
    </section>

    <div class="result-bar">
      <div id="resultSummary">Showing 0 jobs</div>
      <div id="activeFilters"></div>
    </div>

    <section id="jobsList" class="jobs"></section>

    <footer>
      Job availability is based on whether a posting was listed on a public career page
      at report generation time. Always verify details on the official posting page.
    </footer>
  </main>

  <script>
    const jobs = __JOBS_JSON__;
    const defaultProfile = __PROFILE_EDITOR_JSON__;
    const PROFILE_STORAGE_KEY =
      "hiddenForeignOpportunities.matchingProfile.v1";

    let activeProfile = JSON.parse(
      JSON.stringify(defaultProfile)
    );

    const searchInput = document.getElementById("searchInput");
    const locationSelect = document.getElementById("locationSelect");
    const companySelect = document.getElementById("companySelect");
    const sourceSelect = document.getElementById("sourceSelect");
    const categorySelect = document.getElementById("categorySelect");
    const matchSelect = document.getElementById("matchSelect");
    const freshnessSelect = document.getElementById("freshnessSelect");
    const sortSelect = document.getElementById("sortSelect");
    const jobsList = document.getElementById("jobsList");
    const resultSummary = document.getElementById("resultSummary");
    const activeFilters = document.getElementById("activeFilters");
    const totalJobs = document.getElementById("totalJobs");
    const visibleJobs = document.getElementById("visibleJobs");
    const clearFilters = document.getElementById("clearFilters");
    const copyLinkButton = document.getElementById("copyLinkButton");
    const openProfileEditor = document.getElementById(
      "openProfileEditor"
    );
    const closeProfileEditor = document.getElementById(
      "closeProfileEditor"
    );
    const cancelProfileEditor = document.getElementById(
      "cancelProfileEditor"
    );
    const profileEditorDialog = document.getElementById(
      "profileEditorDialog"
    );
    const profileEditorForm = document.getElementById(
      "profileEditorForm"
    );

    const profileNameInput = document.getElementById(
      "profileNameInput"
    );
    const profileCareerStageSelect = document.getElementById(
      "profileCareerStageSelect"
    );
    const profileRemotePreferenceSelect = document.getElementById(
      "profileRemotePreferenceSelect"
    );
    const profileLocationsInput = document.getElementById(
      "profileLocationsInput"
    );
    const profileRolesInput = document.getElementById(
      "profileRolesInput"
    );
    const profileSkillsInput = document.getElementById(
      "profileSkillsInput"
    );
    const currentProfileName = document.getElementById(
      "currentProfileName"
    );

    const currentProfileLocations = document.getElementById(
      "currentProfileLocations"
    );

    const currentProfileRoles = document.getElementById(
      "currentProfileRoles"
    );

    const resetProfileEditor =
      document.getElementById(
        "resetProfileEditor"
      );

    totalJobs.textContent = jobs.length;

    function editorListValue(values) {
      if (!Array.isArray(values)) {
        return "";
      }

      return values
        .map(value => String(value).trim())
        .filter(Boolean)
        .join(", ");
    }

    function parseEditorList(value) {
      return String(value || "")
        .split(",")
        .map(item => item.trim())
        .filter(Boolean);
    }

    function buildRoleKeywordsFromAreas(roleAreas) {
      const keywordMap = {
        "marketing": [
          "marketing",
          "communications",
          "communication",
          "brand",
          "content",
          "social media",
        ],

        "business development": [
          "business development",
          "partnership",
          "growth",
        ],

        "customer success": [
          "customer success",
          "client service",
        ],

        "operations": [
          "operations",
        ],

        "sales": [
          "sales",
          "account executive",
          "account manager",
        ],

        "project coordination": [
          "project coordinator",
          "project management",
        ],

        "cross-border business": [
          "cross border",
          "cross-border",
        ],
      };

      const keywords = [];

      roleAreas.forEach(area => {
        const normalizedArea = String(area || "")
          .trim()
          .toLowerCase();

        if (!normalizedArea) {
          return;
        }

        const mappedKeywords =
          keywordMap[normalizedArea]
          || [normalizedArea];

        mappedKeywords.forEach(keyword => {
          if (!keywords.includes(keyword)) {
            keywords.push(keyword);
          }
        });
      });

      return keywords;
    }

    function editableProfileSnapshot(profile) {
  return {
    profile_name:
      profile.profile_name || "",

    career_stage:
      profile.career_stage || "early_career",

    remote_preference:
      profile.remote_preference || "preferred",

    target_locations:
      Array.isArray(profile.target_locations)
        ? profile.target_locations
        : [],

    target_role_areas:
      Array.isArray(profile.target_role_areas)
        ? profile.target_role_areas
        : [],

    skill_keywords:
      Array.isArray(profile.skill_keywords)
        ? profile.skill_keywords
        : [],
  };
}

function saveActiveProfile(profile) {
  try {
    const profileSnapshot =
      editableProfileSnapshot(profile);

    const defaultSnapshot =
      editableProfileSnapshot(defaultProfile);

    if (
      JSON.stringify(profileSnapshot)
      === JSON.stringify(defaultSnapshot)
    ) {
      localStorage.removeItem(
        PROFILE_STORAGE_KEY
      );

      return;
    }

    localStorage.setItem(
      PROFILE_STORAGE_KEY,
      JSON.stringify(profileSnapshot)
    );
  } catch (error) {
    console.warn(
      "Could not save matching profile:",
      error
    );
  }
}

function profileFromStoredSnapshot(savedProfile) {
  if (
    !savedProfile
    || typeof savedProfile !== "object"
  ) {
    return null;
  }

  const targetLocations =
    Array.isArray(savedProfile.target_locations)
      ? savedProfile.target_locations
      : defaultProfile.target_locations;

  const targetRoleAreas =
    Array.isArray(savedProfile.target_role_areas)
      ? savedProfile.target_role_areas
      : defaultProfile.target_role_areas;

  const skillKeywords =
    Array.isArray(savedProfile.skill_keywords)
      ? savedProfile.skill_keywords
      : defaultProfile.skill_keywords;

  const allowedCareerStages =
    new Set([
      "early_career",
      "mid_career",
      "senior",
      "any",
    ]);

  const allowedRemotePreferences =
    new Set([
      "preferred",
      "accepted",
      "not_preferred",
      "any",
    ]);

  const careerStage =
    allowedCareerStages.has(
      savedProfile.career_stage
    )
      ? savedProfile.career_stage
      : defaultProfile.career_stage;

  const remotePreference =
    allowedRemotePreferences.has(
      savedProfile.remote_preference
    )
      ? savedProfile.remote_preference
      : defaultProfile.remote_preference;

  return {
    ...JSON.parse(
      JSON.stringify(defaultProfile)
    ),

    profile_name:
      typeof savedProfile.profile_name === "string"
      && savedProfile.profile_name.trim()
        ? savedProfile.profile_name.trim()
        : defaultProfile.profile_name,

    career_stage:
      careerStage,

    remote_preference:
      remotePreference,

    target_locations:
      targetLocations,

    target_role_areas:
      targetRoleAreas,

    skill_keywords:
      skillKeywords
        .map(value =>
          String(value).trim().toLowerCase()
        )
        .filter(Boolean),

    location_keywords:
      targetLocations
        .map(value =>
          String(value).trim()
        )
        .filter(value =>
          value
          && value.toLowerCase() !== "remote"
        )
        .map(value =>
          value.toLowerCase()
        ),

    role_keywords:
      buildRoleKeywordsFromAreas(
        targetRoleAreas
      ),
  };
}

function resetActiveProfile() {
  try {
    localStorage.removeItem(
      PROFILE_STORAGE_KEY
    );
  } catch (error) {
    console.warn(
      "Could not clear saved matching profile:",
      error
    );
  }

  activeProfile = JSON.parse(
    JSON.stringify(defaultProfile)
  );

  populateProfileEditor(
    activeProfile
  );

  updateVisibleProfile(
    activeProfile
  );

  rescoreJobs(
    activeProfile
  );

  applyFilters();
}

function loadStoredProfile() {
  try {
    const rawProfile =
      localStorage.getItem(
        PROFILE_STORAGE_KEY
      );

    if (!rawProfile) {
      return null;
    }

    return profileFromStoredSnapshot(
      JSON.parse(rawProfile)
    );
  } catch (error) {
    console.warn(
      "Could not load saved matching profile:",
      error
    );

    return null;
  }
}

    function buildProfileFromEditor() {
      const targetLocations = parseEditorList(
        profileLocationsInput.value
      );

      const targetRoleAreas = parseEditorList(
        profileRolesInput.value
      );

      const skillKeywords = parseEditorList(
        profileSkillsInput.value
      );

      return {
        ...activeProfile,

        profile_name:
          profileNameInput.value.trim()
          || "Custom matching profile",

        career_stage:
          profileCareerStageSelect.value,

        remote_preference:
          profileRemotePreferenceSelect.value,

        target_locations:
          targetLocations,

        target_role_areas:
          targetRoleAreas,

        skill_keywords:
          skillKeywords.map(value =>
            value.toLowerCase()
          ),

        location_keywords:
          targetLocations
            .filter(value =>
              value.toLowerCase() !== "remote"
            )
            .map(value =>
              value.toLowerCase()
            ),

        role_keywords:
           buildRoleKeywordsFromAreas(
            targetRoleAreas
          ),
      };
    }

    function renderProfileChipList(container, values) {
      container.innerHTML = "";

      if (!Array.isArray(values) || !values.length) {
        const empty = document.createElement("span");
        empty.className = "profile-empty";
        empty.textContent = "Not specified";
        container.appendChild(empty);
        return;
      }

      values.forEach(value => {
        const chip = document.createElement("span");
        chip.className = "profile-chip";
        chip.textContent = value;
        container.appendChild(chip);
      });
    }

    function updateVisibleProfile(profile) {
      currentProfileName.textContent =
        profile.profile_name
        || "Custom matching profile";

      renderProfileChipList(
        currentProfileLocations,
        profile.target_locations
      );

      renderProfileChipList(
        currentProfileRoles,
        profile.target_role_areas
      );
    }

    function safeMatchText(value) {
      if (value === null || value === undefined) {
        return "";
      }

      if (Array.isArray(value)) {
        return value.map(safeMatchText).join(" ");
      }

      return String(value);
    }

    function normalizeMatchText(value) {
      return safeMatchText(value)
        .toLowerCase()
        .replace(/\\s+/g, " ")
        .trim();
    }

    function normalizeLocationText(value) {
      return normalizeMatchText(value)
        .replace(/[,;/|()]+/g, " ")
        .replace(/[-–—]+/g, " ")
        .replace(/\\s+/g, " ")
        .trim();
    }

    function isUnknownLocation(value) {
      const normalized =
        normalizeMatchText(value);

      return new Set([
        "",
        "n/a",
        "na",
        "unknown",
        "unknown location",
        "not specified",
        "not available",
        "tbd",
        "-",
        "--",
      ]).has(normalized);
    }

    const WORK_MODE_ONLY_VALUES = new Set([
      "in office",
      "onsite",
      "on site",
      "hybrid",
      "distributed",
    ]);

    function isWorkModeOnlyLocation(value) {
      return WORK_MODE_ONLY_VALUES.has(
        normalizeLocationText(value)
      );
    }

    const UNRESTRICTED_REMOTE_VALUES = new Set([
      "remote",
      "global remote",
      "remote global",
      "worldwide remote",
      "remote worldwide",
      "work from home",
      "hybrid or remote",
    ]);

    function isRegionRestrictedRemote(value, profile) {
      const location = normalizeLocationText(value);

      if (!containsMatchKeyword(location, "remote")) {
        return false;
      }

      if (UNRESTRICTED_REMOTE_VALUES.has(location)) {
        return false;
      }

      if (
        findMatchKeywords(
          location,
          profile.location_keywords || []
        ).length
      ) {
        return false;
      }

      const removableWords = [
        "remote",
        "hybrid",
        "distributed",
        "in office",
        "onsite",
        "on site",
        "or",
        "and",
      ];

      let remainder = location;

      for (const word of removableWords) {
        const escapedWord = word.replace(
        /[.*+?^${}()|[\\]\\\\]/g,
        "\\\\$&"
        );

        remainder = remainder.replace(
          new RegExp(`\\b${escapedWord}\\b`, "g"),
          " "
        );
      }

      remainder = remainder
        .replace(/\\s+/g, " ")
        .trim();

      return Boolean(remainder);
    }

    function containsMatchKeyword(text, keyword) {
      const normalizedKeyword = normalizeMatchText(keyword);

      if (!normalizedKeyword) {
        return false;
      }

      const simpleToken = /^[a-z0-9+#.-]+$/.test(
        normalizedKeyword
      );

      if (!simpleToken) {
        return text.includes(normalizedKeyword);
      }

      let start = text.indexOf(normalizedKeyword);

      while (start !== -1) {
        const before =
          start > 0
            ? text[start - 1]
            : "";

        const afterIndex =
          start + normalizedKeyword.length;

        const after =
          afterIndex < text.length
            ? text[afterIndex]
            : "";

        const beforeIsAlphaNumeric =
          /[a-z0-9]/.test(before);

        const afterIsAlphaNumeric =
          /[a-z0-9]/.test(after);

        if (
          !beforeIsAlphaNumeric
          && !afterIsAlphaNumeric
        ) {
          return true;
        }

        start = text.indexOf(
          normalizedKeyword,
          start + 1
        );
      }

      return false;
    }

    function findMatchKeywords(text, keywords) {
      if (!Array.isArray(keywords)) {
        return [];
      }

      const matches = [];

      keywords.forEach(keyword => {
        if (
          containsMatchKeyword(text, keyword)
          && !matches.includes(keyword)
        ) {
          matches.push(keyword);
        }
      });

      return matches;
    }

    function readableMatchKeyword(keyword) {
      const value = String(keyword || "");

      const containsChinese = Array
        .from(value)
        .some(character => {
          const code = character.charCodeAt(0);

          return code >= 0x4e00
            && code <= 0x9fff;
        });

      if (containsChinese) {
        return value;
      }

      return value
        .replaceAll("-", " ")
        .split(" ")
        .map(word => {
          if (!word) {
            return word;
          }

          return (
            word.charAt(0).toUpperCase()
            + word.slice(1)
          );
        })
        .join(" ");
    }

    function browserScoreLabel(score) {
      if (score >= 75) {
        return "Strong match";
      }

      if (score >= 55) {
        return "Potential match";
      }

      if (score >= 35) {
        return "Worth exploring";
      }

      return "Low match";
    }

    function scoreJobInBrowser(job, profile) {
      const scoring =
        profile
        && typeof profile.scoring === "object"
          ? profile.scoring
          : {};

      const careerStage =
        profile.career_stage || "early_career";

      const remotePreference =
        profile.remote_preference || "preferred";

      const useEarlyCareerRules =
        careerStage === "early_career";

      const scorePoints = key => {
        const value = Number(scoring[key]);

        return Number.isFinite(value)
          ? value
          : 0;
      };

      const title = normalizeMatchText(
        job.title
      );

     const location = normalizeLocationText(
       job.location
     );

      const description = normalizeMatchText(
        job.description
      );

      const skills = normalizeMatchText(
        job.skills
      );

      const sourceType = normalizeMatchText(
        job.source_type
      );

      const roleText = title;

      const skillText =
        sourceType === "china_company_career"
          ? title
          : [title, skills]
              .filter(Boolean)
              .join(" ");

      const fullText = [
        title,
        location,
        description,
        skills,
      ]
        .filter(Boolean)
        .join(" ");

      let score = 0;

      const goodFit = [];
      const watchOut = [];

      const locationMatches =
        findMatchKeywords(
          location,
          profile.location_keywords
        );

      const remoteMatches =
        findMatchKeywords(
          location,
          profile.remote_keywords
        );

    const restrictedRemoteMatches =
      findMatchKeywords(
        location,
        profile.restricted_remote_keywords
      );

    const regionRestrictedRemote =
      isRegionRestrictedRemote(
        job.location,
        profile
      );

    if (
      restrictedRemoteMatches.length ||
      regionRestrictedRemote
    ) {
        score += scorePoints(
          "restricted_remote_penalty"
        );

        watchOut.push(
          `Remote role appears region-restricted: ${
            safeMatchText(job.location)
          }`
         );
      } else if (locationMatches.length) {
        score += scorePoints(
          "location_match"
        );

        const displayedLocation =
          safeMatchText(job.location)
          || readableMatchKeyword(
            locationMatches[0]
          );

        goodFit.push(
          `Target location: ${displayedLocation}`
        );
      } else if (remoteMatches.length) {
        if (remotePreference === "preferred") {
         score += scorePoints(
           "remote_match"
          );

          goodFit.push(
            "Remote-friendly location"
          );
        }

      } else if (
      !isUnknownLocation(job.location)
      && !isWorkModeOnlyLocation(job.location)
    ) {
        score += scorePoints(
          "location_mismatch_penalty"
        );

        watchOut.push(
          `Location outside current targets: ${
            safeMatchText(job.location)
          }`
        );
      }

      const roleMatches =
        findMatchKeywords(
          roleText,
          profile.role_keywords
        );

      if (roleMatches.length) {
        score += scorePoints(
          "role_match"
        );

        const labels = roleMatches
          .slice(0, 2)
          .map(readableMatchKeyword);

        goodFit.push(
          `Preferred role: ${labels.join(", ")}`
        );
      }

      const earlyCareerMatches =
        findMatchKeywords(
          title,
          profile.early_career_keywords
        );

      if (
        useEarlyCareerRules
        && earlyCareerMatches.length
      ) {
        score += scorePoints(
          "early_career_match"
        );

        const labels = earlyCareerMatches
          .slice(0, 2)
          .map(readableMatchKeyword);

        goodFit.push(
          `Early-career signal: ${
            labels.join(", ")
          }`
        );
      }

      const skillMatches =
        findMatchKeywords(
          skillText,
          profile.skill_keywords
        );

      if (skillMatches.length) {
        const skillMatchMax =
          scorePoints("skill_match_max");

        const pointsPerSkill =
          Math.max(
            1,
            Math.floor(skillMatchMax / 4)
          );

        const skillPoints =
          Math.min(
            skillMatchMax,
            skillMatches.length
              * pointsPerSkill
          );

        score += skillPoints;

        const labels = skillMatches
          .slice(0, 4)
          .map(readableMatchKeyword);

        goodFit.push(
          `Matched skills: ${labels.join(", ")}`
        );
      }

        const titleRiskMatches =
          findMatchKeywords(
            title,
            profile.title_risk_keywords
          );

        if (useEarlyCareerRules) {
          titleRiskMatches.forEach(keyword => {
            score += scorePoints(
              "title_risk_penalty"
            );

            watchOut.push(
              `Seniority signal in title: ${
                readableMatchKeyword(keyword)
              }`
            );
          });
        }

        const riskMatches =
          findMatchKeywords(
            fullText,
            profile.risk_keywords
          );

        if (useEarlyCareerRules) {
          riskMatches.forEach(keyword => {
            score += scorePoints(
              "risk_keyword_penalty"
            );

            watchOut.push(
              `Seniority or experience signal: ${
                readableMatchKeyword(keyword)
              }`
            );
          });
        }

      const strongExcludeMatches =
        findMatchKeywords(
          fullText,
          profile.strong_exclude_keywords
        );

      strongExcludeMatches.forEach(keyword => {
        score += scorePoints(
          "strong_exclude_penalty"
        );

        watchOut.push(
          `Specialized requirement: ${
            readableMatchKeyword(keyword)
          }`
        );
      });

      const minimumScore =
        Number.isFinite(
          Number(scoring.min_score)
        )
          ? Number(scoring.min_score)
          : 0;

      const maximumScore =
        Number.isFinite(
          Number(scoring.max_score)
        )
          ? Number(scoring.max_score)
          : 100;

      score = Math.max(
        minimumScore,
        Math.min(maximumScore, score)
      );

      return {
        ...job,
        match_score: score,
        match_label:
          browserScoreLabel(score),
        good_fit: goodFit,
        watch_out: watchOut,
      };
    }

    function rescoreJobs(profile) {
      jobs.forEach(job => {
        Object.assign(
          job,
          scoreJobInBrowser(
            job,
            profile
          )
        );
      });
    }

    function populateProfileEditor(profile) {
      const safeProfile = profile && typeof profile === "object"
        ? profile
        : {};

      profileNameInput.value = safeProfile.profile_name || "";

      profileCareerStageSelect.value =
        safeProfile.career_stage || "early_career";

      profileRemotePreferenceSelect.value =
        safeProfile.remote_preference || "preferred";

        profileLocationsInput.value = editorListValue(
        safeProfile.target_locations
      );

      profileRolesInput.value = editorListValue(
        safeProfile.target_role_areas
      );

      profileSkillsInput.value = editorListValue(
        safeProfile.skill_keywords
      );
    }

    function showProfileEditor() {
      populateProfileEditor(activeProfile);

      if (typeof profileEditorDialog.showModal === "function") {
        profileEditorDialog.showModal();
      } else {
        profileEditorDialog.setAttribute("open", "");
      }
    }

    function hideProfileEditor() {
      if (typeof profileEditorDialog.close === "function") {
        profileEditorDialog.close();
      } else {
        profileEditorDialog.removeAttribute("open");
      }
    }

    openProfileEditor.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      showProfileEditor();
    });

    closeProfileEditor.addEventListener(
      "click",
      hideProfileEditor
    );

    cancelProfileEditor.addEventListener(
      "click",
      hideProfileEditor
    );

    resetProfileEditor.addEventListener(
      "click",
      () => {
        resetActiveProfile();
      }
    );

    profileEditorDialog.addEventListener("click", event => {
      if (event.target === profileEditorDialog) {
        hideProfileEditor();
      }
    });

    profileEditorForm.addEventListener("submit", event => {
      event.preventDefault();

      activeProfile = buildProfileFromEditor();

      saveActiveProfile(activeProfile);

      updateVisibleProfile(activeProfile);

      rescoreJobs(activeProfile);

      applyFilters();


      console.log(
        "Applied matching profile:",
        activeProfile
      );

      hideProfileEditor();
    });

    function uniqueSorted(values) {
      return [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b));
    }

    function addOptions(select, values) {
      values.forEach(value => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
      });
    }

    addOptions(locationSelect, uniqueSorted(jobs.map(job => job.location)));
    addOptions(companySelect, uniqueSorted(jobs.map(job => job.company)));
    addOptions(sourceSelect, uniqueSorted(jobs.map(job => job.source)));

    function setSelectIfOptionExists(select, value) {
  if (!value) return;

  const option = [...select.options].find(item => item.value === value);

  if (option) {
    select.value = value;
  }
}

function readFiltersFromUrl() {
  const params = new URLSearchParams(window.location.search);

  searchInput.value = params.get("q") || "";

  setSelectIfOptionExists(locationSelect, params.get("location"));
  setSelectIfOptionExists(companySelect, params.get("company"));
  setSelectIfOptionExists(sourceSelect, params.get("source"));
  setSelectIfOptionExists(categorySelect, params.get("category"));

  const minimumMatch = params.get("min_match") || "";
  const allowedMatchScores = new Set(["", "35", "55", "75"]);
  const safeMinimumMatch = allowedMatchScores.has(minimumMatch)
    ? minimumMatch
    : "";

  setSelectIfOptionExists(matchSelect, safeMinimumMatch);
  setSelectIfOptionExists(freshnessSelect, params.get("freshness"));
  setSelectIfOptionExists(sortSelect, params.get("sort"));
}

function updateUrlFromFilters() {
  const params = new URLSearchParams();

  if (searchInput.value.trim()) {
    params.set("q", searchInput.value.trim());
  }

  if (locationSelect.value) {
    params.set("location", locationSelect.value);
  }

  if (companySelect.value) {
    params.set("company", companySelect.value);
  }

  if (sourceSelect.value) {
    params.set("source", sourceSelect.value);
  }

  if (categorySelect.value) {
    params.set("category", categorySelect.value);
  }

  if (matchSelect.value) {
    params.set("min_match", matchSelect.value);
  }

  if (freshnessSelect.value) {
    params.set("freshness", freshnessSelect.value);
  }

  if (sortSelect.value && sortSelect.value !== "updated_desc") {
    params.set("sort", sortSelect.value);
  }

  const query = params.toString();
  const newUrl = query
    ? `${window.location.pathname}?${query}`
    : window.location.pathname;

  window.history.replaceState({}, "", newUrl);
}

    function includesAny(text, keywords) {
      return keywords.some(keyword => text.includes(keyword));
    }

    function isMainlandChina(job) {
      const text = `${job.location} ${job.source_type} ${job.audience}`.toLowerCase();

      if (job.audience === "china_based_job_seekers") return true;
      if (["china_local_static", "china_company_career"].includes(job.source_type)) return true;
      if (text.includes("hong kong") || text.includes("taiwan")) return false;

      return text.includes("china");
    }

    function isRemote(job) {
      return includesAny(job.search_text, ["remote", "global remote", "worldwide", "work from home", "distributed"]);
    }

    function isInternship(job) {
      return includesAny(job.search_text, ["intern", "internship", "graduate", "trainee", "entry level", "entry-level", "junior", "campus", "new grad", "实习", "校招", "应届", "管培"]);
    }

    function isSales(job) {
      const title = job.title.toLowerCase();
      return includesAny(title, ["sales", "account executive", "account manager", "business development", "partnership", "customer success", "client", "revenue"]);
    }

    function isMarketing(job) {
      const title = job.title.toLowerCase();
      return includesAny(title, ["marketing", "communication", "communications", "brand", "content", "social media", "event", "events", "pr", "growth"]);
    }

    function isAiData(job) {
      const title = job.title.toLowerCase();
      return includesAny(title, ["ai", "artificial intelligence", "machine learning", "data", "analytics", "analyst", "business intelligence", "sql", "python", "llm"]);
    }

    function matchesCategory(job, category) {
      if (!category) return true;
      if (category === "mainland") return isMainlandChina(job);
      if (category === "remote") return isRemote(job);
      if (category === "internship") return isInternship(job);
      if (category === "sales") return isSales(job);
      if (category === "marketing") return isMarketing(job);
      if (category === "ai_data") return isAiData(job);
      return true;
      }

    function dateValue(value) {
      if (!value || value === "Unknown") return 0;

      const parsed = Date.parse(`${value}T00:00:00`);
      if (Number.isNaN(parsed)) return 0;

      return parsed;
    }

    function daysSinceUpdated(value) {
      const updated = dateValue(value);
      if (!updated) return Infinity;

      const generated = Date.parse("__GENERATED_DATE__T00:00:00");
      if (Number.isNaN(generated)) return Infinity;

      const diff = generated - updated;
      return diff / (1000 * 60 * 60 * 24);
    }

    function matchesFreshness(job, freshnessDays) {
      if (!freshnessDays) return true;
      return daysSinceUpdated(job.posted_date) <= Number(freshnessDays);
    }

    function matchScoreValue(job) {
      if (
        job.match_score === null
        || job.match_score === undefined
      ) {
        return -1;
      }

      const score = Number(job.match_score);

      return Number.isFinite(score) ? score : -1;
    }

    function matchesMinimumScore(job, minimumScore) {
      if (!minimumScore) return true;

      return matchScoreValue(job) >= Number(minimumScore);
    }

    function compareJobs(a, b, sortMode) {
      if (sortMode === "match_desc") {
            const scoreA = Number.isFinite(Number(a.match_score))
              ? Number(a.match_score)
              : -1;

        const scoreB = Number.isFinite(Number(b.match_score))
          ? Number(b.match_score)
          : -1;

        return scoreB - scoreA
          || dateValue(b.posted_date) - dateValue(a.posted_date)
          || a.company.localeCompare(b.company)
          || a.title.localeCompare(b.title);
      }
     if (sortMode === "updated_asc") {
        return dateValue(a.posted_date) - dateValue(b.posted_date)
          || a.company.localeCompare(b.company)
          || a.title.localeCompare(b.title);
      }

    if (sortMode === "company") {
        return a.company.localeCompare(b.company)
          || a.title.localeCompare(b.title);
    }

    if (sortMode === "title") {
      return a.title.localeCompare(b.title)
       || a.company.localeCompare(b.company);
    }

    return dateValue(b.posted_date) - dateValue(a.posted_date)
      || a.company.localeCompare(b.company)
      || a.title.localeCompare(b.title);
  }

    function escapeHtml(text) {
      return String(text || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function renderJobs(filteredJobs) {
      jobsList.innerHTML = "";

      visibleJobs.textContent = filteredJobs.length;
      resultSummary.textContent = `Showing ${filteredJobs.length} of ${jobs.length} jobs`;

      if (!filteredJobs.length) {
        jobsList.innerHTML = `<div class="empty">No matching jobs found. Try adjusting your filters.</div>`;
        return;
      }

      filteredJobs.slice(0, 300).forEach(job => {
        const card = document.createElement("article");
        card.className = "job-card";

        const titleHtml = job.url
          ? `<a href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(job.title)}</a>`
          : escapeHtml(job.title);

                const hasMatchScore =
          job.match_score !== null
          && job.match_score !== undefined
          && Number.isFinite(Number(job.match_score));

        const matchScore = hasMatchScore
          ? Number(job.match_score)
          : null;

        const goodFit = Array.isArray(job.good_fit)
          ? job.good_fit.slice(0, 3)
          : [];

        const watchOut = Array.isArray(job.watch_out)
          ? job.watch_out.slice(0, 2)
          : [];

        const matchHtml = hasMatchScore
          ? `
            <div class="match-panel">
              <div class="match-header">
                <span class="match-score">
                  Match ${matchScore}/100
                </span>
                ${
                  job.match_label
                    ? `<span class="match-label">${escapeHtml(job.match_label)}</span>`
                    : ""
                }
              </div>

              ${
                goodFit.length
                  ? `
                    <p class="match-reason">
                      <strong>Good fit:</strong>
                      ${goodFit.map(reason => escapeHtml(reason)).join(" · ")}
                    </p>
                  `
                  : ""
              }

              ${
                watchOut.length
                  ? `
                    <p class="match-reason watch-out">
                      <strong>Watch out:</strong>
                      ${watchOut.map(reason => escapeHtml(reason)).join(" · ")}
                    </p>
                  `
                  : ""
              }
            </div>
          `
          : "";


        card.innerHTML = `
          <h2 class="job-title">${titleHtml}</h2>
          <div class="meta">
            <span class="badge">${escapeHtml(job.company)}</span>
            <span class="badge">${escapeHtml(job.location)}</span>
            <span class="badge">Updated: ${escapeHtml(job.posted_date)}</span>
            <span class="badge">Source: ${escapeHtml(job.source)}</span>
            <span class="badge">${escapeHtml(job.source_type_label || job.source_type)}</span>
          </div>
          ${matchHtml}
          ${job.description ? `<p class="description">${escapeHtml(job.description)}</p>` : ""}
        `;

        jobsList.appendChild(card);
      });

      if (filteredJobs.length > 300) {
        const notice = document.createElement("div");
        notice.className = "empty";
        notice.textContent = `Only the first 300 results are shown. Narrow your filters to see more specific jobs.`;
        jobsList.appendChild(notice);
      }
    }

    function applyFilters() {
      const query = searchInput.value.trim().toLowerCase();
      const location = locationSelect.value;
      const company = companySelect.value;
      const source = sourceSelect.value;
      const category = categorySelect.value;
      const minimumMatch = matchSelect.value;
      const freshness = freshnessSelect.value;
      const sortMode = sortSelect.value;

      const filteredJobs = jobs.filter(job => {
        if (query && !job.search_text.includes(query)) return false;
        if (location && job.location !== location) return false;
        if (company && job.company !== company) return false;
        if (source && job.source !== source) return false;
        if (!matchesCategory(job, category)) return false;
        if (!matchesMinimumScore(job, minimumMatch)) return false;
        if (!matchesFreshness(job, freshness)) return false;
        return true;
      });

      filteredJobs.sort((a, b) => compareJobs(a, b, sortMode));

      const labels = [];
      if (query) labels.push(`Search: ${query}`);
      if (location) labels.push(`Location: ${location}`);
      if (company) labels.push(`Company: ${company}`);
      if (source) labels.push(`Source: ${source}`);
      if (category) labels.push(`Category: ${category}`);

    const matchLabels = {
      "75": "Strong matches (75+)",
      "55": "Potential or better (55+)",
      "35": "Worth exploring or better (35+)",
    };

    if (minimumMatch) {
      labels.push(
        `Match: ${matchLabels[minimumMatch] || `${minimumMatch}+`}`
      );
    }

    if (freshness) {
      labels.push(`Updated in last ${freshness} days`);
    }
      const sortLabels = {
        match_desc: "Best Match first",
        updated_asc: "Oldest first",
        company: "Company A-Z",
        title: "Title A-Z",
      };

      if (sortMode && sortMode !== "updated_desc") {
        labels.push(`Sort: ${sortLabels[sortMode] || sortMode}`);
      }

      activeFilters.textContent = labels.length ? labels.join(" · ") : "No active filters";
      updateUrlFromFilters();
      renderJobs(filteredJobs);
    }

    [searchInput, locationSelect, companySelect, sourceSelect, categorySelect, matchSelect, freshnessSelect, sortSelect].forEach(element => {
      element.addEventListener("input", applyFilters);
      element.addEventListener("change", applyFilters);
    });

    document.querySelectorAll("button[data-category]").forEach(button => {
      button.addEventListener("click", () => {
        categorySelect.value = button.dataset.category;
        applyFilters();
      });
    });

    document.querySelectorAll("button[data-location]").forEach(button => {
      button.addEventListener("click", () => {
        const targetLocation = button.dataset.location.toLowerCase();
        const option = [...locationSelect.options].find(item =>
          item.value.toLowerCase().includes(targetLocation)
        );

        if (option) {
          locationSelect.value = option.value;
        }

        applyFilters();
      });
    });

    document.querySelectorAll("button[data-freshness]").forEach(button => {
      button.addEventListener("click", () => {
        freshnessSelect.value = button.dataset.freshness;
        applyFilters();
      });
    });

    clearFilters.addEventListener("click", () => {
      searchInput.value = "";
      locationSelect.value = "";
      companySelect.value = "";
      sourceSelect.value = "";
      categorySelect.value = "";
      matchSelect.value = "";
      freshnessSelect.value = "";
      sortSelect.value = "updated_desc";
      applyFilters();
    });

    copyLinkButton.addEventListener("click", async () => {
      applyFilters();

      try {
        await navigator.clipboard.writeText(window.location.href);
        shareStatus.textContent = "Link copied";
      } catch (error) {
        shareStatus.textContent = "Copy failed. Use the browser address bar.";
      }

      window.setTimeout(() => {
        shareStatus.textContent = "";
      }, 2500);
    });

    const storedProfile =
      loadStoredProfile();

    if (storedProfile) {
      activeProfile = storedProfile;

      updateVisibleProfile(
        activeProfile
      );

      rescoreJobs(
        activeProfile
      );
    }

    readFiltersFromUrl();
    applyFilters();
  </script>
</body>
</html>
"""

    return (
        html_template
        .replace("__GENERATED_DATE__", today)
        .replace("__JOBS_JSON__", jobs_json)
        .replace("__PROFILE_NAME__", profile_name_html)
        .replace("__PROFILE_DESCRIPTION__", profile_description_html)
        .replace("__PROFILE_LOCATIONS__", profile_locations_html)
        .replace("__PROFILE_ROLES__", profile_roles_html)
        .replace(
            "__PROFILE_EDITOR_JSON__",
            profile_editor_json,
            )
        .replace(
            "__POSITIVE_SCORE_RULES__",
            positive_score_rules_html,
        )
        .replace(
            "__RISK_SCORE_RULES__",
            risk_score_rules_html,
        )
    )


def generate_web_dashboard(jobs=None, profile=None):
    if jobs is None:
        jobs = load_jobs()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    html = build_dashboard_html(jobs, profile)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    return OUTPUT_FILE


if __name__ == "__main__":
    from match_jobs import PROFILE_FILE, load_json, score_jobs

    profile = load_json(PROFILE_FILE)
    matched_jobs = score_jobs(load_jobs(), profile)

    output_file = generate_web_dashboard(matched_jobs, profile)
    print(f"Generated matched web dashboard at {output_file}")
