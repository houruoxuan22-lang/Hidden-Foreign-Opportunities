from scripts.match_jobs import (
    PROFILE_FILE,
    contains_keyword,
    load_json,
    normalize_text,
    score_job,
    score_label,
)

def load_default_profile():
    return load_json(PROFILE_FILE)

def test_normalize_text_lowercases_and_collapses_spaces():
    result = normalize_text("  Marketing   Communications  ")

    assert result == "marketing communications"


def test_contains_keyword_matches_complete_word():
    assert contains_keyword(
        "senior marketing manager",
        "manager",
    )


def test_contains_keyword_does_not_match_inside_another_word():
    assert not contains_keyword(
        "leadership development",
        "lead",
    )


def test_score_label_strong_match():
    assert score_label(75) == "Strong match"
    assert score_label(100) == "Strong match"


def test_score_label_potential_match():
    assert score_label(55) == "Potential match"
    assert score_label(74) == "Potential match"


def test_score_label_worth_exploring():
    assert score_label(35) == "Worth exploring"
    assert score_label(54) == "Worth exploring"


def test_score_label_low_match():
    assert score_label(0) == "Low match"
    assert score_label(34) == "Low match"

def test_score_job_rewards_strong_early_career_fit():
    profile = load_default_profile()

    job = {
        "title": "Marketing Intern",
        "company": "Example Company",
        "location": "Shanghai, China",
        "description": "",
        "skills": [
            "English",
            "Marketing",
            "CRM",
            "Excel",
        ],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert result["match_score"] == 90
    assert result["match_label"] == "Strong match"
    assert result["watch_out"] == []

    assert any(
        reason.startswith("Target location:")
        for reason in result["good_fit"]
    )
    assert any(
        reason.startswith("Preferred role:")
        for reason in result["good_fit"]
    )
    assert any(
        reason.startswith("Early-career signal:")
        for reason in result["good_fit"]
    )
    assert any(
        reason.startswith("Matched skills:")
        for reason in result["good_fit"]
    )


def test_score_job_applies_each_title_seniority_penalty():
    profile = load_default_profile()

    job = {
        "title": "Senior Marketing Manager",
        "company": "Example Company",
        "location": "Shanghai, China",
        "description": "",
        "skills": ["Marketing"],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert result["match_score"] == 25
    assert result["match_label"] == "Low match"

    assert "Seniority signal in title: Senior" in result["watch_out"]
    assert "Seniority signal in title: Manager" in result["watch_out"]


def test_score_job_penalizes_region_restricted_remote_role():
    profile = load_default_profile()

    job = {
        "title": "Marketing Specialist",
        "company": "Example Company",
        "location": "US-Remote",
        "description": "",
        "skills": ["Marketing"],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert result["match_score"] == 30
    assert result["match_label"] == "Low match"

    assert any(
        reason.startswith("Remote role appears region-restricted:")
        for reason in result["watch_out"]
    )

    assert "Remote-friendly location" not in result["good_fit"]


def test_score_job_applies_specialized_qualification_penalty():
    profile = load_default_profile()

    job = {
        "title": "Marketing Intern",
        "company": "Example Company",
        "location": "Shanghai, China",
        "description": "A PhD is required for this position.",
        "skills": ["Marketing"],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert result["match_score"] == 45
    assert result["match_label"] == "Worth exploring"
    assert "Specialized requirement: Phd" in result["watch_out"]


def test_score_job_never_goes_below_zero():
    profile = load_default_profile()

    job = {
        "title": "Senior Director Head Manager Marketing",
        "company": "Example Company",
        "location": "New York, USA",
        "description": (
            "Requires 10+ years and 7+ years of experience. "
            "PhD, doctorate, and security clearance required."
        ),
        "skills": [],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert result["match_score"] == 0
    assert result["match_label"] == "Low match"
    assert len(result["watch_out"]) >= 5


def test_score_job_never_exceeds_one_hundred():
    profile = load_default_profile()

    profile["scoring"]["location_match"] = 80
    profile["scoring"]["role_match"] = 80
    profile["scoring"]["early_career_match"] = 80
    profile["scoring"]["skill_match_max"] = 80

    job = {
        "title": "Marketing Intern",
        "company": "Example Company",
        "location": "Shanghai, China",
        "description": "",
        "skills": [
            "English",
            "Marketing",
            "CRM",
            "Excel",
        ],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert result["match_score"] == 100
    assert result["match_label"] == "Strong match"