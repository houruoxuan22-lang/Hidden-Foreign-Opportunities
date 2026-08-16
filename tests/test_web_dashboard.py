import re
import shutil
import subprocess

from scripts.generate_web_dashboard import (
    build_dashboard_html,
    clean_dashboard_description,
    deduplicate_normalized_jobs,
    normalize_job,
)
from scripts.match_jobs import (
    PROFILE_FILE,
    load_json,
)


def sample_scored_job():
    return {
        "title": "Marketing & Communications Specialist",
        "company": "Example Company",
        "location": "Shanghai, China",
        "source": "example_source",
        "source_type": "greenhouse",
        "audience": "china_based_job_seekers",
        "url": "https://example.com/jobs/marketing-specialist",
        "posted_date": "2026-08-05T12:30:00",
        "description": "<p>Plan campaigns and create content.</p>",
        "match_score": 80,
        "match_label": "Strong match",
        "good_fit": [
            "Target location: Shanghai, China",
            "Preferred role: Marketing, Communications",
        ],
        "watch_out": [],
    }


def test_normalize_job_cleans_and_preserves_dashboard_fields():
    normalized = normalize_job(sample_scored_job())

    assert normalized["title"] == "Marketing & Communications Specialist"
    assert normalized["company"] == "Example Company"
    assert normalized["posted_date"] == "2026-08-05"
    assert normalized["description"] == "Plan campaigns and create content."
    assert normalized["source_type"] == "greenhouse"
    assert normalized["source_type_label"] == "Official ATS"
    assert normalized["match_score"] == 80
    assert normalized["match_label"] == "Strong match"
    assert normalized["good_fit"] == [
        "Target location: Shanghai, China",
        "Preferred role: Marketing, Communications",
    ]


def test_dashboard_description_removes_navigation_noise():
    description = (
        "Skip to main content View Profile "
        "Search by keyword Search by location "
        "Show more options Work area all Career status all"
    )

    assert clean_dashboard_description(description) == ""


def test_deduplicate_jobs_uses_normalized_url():
    first_job = normalize_job(sample_scored_job())

    duplicate_job = normalize_job(
        {
            **sample_scored_job(),
            "title": "Duplicate title",
            "url": "https://example.com/jobs/marketing-specialist/",
        }
    )

    unique_jobs = deduplicate_normalized_jobs(
        [first_job, duplicate_job]
    )

    assert len(unique_jobs) == 1
    assert unique_jobs[0]["title"] == (
        "Marketing & Communications Specialist"
    )

def test_deduplicate_jobs_uses_greenhouse_job_id_across_url_changes():
    jobs = [
        {
            "company": "Stripe",
            "source": "greenhouse",
            "title": "Security Analyst",
            "location": "Remote",
            "url": "https://boards.greenhouse.io/stripe/jobs/123?gh_jid=7893199",
        },
        {
            "company": "Stripe",
            "source": "greenhouse",
            "title": "Security Analyst",
            "location": "Remote",
            "url": "https://stripe.com/jobs/search?foo=bar&gh_jid=7893199",
        },
    ]

    deduped = deduplicate_normalized_jobs(jobs)

    assert len(deduped) == 1

def test_dashboard_contains_profile_and_scoring_explanation():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert profile["profile_name"] in dashboard_html
    assert "Current matching profile" in dashboard_html
    assert "How the match score is calculated" in dashboard_html
    assert "Target location match" in dashboard_html
    assert "Preferred role match" in dashboard_html
    assert "Specialized qualification requirement" in dashboard_html
    assert "+25" in dashboard_html
    assert "-30" in dashboard_html

    assert "Best Match first" in dashboard_html
    assert "Strong matches (75+)" in dashboard_html
    assert '"match_score": 80' in dashboard_html

    assert "__PROFILE_NAME__" not in dashboard_html
    assert "__PROFILE_DESCRIPTION__" not in dashboard_html
    assert "__PROFILE_LOCATIONS__" not in dashboard_html
    assert "__PROFILE_ROLES__" not in dashboard_html
    assert "__POSITIVE_SCORE_RULES__" not in dashboard_html
    assert "__RISK_SCORE_RULES__" not in dashboard_html
    assert "__JOBS_JSON__" not in dashboard_html

    assert 'id="openProfileEditor"' in dashboard_html
    assert 'id="profileEditorDialog"' in dashboard_html
    assert 'id="profileLocationsInput"' in dashboard_html
    assert 'id="profileRolesInput"' in dashboard_html
    assert 'id="profileSkillsInput"' in dashboard_html
    assert 'id="profileCareerStageSelect"' in dashboard_html
    assert 'id="profileRemotePreferenceSelect"' in dashboard_html
    assert "function populateProfileEditor(profile)" in dashboard_html
    assert "function showProfileEditor()" in dashboard_html
    assert "function hideProfileEditor()" in dashboard_html

