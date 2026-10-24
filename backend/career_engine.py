"""
career_engine.py
Skill gap analysis and career pathway engine for Livelihood Voice Assistant.

Input:  Skill Profile dict (from multimodal_gemma.py)
Output: {
    "skill_gaps": [...],
    "matched_jobs": [...],
    "recommended_courses": [...],
    "pathway": {
        "current": {...},
        "gap": {...},
        "target": {...}
    },
    "readiness_score": float (0–100)
}
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load mock database
# ---------------------------------------------------------------------------

_DB_PATH = Path(__file__).parent.parent / "data" / "mock_database.json"

def _load_db() -> dict:
    try:
        with open(_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Database not found at {_DB_PATH}")
        return {"job_opportunities": [], "micro_learning_modules": [], "skill_taxonomy": {}}


# ---------------------------------------------------------------------------
# Skill normalisation helpers
# ---------------------------------------------------------------------------

def _normalise(skill: str) -> str:
    """Lower-case, strip hyphens/underscores, remove filler words."""
    return skill.lower().replace("-", " ").replace("_", " ").strip()


def _skill_match(worker_skills: list[str], job_skills: list[str]) -> tuple[list[str], list[str]]:
    """
    Returns (matched, missing) lists.
    Uses fuzzy substring matching to handle abbreviations / spacing differences.
    """
    worker_norm = [_normalise(s) for s in worker_skills]
    matched, missing = [], []

    for js in job_skills:
        js_norm = _normalise(js)
        found = any(
            js_norm in ws or ws in js_norm or
            _token_overlap(js_norm, ws) >= 0.6
            for ws in worker_norm
        )
        if found:
            matched.append(js)
        else:
            missing.append(js)

    return matched, missing


def _token_overlap(a: str, b: str) -> float:
    """Jaccard overlap on word tokens."""
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ---------------------------------------------------------------------------
# Job matching
# ---------------------------------------------------------------------------

def _match_jobs(profile: dict, jobs: list[dict], top_n: int = 3) -> list[dict]:
    """Score and rank jobs by skill overlap + experience fit."""
    worker_skills  = profile.get("skills", [])
    worker_exp     = int(profile.get("years_experience", 0))
    scored_jobs    = []

    for job in jobs:
        required  = job.get("required_skills", [])
        preferred = job.get("preferred_skills", [])
        matched_r, missing_r = _skill_match(worker_skills, required)
        matched_p, _         = _skill_match(worker_skills, preferred)

        # Base score: % of required skills met (weighted 70%) + preferred (30%)
        req_score  = len(matched_r) / max(len(required), 1)
        pref_score = len(matched_p) / max(len(preferred), 1)
        base_score = 0.70 * req_score + 0.30 * pref_score

        # Experience bonus: +5% per year up to 20 years
        exp_bonus  = min(worker_exp / 20, 1.0) * 0.1
        final_score = min(base_score + exp_bonus, 1.0)

        scored_jobs.append({
            **job,
            "match_score"    : round(final_score * 100, 1),
            "matched_skills" : matched_r,
            "missing_skills" : missing_r,
        })

    scored_jobs.sort(key=lambda j: j["match_score"], reverse=True)
    return scored_jobs[:top_n]


# ---------------------------------------------------------------------------
# Skill gap computation
# ---------------------------------------------------------------------------

def _compute_gaps(profile: dict, top_jobs: list[dict]) -> list[str]:
    """Union of missing skills across the top 2 recommended jobs."""
    gap_set: set[str] = set()
    for job in top_jobs[:2]:
        gap_set.update(job.get("missing_skills", []))
    return list(gap_set)


# ---------------------------------------------------------------------------
# Course recommendation
# ---------------------------------------------------------------------------

def _recommend_courses(
    skill_gaps: list[str],
    modules: list[dict],
    profile: dict,
    top_n: int = 2,
) -> list[dict]:
    """Pick courses that address the most skill gaps for this worker."""
    scored: list[tuple[float, dict]] = []

    # Detect category from profile occupation
    occ = profile.get("occupation", "").lower()
    if any(kw in occ for kw in ["weav", "textile", "loom"]):
        preferred_category = "weaving"
    elif any(kw in occ for kw in ["hvac", "ac ", "refriger", "cool"]):
        preferred_category = "hvac"
    elif any(kw in occ for kw in ["carpen", "wood", "furni", "joiner"]):
        preferred_category = "carpentry"
    else:
        preferred_category = "general"

    gap_norm = [_normalise(g) for g in skill_gaps]

    for module in modules:
        unlocked = [_normalise(s) for s in module.get("skills_unlocked", [])]
        overlap  = sum(
            1 for u in unlocked
            if any(_token_overlap(u, g) >= 0.5 or u in g or g in u for g in gap_norm)
        )
        cat_bonus = 0.3 if module.get("category") == preferred_category else 0.0
        score     = overlap + cat_bonus
        scored.append((score, module))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:top_n]]


# ---------------------------------------------------------------------------
# Readiness score
# ---------------------------------------------------------------------------

def _readiness_score(profile: dict, top_jobs: list[dict]) -> float:
    """
    Composite readiness score (0–100) factoring:
    - Top job match score (50%)
    - Years of experience vs 10-year benchmark (30%)
    - AI confidence score (20%)
    """
    top_match   = top_jobs[0]["match_score"] if top_jobs else 0.0
    exp_score   = min(profile.get("years_experience", 0) / 10, 1.0) * 100
    confidence  = profile.get("confidence_score", 0.5) * 100

    return round(0.5 * top_match + 0.3 * exp_score + 0.2 * confidence, 1)


# ---------------------------------------------------------------------------
# Pathway builder
# ---------------------------------------------------------------------------

def _build_pathway(profile: dict, skill_gaps: list[str], top_job: dict) -> dict:
    """
    Returns a 3-step visual timeline payload:
    Step 1 – Current Skills
    Step 2 – Learning Gap
    Step 3 – Target Opportunity
    """
    return {
        "current": {
            "label"   : "Your Skills Today",
            "skills"  : profile.get("skills", []),
            "tools"   : profile.get("tools_detected", []),
            "level"   : profile.get("experience_level", "Intermediate"),
            "summary" : profile.get("raw_summary", ""),
        },
        "gap": {
            "label"   : "Skills to Unlock",
            "skills"  : skill_gaps,
            "message" : (
                f"Add {len(skill_gaps)} skill{'s' if len(skill_gaps) != 1 else ''} "
                "to qualify for top opportunities."
            ),
        },
        "target": {
            "label"         : "Your Next Role",
            "job_title"     : top_job.get("title", ""),
            "employer"      : top_job.get("employer", ""),
            "salary_range"  : top_job.get("salary_range_inr", ""),
            "match_score"   : top_job.get("match_score", 0),
            "location"      : top_job.get("location", ""),
            "openings"      : top_job.get("openings", 0),
        },
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse_career(profile: dict) -> dict:
    """
    Main entry point.

    Args:
        profile: Skill & Livelihood Profile dict from multimodal_gemma.extract_skill_profile()

    Returns:
        Career analysis dict with skill_gaps, matched_jobs, recommended_courses,
        pathway, and readiness_score.
    """
    db = _load_db()
    jobs    = db.get("job_opportunities", [])
    modules = db.get("micro_learning_modules", [])

    # 1. Match jobs
    matched_jobs = _match_jobs(profile, jobs, top_n=3)

    # 2. Compute skill gaps from top 2 jobs
    skill_gaps = _compute_gaps(profile, matched_jobs)

    # 3. Recommend courses targeting the gaps
    courses = _recommend_courses(skill_gaps, modules, profile, top_n=2)

    # 4. Build visual pathway
    top_job = matched_jobs[0] if matched_jobs else {}
    pathway = _build_pathway(profile, skill_gaps, top_job)

    # 5. Composite readiness score
    readiness = _readiness_score(profile, matched_jobs)

    return {
        "skill_gaps"          : skill_gaps,
        "matched_jobs"        : matched_jobs,
        "recommended_courses" : courses,
        "pathway"             : pathway,
        "readiness_score"     : readiness,
    }


# ---------------------------------------------------------------------------
# CLI test harness
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.multimodal_gemma import extract_skill_profile

    test_transcript = "I am a carpenter with 15 years experience in furniture making and woodworking."
    profile = extract_skill_profile(transcript=test_transcript, force_mock=True)
    result  = analyse_career(profile)

    print("\n=== SKILL PROFILE ===")
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    print("\n=== CAREER ANALYSIS ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
