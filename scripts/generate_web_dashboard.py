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

def format_date(value):
    ...
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
    ...

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

def build_dashboard_html(jobs):
    today = date.today().isoformat()
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

        <select id="freshnessSelect">
          <option value="">All dates</option>
          <option value="7">Updated in last 7 days</option>
          <option value="14">Updated in last 14 days</option>
          <option value="30">Updated in last 30 days</option>
        </select>

        <select id="sortSelect">
          <option value="updated_desc">Newest first</option>
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

    const searchInput = document.getElementById("searchInput");
    const locationSelect = document.getElementById("locationSelect");
    const companySelect = document.getElementById("companySelect");
    const sourceSelect = document.getElementById("sourceSelect");
    const categorySelect = document.getElementById("categorySelect");
    const freshnessSelect = document.getElementById("freshnessSelect");
    const sortSelect = document.getElementById("sortSelect");
    const jobsList = document.getElementById("jobsList");
    const resultSummary = document.getElementById("resultSummary");
    const activeFilters = document.getElementById("activeFilters");
    const totalJobs = document.getElementById("totalJobs");
    const visibleJobs = document.getElementById("visibleJobs");
    const clearFilters = document.getElementById("clearFilters");
    const copyLinkButton = document.getElementById("copyLinkButton");
    const shareStatus = document.getElementById("shareStatus");

    totalJobs.textContent = jobs.length;

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

    function compareJobs(a, b, sortMode) {
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

        card.innerHTML = `
          <h2 class="job-title">${titleHtml}</h2>
          <div class="meta">
            <span class="badge">${escapeHtml(job.company)}</span>
            <span class="badge">${escapeHtml(job.location)}</span>
            <span class="badge">Updated: ${escapeHtml(job.posted_date)}</span>
            <span class="badge">Source: ${escapeHtml(job.source)}</span>
            <span class="badge">${escapeHtml(job.source_type_label || job.source_type)}</span>
          </div>
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
      const freshness = freshnessSelect.value;
      const sortMode = sortSelect.value;

      const filteredJobs = jobs.filter(job => {
        if (query && !job.search_text.includes(query)) return false;
        if (location && job.location !== location) return false;
        if (company && job.company !== company) return false;
        if (source && job.source !== source) return false;
        if (!matchesCategory(job, category)) return false;
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
      if (freshness) labels.push(`Updated in last ${freshness} days`);
      if (sortMode && sortMode !== "updated_desc") labels.push(`Sort: ${sortMode}`);

      activeFilters.textContent = labels.length ? labels.join(" · ") : "No active filters";
      updateUrlFromFilters();
      renderJobs(filteredJobs);
    }

    [searchInput, locationSelect, companySelect, sourceSelect, categorySelect, freshnessSelect, sortSelect].forEach(element => {
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
    )


def generate_web_dashboard(jobs=None):
    if jobs is None:
        jobs = load_jobs()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    html = build_dashboard_html(jobs)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    return OUTPUT_FILE


if __name__ == "__main__":
    output_file = generate_web_dashboard()
    print(f"Generated web dashboard at {output_file}")