def test_dashboard_contains_region_restricted_remote_scoring():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert "const UNRESTRICTED_REMOTE_VALUES = new Set([" in dashboard_html
    assert "function isRegionRestrictedRemote(value, profile)" in dashboard_html
    assert "const regionRestrictedRemote =" in dashboard_html
    assert "isRegionRestrictedRemote(" in dashboard_html
    assert "restrictedRemoteMatches.length ||" in dashboard_html
    assert "regionRestrictedRemote" in dashboard_html
    assert '"restricted_remote_penalty"' in dashboard_html

def test_dashboard_contains_title_location_fallback_scoring():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert "const TITLE_GEOGRAPHY_HINT_KEYWORDS = [" in dashboard_html
    assert '"hong kong"' in dashboard_html
    assert '"austin"' in dashboard_html

    assert "function titleLocationFallback(job, profile)" in dashboard_html
    assert "const titleLocationResult =" in dashboard_html
    assert "const titleLocationMatches =" in dashboard_html
    assert "const titleGeographyMatches =" in dashboard_html

    assert "Target location in title:" in dashboard_html
    assert "Location in title outside current targets:" in dashboard_html

    assert (
        "profile.location_keywords || []"
        in dashboard_html
    )

def test_dashboard_suppresses_specialist_early_career_when_title_has_risk():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert "let earlyCareerMatches =" in dashboard_html
    assert 'earlyCareerMatches.includes("specialist")' in dashboard_html
    assert "&& titleRiskMatches.length" in dashboard_html
    assert (
        'keyword => keyword !== "specialist"'
        in dashboard_html
    )

def test_dashboard_syncs_quick_button_active_states():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert "function setQuickButtonActive(button, isActive)" in dashboard_html
    assert 'button.classList.toggle("active", isActive)' in dashboard_html
    assert '"aria-pressed"' in dashboard_html
    assert "function syncQuickButtonStates()" in dashboard_html
    assert "syncQuickButtonStates();" in dashboard_html

def test_dashboard_freshness_uses_last_seen_not_posted_date():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert '"last_seen"' in dashboard_html
    assert "daysSinceUpdated(job.last_seen)" in dashboard_html
    assert "daysSinceUpdated(job.posted_date)" not in dashboard_html

def test_dashboard_includes_possibly_closed_status():
    profile = load_json(PROFILE_FILE)
    job = sample_scored_job()
    job["possibly_closed"] = True

    dashboard_html = build_dashboard_html(
        [job],
        profile,
    )

    assert '"possibly_closed": true' in dashboard_html

def test_dashboard_displays_possibly_closed_badge():
    profile = load_json(PROFILE_FILE)
    job = sample_scored_job()
    job["possibly_closed"] = True

    dashboard_html = build_dashboard_html(
        [job],
        profile,
    )

    assert "Possibly closed" in dashboard_html
    assert 'class="badge badge-warning">Possibly closed</span>' in dashboard_html


def test_dashboard_recency_sort_uses_last_seen_not_posted_date():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert "dateValue(b.last_seen) - dateValue(a.last_seen)" in dashboard_html
    assert "dateValue(a.last_seen) - dateValue(b.last_seen)" in dashboard_html
    assert "dateValue(b.posted_date) - dateValue(a.posted_date)" not in dashboard_html
    assert "dateValue(a.posted_date) - dateValue(b.posted_date)" not in dashboard_html

