from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]

PROFILE_FILE = ROOT_DIR / "profiles" / "default_profile.json"
JOBS_FILE = ROOT_DIR / "data" / "jobs.json"
OUTPUT_FILE = ROOT_DIR / "data" / "jobs_matched.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)


def safe_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, list):
        return " ".join(safe_text(item) for item in value)

    return str(value)


def normalize_text(value: Any) -> str:
    text = safe_text(value).lower()
    return re.sub(r"\s+", " ", text).strip()


def contains_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = normalize_text(keyword)

    if not normalized_keyword:
        return False

    # Use boundaries for simple English tokens, so "lead" does not
    # accidentally match words such as "leadership".
    if re.fullmatch(r"[a-z0-9+#.-]+", normalized_keyword):
        pattern = (
            rf"(?<![a-z0-9])"
            rf"{re.escape(normalized_keyword)}"
            rf"(?![a-z0-9])"
        )
        return re.search(pattern, text) is not None

    return normalized_keyword in text


def find_matching_keywords(
    text: str,
    keywords: list[str],
) -> list[str]:
    matches = []

    for keyword in keywords:
        if contains_keyword(text, keyword) and keyword not in matches:
            matches.append(keyword)

    return matches


def readable_keyword(keyword: str) -> str:
    if any("\u4e00" <= character <= "\u9fff" for character in keyword):
        return keyword

    return keyword.replace("-", " ").title()


def score_label(score: int) -> str:
    if score >= 75:
        return "Strong match"

    if score >= 55:
        return "Potential match"

    if score >= 35:
        return "Worth exploring"

    return "Low match"


