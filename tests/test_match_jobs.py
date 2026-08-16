import pytest
@pytest.mark.parametrize(
    "location",
    [
        "Remote US",
        "Remote-US",
        "Remote in the US",
        "Remote in the U.S.",
        "Remote Canada",
        "Remote-Canada",
        "Remote in Canada",
        "Remote UK",
        "Remote in the UK",
        "Remote North America",
    ],
)
def test_score_job_penalizes_restricted_remote_variants(location):
    profile = load_default_profile()

    job = {
        "title": "Marketing Specialist",
        "company": "Example Company",
        "location": location,
        "description": "",
        "skills": ["Marketing"],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert any(
        reason.startswith(
            "Remote role appears region-restricted:"
        )
        for reason in result["watch_out"]
    )

    assert (
        "Remote-friendly location"
        not in result["good_fit"]
    )

@pytest.mark.parametrize(
    ("raw_location", "expected"),
    [
        ("US-Remote", "us remote"),
        ("Remote-US", "remote us"),
        ("Remote, US", "remote us"),
        (
            "Remote (US/Canada)",
            "remote us canada",
        ),
        (
            "Remote, North America",
            "remote north america",
        ),
        (
            "US-Remote; US-Chicago",
            "us remote us chicago",
        ),
        (
            "Toronto, Remote-Canada",
            "toronto remote canada",
        ),
    ],
)
def test_normalize_location_text_handles_common_separators(
    raw_location,
    expected,
):
    assert (
        normalize_location_text(raw_location)
        == expected
    )

@pytest.mark.parametrize(
    "location",
    [
        "Remote, North America",
        "Remote (US/Canada)",
    ],
)
def test_score_job_detects_restricted_remote_after_location_normalization(
    location,
):
    profile = load_default_profile()

    job = {
        "title": "Marketing Specialist",
        "company": "Example Company",
        "location": location,
        "description": "",
        "skills": ["Marketing"],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert any(
        reason.startswith(
            "Remote role appears region-restricted:"
        )
        for reason in result["watch_out"]
    )


@pytest.mark.parametrize(
    "location",
    [
        "In-Office",
        "In Office",
        "On-Site",
        "Onsite",
        "Hybrid",
        "Distributed",
    ],
)
def test_is_work_mode_only_location(location):
    assert is_work_mode_only_location(location)

@pytest.mark.parametrize(
    "location",
    [
        "In-Office",
        "Hybrid",
        "Distributed",
    ],
)
def test_work_mode_only_location_is_not_location_mismatch(
    location,
):
    profile = load_default_profile()

    job = {
        "title": "Marketing Specialist",
        "company": "Example Company",
        "location": location,
        "description": "",
        "skills": ["Marketing"],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert not any(
        reason.startswith(
            "Location outside current targets:"
        )
        for reason in result["watch_out"]
    )
@pytest.mark.parametrize(
    ("location", "should_be_remote"),
    [
        ("Hybrid", False),
        ("Distributed", False),
        ("Remote", True),
        ("Hybrid or Remote", True),
    ],
)
def test_work_mode_remote_classification(
    location,
    should_be_remote,
):
    profile = load_default_profile()

    job = {
        "title": "Marketing Specialist",
        "company": "Example Company",
        "location": location,
        "description": "",
        "skills": ["Marketing"],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    is_remote = (
        "Remote-friendly location"
        in result["good_fit"]
    )

    assert is_remote is should_be_remote

from scripts.match_jobs import (
    PROFILE_FILE,
    contains_keyword,
    load_json,
    normalize_text,
    normalize_location_text,
    score_job,
    score_label,
    is_unknown_location,
    is_work_mode_only_location,
    title_location_fallback,
    is_region_restricted_remote,
)

@pytest.mark.parametrize(
    (
        "title",
        "location",
        "expected_target",
        "expected_geography",
    ),
    [
        (
            "Senior Customer Engineer, Shenzhen",
            "Distributed",
            ["shenzhen"],
            [],
        ),
        (
            "Senior Named Account Executive, North China",
            "Hybrid",
            ["china"],
            [],
        ),
        (
            "Named Account Executive, FSI (Hong Kong)",
            "Hybrid",
            [],
            ["hong kong"],
        ),
        (
            "Software Engineer Intern (Fall 2026) - Austin, TX",
            "In-Office",
            [],
            ["austin"],
        ),
        (
            "Accounting Intern (Fall 2026)",
            "In-Office",
            [],
            [],
        ),
    ],
)
def test_title_location_fallback_for_work_mode_only_locations(
    title,
    location,
    expected_target,
    expected_geography,
):
    profile = load_default_profile()

    target_matches, geography_matches = title_location_fallback(
        {
            "title": title,
            "location": location,
        },
        profile,
    )

    assert target_matches == expected_target
    assert geography_matches == expected_geography

@pytest.mark.parametrize(
    (
        "title",
        "location",
        "expected_location",
    ),
    [
        (
            "Senior Customer Engineer, Shenzhen",
            "Distributed",
            "Shenzhen",
        ),
        (
            "Senior Named Account Executive, North China",
            "Hybrid",
            "China",
        ),
    ],
)
def test_score_job_uses_target_location_from_title_for_work_mode_only_location(
    title,
    location,
    expected_location,
):
    profile = load_default_profile()

    job = {
        "title": title,
        "company": "Example Company",
        "location": location,
        "description": "",
        "skills": [],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert (
        f"Target location in title: {expected_location}"
        in result["good_fit"]
    )

    assert not any(
        reason.startswith("Location outside current targets:")
        for reason in result["watch_out"]
    )


@pytest.mark.parametrize(
    (
        "title",
        "location",
        "expected_location",
    ),
    [
        (
            "Named Account Executive, FSI (Hong Kong)",
            "Hybrid",
            "Hong Kong",
        ),
        (
            "Software Engineer Intern (Fall 2026) - Austin, TX",
            "In-Office",
            "Austin",
        ),
    ],
)
def test_score_job_penalizes_non_target_location_from_title_for_work_mode_only_location(
    title,
    location,
    expected_location,
):
    profile = load_default_profile()

    job = {
        "title": title,
        "company": "Example Company",
        "location": location,
        "description": "",
        "skills": [],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert (
        f"Location in title outside current targets: {expected_location}"
        in result["watch_out"]
    )

    assert not any(
        reason.startswith("Target location in title:")
        for reason in result["good_fit"]
    )

def test_score_job_keeps_work_mode_only_location_neutral_without_title_geography():
    profile = load_default_profile()

    job = {
        "title": "Accounting Intern (Fall 2026)",
        "company": "Example Company",
        "location": "In-Office",
        "description": "",
        "skills": [],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert not any(
        reason.startswith("Target location")
        for reason in result["good_fit"]
    )

    assert not any(
        "Location" in reason
        for reason in result["watch_out"]
    )

@pytest.mark.parametrize(
    "location",
    [
        "Remote India",
        "India, Remote",
        "Texas, USA, Remote",
        "London, United Kingdom, Remote",
        "Thailand, Remote",
        "France, Remote",
        "SF, NYC, remote",
        "New York, San Francisco or Remote",
        "South Africa, Remote",
    ],
)
def test_region_restricted_remote_locations(
    location,
):
    profile = load_default_profile()

    assert is_region_restricted_remote(
        location,
        profile,
    )

@pytest.mark.parametrize(
    "location",
    [
        "Remote",
        "Global Remote",
        "Worldwide Remote",
        "Hybrid or Remote",
        "Shanghai, China, Remote",
        "China, Remote",
    ],
)
def test_unrestricted_or_target_remote_locations(
    location,
):
    profile = load_default_profile()

    assert not is_region_restricted_remote(
        location,
        profile,
    )

@pytest.mark.parametrize(
    "location",
    [
        "Remote India",
        "Texas, USA, Remote",
        "France, Remote",
    ],
)
def test_score_job_penalizes_generic_region_restricted_remote(
    location,
):
    profile = load_default_profile()

    job = {
        "title": "Marketing Specialist",
        "company": "Example Company",
        "location": location,
        "description": "",
        "skills": ["Marketing"],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert (
        "Remote-friendly location"
        not in result["good_fit"]
    )

    assert any(
        reason.startswith(
            "Remote role appears region-restricted:"
        )
        for reason in result["watch_out"]
    )

def load_default_profile():
    return load_json(PROFILE_FILE)

def test_normalize_text_lowercases_and_collapses_spaces():
    result = normalize_text("  Marketing   Communications  ")

    assert result == "marketing communications"

@pytest.mark.parametrize(
    "location",
    [
        "",
        "N/A",
        "NA",
        "Unknown",
        "Unknown Location",
        "Not specified",
        "Not available",
        "TBD",
        "-",
        "--",
    ],
)
def test_is_unknown_location_recognizes_placeholder_values(location):
    assert is_unknown_location(location)


@pytest.mark.parametrize(
    "location",
    [
        "",
        "N/A",
        "Unknown",
        "Not specified",
    ],
)
def test_score_job_does_not_penalize_unknown_location(location):
    profile = load_default_profile()

    job = {
        "title": "Marketing Specialist",
        "company": "Example Company",
        "location": location,
        "description": "",
        "skills": ["Marketing"],
        "source_type": "ats_api",
    }

    result = score_job(job, profile)

    assert not any(
        reason.startswith(
            "Location outside current targets:"
        )
        for reason in result["watch_out"]
    )

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