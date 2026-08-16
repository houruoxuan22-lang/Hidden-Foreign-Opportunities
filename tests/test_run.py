from pathlib import Path
from run import apply_seen_metadata, merge_missing_jobs
from scripts.job_identity import deduplicate_jobs, job_identity

def test_deduplicate_jobs_removes_same_greenhouse_job_across_url_changes():
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

    deduped = deduplicate_jobs(jobs)

    assert len(deduped) == 1


def test_deduplicate_jobs_keeps_distinct_native_job_ids():
    jobs = [
        {
            "company": "Stripe",
            "source": "greenhouse",
            "title": "Security Analyst, Bug Bounty",
            "location": "Remote, North America",
            "url": "https://stripe.com/jobs/search?gh_jid=7979393",
        },
        {
            "company": "Stripe",
            "source": "greenhouse",
            "title": "Security Analyst, Bug Bounty",
            "location": "Remote, North America",
            "url": "https://stripe.com/jobs/search?gh_jid=8070570",
        },
    ]

    deduped = deduplicate_jobs(jobs)

    assert len(deduped) == 2

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

def test_job_identity_uses_greenhouse_job_id_across_url_changes():
    first = {
        "company": "Stripe",
        "source": "greenhouse",
        "url": "https://boards.greenhouse.io/stripe/jobs/123?gh_jid=7893199",
    }
    second = {
        "company": "Stripe",
        "source": "greenhouse",
        "url": "https://stripe.com/jobs/search?foo=bar&gh_jid=7893199",
    }

    assert job_identity(first) == job_identity(second)

def test_job_identity_keeps_greenhouse_ids_separate_across_companies():
    first = {
        "company": "Stripe",
        "source": "greenhouse",
        "url": "https://stripe.com/jobs/search?gh_jid=7893199",
    }
    second = {
        "company": "Cloudflare",
        "source": "greenhouse",
        "url": "https://boards.greenhouse.io/cloudflare/jobs/7893199?gh_jid=7893199",
    }

    assert job_identity(first) != job_identity(second)

def test_job_identity_uses_european_chamber_vacancy_id_across_url_changes():
    first = {
        "company": "European Chamber China",
        "source": "european_chamber",
        "url": "https://www.europeanchamber.com.cn/en/job-vacancies/5398/Commissioning_Engineer",
    }
    second = {
        "company": "European Chamber China",
        "source": "european_chamber",
        "url": "https://www.europeanchamber.com.cn/en/job-vacancies/5398/Changed_Title_Slug",
    }

    assert job_identity(first) == job_identity(second)


def test_job_identity_uses_sap_job_id_across_url_changes():
    first = {
        "company": "SAP China",
        "source": "sap_careers",
        "url": "https://jobs.sap.com/job/Beijing-Old-Title-100016/1426364433/",
    }
    second = {
        "company": "SAP China",
        "source": "sap_careers",
        "url": "https://jobs.sap.com/job/Shanghai-Completely-New-Title-200040/1426364433/",
    }

    assert job_identity(first) == job_identity(second)

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

def test_merge_missing_jobs_marks_current_job_active():
    jobs = [
        {
            "company": "Stripe",
            "url": "https://example.com/jobs/123",
        }
    ]
    existing_jobs = [
        {
            "company": "Stripe",
            "url": "https://example.com/jobs/123",
            "possibly_closed": True,
        }
    ]

    result = merge_missing_jobs(
        jobs,
        existing_jobs,
        successful_sources={"Stripe"},
    )

    assert len(result) == 1
    assert result[0]["possibly_closed"] is False


def test_merge_missing_jobs_marks_missing_job_possibly_closed_when_source_succeeded():
    jobs = []
    existing_jobs = [
        {
            "company": "Stripe",
            "url": "https://example.com/jobs/123",
            "first_seen": "2026-08-10T09:00:00+00:00",
            "last_seen": "2026-08-15T09:00:00+00:00",
        }
    ]

    result = merge_missing_jobs(
        jobs,
        existing_jobs,
        successful_sources={"Stripe"},
    )

    assert len(result) == 1
    assert result[0]["possibly_closed"] is True
    assert result[0]["last_seen"] == "2026-08-15T09:00:00+00:00"


def test_merge_missing_jobs_preserves_status_when_source_failed():
    jobs = []
    existing_jobs = [
        {
            "company": "Stripe",
            "url": "https://example.com/jobs/123",
            "possibly_closed": False,
            "first_seen": "2026-08-10T09:00:00+00:00",
            "last_seen": "2026-08-15T09:00:00+00:00",
        }
    ]

    result = merge_missing_jobs(
        jobs,
        existing_jobs,
        successful_sources=set(),
    )

    assert len(result) == 1
    assert result[0]["possibly_closed"] is False
    assert result[0]["last_seen"] == "2026-08-15T09:00:00+00:00"

def test_run_pipeline_deduplicates_before_enrichment():
    source = Path("run.py").read_text(encoding="utf-8")

    dedupe_index = source.index("all_jobs = deduplicate_jobs(all_jobs)")
    enrich_index = source.index("all_jobs = enrich_jobs_with_skills(all_jobs)")
    save_index = source.index("save_jobs(all_jobs)")

    assert dedupe_index < enrich_index < save_index