def score_job(
    job: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    scoring = profile["scoring"]

    title = normalize_text(job.get("title"))
    location = normalize_text(job.get("location"))
    description = normalize_text(job.get("description"))
    skills = normalize_text(job.get("skills"))
    source_type = normalize_text(job.get("source_type"))

    role_text = title

    # Current company-career-page skill extraction may contain navigation text.
    # Until cleaner structured skills are available, only trust the job title.
    if source_type == "china_company_career":
        skill_text = title
    else:
        skill_text = " ".join(
            value for value in [title, skills] if value
        )

    full_text = " ".join(
        value
        for value in [title, location, description, skills]
        if value
    )

    score = 0
    good_fit: list[str] = []
    watch_out: list[str] = []

    # 1. Location matching
    location_matches = find_matching_keywords(
        location,
        profile.get("location_keywords", []),
    )
    remote_matches = find_matching_keywords(
        location,
        profile.get("remote_keywords", []),
    )

    restricted_remote_matches = find_matching_keywords(
        location,
        profile.get("restricted_remote_keywords", []),
    )

    if restricted_remote_matches:
        score += scoring["restricted_remote_penalty"]

        displayed_location = safe_text(job.get("location"))
        watch_out.append(
            f"Remote role appears region-restricted: {displayed_location}"
        )

    elif location_matches:
        score += scoring["location_match"]

        displayed_location = safe_text(job.get("location")) or readable_keyword(
            location_matches[0]
        )
        good_fit.append(f"Target location: {displayed_location}")

    elif remote_matches:
        score += scoring["remote_match"]
        good_fit.append("Remote-friendly location")

    elif (
        location
        and location not in {"unknown", "unknown location"}
    ):
        score += scoring["location_mismatch_penalty"]

        displayed_location = safe_text(job.get("location"))
        watch_out.append(
            f"Location outside current targets: {displayed_location}"
        )

    # 2. Preferred role matching
    role_matches = find_matching_keywords(
        role_text,
        profile.get("role_keywords", []),
    )

    if role_matches:
        score += scoring["role_match"]

        role_labels = [
            readable_keyword(keyword)
            for keyword in role_matches[:2]
        ]
        good_fit.append(f"Preferred role: {', '.join(role_labels)}")

    # 3. Early-career title matching
    early_career_matches = find_matching_keywords(
        title,
        profile.get("early_career_keywords", []),
    )

    if early_career_matches:
        score += scoring["early_career_match"]

        level_labels = [
            readable_keyword(keyword)
            for keyword in early_career_matches[:2]
        ]
        good_fit.append(f"Early-career signal: {', '.join(level_labels)}")

    # 4. Skills matching
    skill_matches = find_matching_keywords(
        skill_text,
        profile.get("skill_keywords", []),
    )

    if skill_matches:
        skill_match_max = scoring["skill_match_max"]

        # The first four matched skills each contribute an equal share.
        points_per_skill = max(1, skill_match_max // 4)
        skill_points = min(
            skill_match_max,
            len(skill_matches) * points_per_skill,
        )

        score += skill_points

        skill_labels = [
            readable_keyword(keyword)
            for keyword in skill_matches[:4]
        ]
        good_fit.append(f"Matched skills: {', '.join(skill_labels)}")
    
    # 5. Seniority risks from the job title
    title_risk_matches = find_matching_keywords(
        title,
        profile.get("title_risk_keywords", []),
    )

    for risk_keyword in title_risk_matches:
        score += scoring["title_risk_penalty"]
        watch_out.append(
            f"Seniority signal in title: {readable_keyword(risk_keyword)}"
        )

    # 6. Seniority and experience risks
    risk_matches = find_matching_keywords(
        full_text,
        profile.get("risk_keywords", []),
    )

    for risk_keyword in risk_matches:
        score += scoring["risk_keyword_penalty"]
        watch_out.append(
            f"Seniority or experience signal: {readable_keyword(risk_keyword)}"
        )

    # 7. Strong qualification risks
    strong_exclude_matches = find_matching_keywords(
        full_text,
        profile.get("strong_exclude_keywords", []),
    )

    for exclude_keyword in strong_exclude_matches:
        score += scoring["strong_exclude_penalty"]
        watch_out.append(
            f"Specialized requirement: {readable_keyword(exclude_keyword)}"
        )

    minimum_score = scoring.get("min_score", 0)
    maximum_score = scoring.get("max_score", 100)

    score = max(minimum_score, min(maximum_score, score))

    scored_job = dict(job)
    scored_job["match_score"] = score
    scored_job["match_label"] = score_label(score)
    scored_job["good_fit"] = good_fit
    scored_job["watch_out"] = watch_out

    return scored_job


def score_jobs(
    jobs: list[dict[str, Any]],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        score_job(job, profile)
        for job in jobs
        if isinstance(job, dict)
    ]


def print_top_matches(jobs: list[dict[str, Any]], limit: int = 10) -> None:
    ranked_jobs = sorted(
        jobs,
        key=lambda job: (
            job.get("match_score", 0),
            safe_text(job.get("posted_date")),
        ),
        reverse=True,
    )

    print()
    print(f"Top {min(limit, len(ranked_jobs))} matches")
    print("-" * 80)

    for job in ranked_jobs[:limit]:
        score = job.get("match_score", 0)
        company = safe_text(job.get("company")) or "Unknown company"
        title = safe_text(job.get("title")) or "Untitled"
        location = safe_text(job.get("location")) or "Unknown location"

        print(f"{score:>3} | {company} | {title} | {location}")

        good_fit = job.get("good_fit", [])
        watch_out = job.get("watch_out", [])

        if good_fit:
            print(f"    Good fit: {'; '.join(good_fit)}")

        if watch_out:
            print(f"    Watch out: {'; '.join(watch_out)}")


def main() -> None:
    profile = load_json(PROFILE_FILE)
    jobs = load_json(JOBS_FILE)

    if not isinstance(jobs, list):
        raise ValueError("data/jobs.json must contain a JSON list.")

    matched_jobs = score_jobs(jobs, profile)
    save_json(OUTPUT_FILE, matched_jobs)

    print(f"Profile: {profile.get('profile_name', 'Unknown profile')}")
    print(f"Scored jobs: {len(matched_jobs)}")
    print(f"Saved matched jobs to: {OUTPUT_FILE.relative_to(ROOT_DIR)}")

    print_top_matches(matched_jobs)


if __name__ == "__main__":
    main()