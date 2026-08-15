from run import apply_seen_metadata, job_identity


def test_job_identity_normalizes_url_case_and_trailing_slash():
    first = {
        "url": "HTTPS://EXAMPLE.COM/jobs/123/",
    }
    second = {
        "url": "https://example.com/jobs/123",
    }

    assert job_identity(first) == job_identity(second)


def test_job_identity_preserves_job_query_parameter():
    first = {
        "url": "https://stripe.com/jobs/search?gh_jid=7893199",
    }
    second = {
        "url": "https://stripe.com/jobs/search?gh_jid=7993151",
    }

    assert job_identity(first) != job_identity(second)


def test_job_identity_falls_back_to_company_title_location():
    first = {
        "company": " Example Company ",
        "title": "Marketing Specialist",
        "location": "Shanghai, China",
    }
    second = {
        "company": "example company",
        "title": " marketing specialist ",
        "location": "SHANGHAI, CHINA",
    }

    assert job_identity(first) == job_identity(second)

def test_apply_seen_metadata_sets_first_and_last_seen_for_new_job():
    jobs = [
        {
            "url": "https://example.com/jobs/123",
            "title": "Marketing Specialist",
        }
    ]

    result = apply_seen_metadata(
        jobs,
        existing_jobs=[],
        seen_at="2026-08-16T00:50:00+08:00",
    )

    assert result[0]["first_seen"] == "2026-08-16T00:50:00+08:00"
    assert result[0]["last_seen"] == "2026-08-16T00:50:00+08:00"


def test_apply_seen_metadata_preserves_first_seen_and_updates_last_seen():
    existing_jobs = [
        {
            "url": "https://example.com/jobs/123",
            "first_seen": "2026-08-10T09:00:00+08:00",
            "last_seen": "2026-08-15T09:00:00+08:00",
        }
    ]
    jobs = [
        {
            "url": "https://example.com/jobs/123/",
            "title": "Marketing Specialist",
        }
    ]

    result = apply_seen_metadata(
        jobs,
        existing_jobs,
        seen_at="2026-08-16T00:50:00+08:00",
    )

    assert result[0]["first_seen"] == "2026-08-10T09:00:00+08:00"
    assert result[0]["last_seen"] == "2026-08-16T00:50:00+08:00"