def test_dashboard_displays_seen_dates_and_source_date():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert "Seen in last 7 days" in dashboard_html
    assert "Recently seen first" in dashboard_html
    assert "Least recently seen first" in dashboard_html
    assert "Last seen:" in dashboard_html
    assert "First seen:" in dashboard_html
    assert "Source date:" in dashboard_html
    assert "Updated:" not in dashboard_html

def test_dashboard_uses_safe_fallback_profile():
    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        None,
    )

    assert "Default matching profile" in dashboard_html
    assert (
        "This dashboard currently uses a default matching profile."
        in dashboard_html
    )
    assert "Not specified" in dashboard_html
    assert "No scoring rules configured." in dashboard_html



def test_embedded_job_json_escapes_script_closing_tags():
    dangerous_job = {
        **sample_scored_job(),
        "title": "</script><script>alert('test')</script>",
    }

    dashboard_html = build_dashboard_html(
        [dangerous_job],
        load_json(PROFILE_FILE),
    )

    assert "<\\/script>" in dashboard_html

def test_generated_dashboard_javascript_has_valid_syntax(tmp_path):
    node = shutil.which("node")

    assert node is not None, (
        "Node.js is required to validate dashboard JavaScript."
    )

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        load_json(PROFILE_FILE),
    )

    scripts = re.findall(
        r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>",
        dashboard_html,
        flags=re.S,
    )

    assert scripts, (
        "Expected at least one inline JavaScript block."
    )

    for index, script in enumerate(scripts):
        script_path = (
            tmp_path
            / f"dashboard-script-{index}.js"
        )

        script_path.write_text(
            script,
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                node,
                "--check",
                str(script_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            "Generated dashboard contains "
            "invalid JavaScript:\n"
            f"{result.stderr}"
        )

def test_dashboard_uses_secondary_job_metadata_line():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert ".meta-secondary {" in dashboard_html
    assert '<div class="meta-secondary">' in dashboard_html
    assert "First seen:" in dashboard_html
    assert "Source date:" in dashboard_html
    assert "Source:" in dashboard_html

def test_dashboard_includes_official_posting_cta():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert ".job-actions {" in dashboard_html
    assert ".job-link {" in dashboard_html
    assert "Open official posting ↗" in dashboard_html
    assert 'target="_blank"' in dashboard_html
    assert 'rel="noopener noreferrer"' in dashboard_html

def test_dashboard_empty_state_can_clear_filters():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert 'id="emptyClearFilters"' in dashboard_html
    assert "function resetFilters()" in dashboard_html
    assert (
        '.getElementById("emptyClearFilters")'
        in dashboard_html
    )
    assert (
        '.addEventListener("click", resetFilters)'
        in dashboard_html
    )

def test_dashboard_uses_clear_profile_labels_and_target_quick_locations():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert ">Target locations</p>" in dashboard_html
    assert ">Target role areas</p>" in dashboard_html

    assert (
        '<button data-location="Shenzhen">Shenzhen</button>'
        in dashboard_html
    )

    assert (
        '<button data-location="Chicago">Chicago</button>'
        not in dashboard_html
    )

def test_dashboard_styles_match_scores_by_score_band():
    profile = load_json(PROFILE_FILE)

    dashboard_html = build_dashboard_html(
        [sample_scored_job()],
        profile,
    )

    assert ".match-score.score-worth {" in dashboard_html
    assert ".match-score.score-potential {" in dashboard_html
    assert ".match-score.score-strong {" in dashboard_html

    assert "function matchScoreClass(score)" in dashboard_html
    assert 'return "score-strong";' in dashboard_html
    assert 'return "score-potential";' in dashboard_html
    assert 'return "score-worth";' in dashboard_html

    assert (
        'class="match-score ${matchScoreClass(matchScore)}"'
        in dashboard_html
    )