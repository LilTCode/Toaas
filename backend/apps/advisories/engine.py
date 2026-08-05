"""Cognitive-load aware course recommendation engine.

Replaces the similarity-matching heuristic that previously lived inline in
``apps.advisories.views``. Three ideas drive the model:

1. **Mastery** — per-dimension proficiency inferred from grades, weighted by how
   heavily each course loaded that dimension. Values are independent per
   dimension (they do *not* sum to 100) and are shrunk toward a neutral prior so
   students with little history get honest low-confidence numbers instead of
   noise. Failures count as evidence, not as absence of evidence.

2. **Helplessness** — repeated failure concentrated in a dimension. This is the
   learned-helplessness signal: it drives the per-dimension strain caps that stop
   the planner from stacking a semester with the exact kind of work the student
   keeps failing.

3. **Constrained greedy selection** — highest value-per-credit-unit first,
   subject to semester/level/prerequisite legality, the 15–24 unit policy, a
   per-dimension strain budget, and a per-semester carryover balance cap.
   Carryovers are processed as a strictly higher tier than new courses.

Everything the planner decides is recorded with a reason so the plan can be
explained to the student and audited by an advisor.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime

from apps.courses.models import Course, TranscriptEntry

COGNITIVE_DIMENSIONS = [
    "abstract_reasoning",
    "logical_reasoning",
    "theoretical_knowledge",
    "quantitative_calculation",
    "practical_application",
]

DIM_LABELS = {
    "abstract_reasoning": "abstract reasoning",
    "logical_reasoning": "logical reasoning",
    "theoretical_knowledge": "theoretical knowledge",
    "quantitative_calculation": "quantitative calculation",
    "practical_application": "practical application",
}

GRADE_POINTS = {"A": 5.0, "B": 4.0, "C": 3.0, "D": 2.0, "E": 1.0, "F": 0.0}
MAX_GRADE_POINT = 5.0

PASS_STATUSES = frozenset({"passed"})
FAIL_STATUSES = frozenset({"failed", "carryover"})

# ── University policy ────────────────────────────────────────────────────────
MIN_UNITS = 15
MAX_UNITS = 24

# ── Model hyper-parameters ───────────────────────────────────────────────────
# Strength of the neutral prior, expressed in "effective credit units" of
# evidence. A student with 6 units fully loaded on a dimension has their raw
# score weighted 50/50 against the 50% prior.
PRIOR_STRENGTH = 6.0
PRIOR_MEAN = 0.5

# Each repeat failure of the same course hurts more than the first.
REPEAT_FAIL_ESCALATION = 0.6
# Share of the helplessness signal carried by the raw failure rate; the rest is
# carried by how often the same course had to be retaken.
HELPLESSNESS_RATE_WEIGHT = 0.6

# Strain budget per dimension = MAX_UNITS * (BASE + SPAN * mastery * (1 - helplessness)).
STRAIN_BASE_RATIO = 0.25
STRAIN_SPAN_RATIO = 0.30

# If the strain caps leave the student below the 15-unit floor, relax them.
STRAIN_RELAX_FACTOR = 1.2
STRAIN_RELAX_ROUNDS = 6

# Learned-helplessness countermeasure: guarantee some winnable courses.
ANCHOR_THRESHOLD = 60.0
MIN_ANCHORS = 2

# Selection priority multipliers.
PRIORITY_CARRYOVER = 1.9
PRIORITY_COMPULSORY = 1.4
PRIORITY_ELECTIVE = 1.0
# Extra urgency per 100 levels a carryover is behind the student's current level.
LEVEL_LAG_URGENCY = 0.10

# Never pile every outstanding course into one semester. At most this many
# carryover units are scheduled now; the rest are deferred to the next session's
# same semester, where they are re-planned alongside that semester's own courses.
MAX_CARRYOVER_UNITS = 12
# Extra urgency per additional failed attempt. Without this, ranking carryovers
# by likely success means the hardest ones are deferred every single semester and
# a student can carry the same course until it blocks graduation.
CARRYOVER_ATTEMPT_URGENCY = 0.15


# ─────────────────────────────────────────────────────────────────────────────
# Transcript reading
# ─────────────────────────────────────────────────────────────────────────────

def _grade_point(entry):
    """Resolve an entry to a 0–5 grade point, tolerating partial data."""
    grade = (entry.grade or "").strip().upper()
    if grade in GRADE_POINTS:
        return GRADE_POINTS[grade]
    if entry.credit_points:
        return max(0.0, min(float(entry.credit_points), MAX_GRADE_POINT))
    if entry.status in PASS_STATUSES:
        return GRADE_POINTS["C"]
    return 0.0


def _attempts_by_course(student):
    """All graded attempts, grouped by course and ordered oldest → newest."""
    entries = list(
        TranscriptEntry.objects.filter(student=student).select_related("course")
    )
    grouped = defaultdict(list)
    for entry in entries:
        if entry.status == "in_progress":
            continue  # no result yet — carries no evidence either way
        grouped[entry.course_id].append(entry)
    for attempts in grouped.values():
        attempts.sort(key=lambda e: (e.created_at or datetime.min, e.id or 0))
    return grouped


def _dim_weight(course, dim):
    """Credit-unit-scaled load a course places on one cognitive dimension."""
    return max(1, course.credit_units) * (getattr(course, dim, 0) / 100.0)


def _is_vacation_delivered(course):
    """True for SIWES-style attachments taken outside the teaching semesters."""
    metadata = getattr(course, "metadata", None) or {}
    return metadata.get("delivery") == "siwes_long_vacation"


# ─────────────────────────────────────────────────────────────────────────────
# Cognitive model
# ─────────────────────────────────────────────────────────────────────────────

def compute_mastery(student, attempts=None):
    """Per-dimension proficiency on a 0–100 scale.

    Unlike the old profile, these values are *independent* per dimension and
    genuinely reflect performance: the same course passed with an A and passed
    with a D produce different mastery. Failures are included at 0 points, which
    is what makes a weak dimension actually read as weak.

    Returns ``(mastery, evidence, confidence)`` where ``evidence`` is the
    effective credit units observed for each dimension and ``confidence`` is the
    share of the estimate driven by real data rather than the prior.
    """
    if attempts is None:
        attempts = _attempts_by_course(student)

    earned = {d: 0.0 for d in COGNITIVE_DIMENSIONS}
    possible = {d: 0.0 for d in COGNITIVE_DIMENSIONS}

    for course_attempts in attempts.values():
        # The most recent attempt is the student's standing result for a course.
        latest = course_attempts[-1]
        course = latest.course
        points = _grade_point(latest)
        for dim in COGNITIVE_DIMENSIONS:
            weight = _dim_weight(course, dim)
            if weight <= 0:
                continue
            earned[dim] += weight * points
            possible[dim] += weight * MAX_GRADE_POINT

    mastery, evidence, confidence = {}, {}, {}
    for dim in COGNITIVE_DIMENSIONS:
        observed_units = possible[dim] / MAX_GRADE_POINT
        raw = (earned[dim] / possible[dim]) if possible[dim] > 0 else PRIOR_MEAN
        shrunk = (observed_units * raw + PRIOR_STRENGTH * PRIOR_MEAN) / (
            observed_units + PRIOR_STRENGTH
        )
        mastery[dim] = round(shrunk * 100, 1)
        evidence[dim] = round(observed_units, 2)
        confidence[dim] = round(observed_units / (observed_units + PRIOR_STRENGTH), 3)

    return mastery, evidence, confidence


def profile_from_mastery(mastery):
    """Relative strength profile expressed as percentages that sum to 100.

    The raw ``mastery`` values are independent per dimension (a student can be
    at 40% in everything), which is useful internally but confusing to display.
    This turns them into a proper distribution — the share of a student's
    measured ability that lives in each dimension.
    """
    total = sum(mastery.get(d, 0) for d in COGNITIVE_DIMENSIONS)
    if total <= 0:
        even = round(100 / len(COGNITIVE_DIMENSIONS), 1)
        return {d: even for d in COGNITIVE_DIMENSIONS}

    result = {
        d: round(mastery.get(d, 0) / total * 100, 1) for d in COGNITIVE_DIMENSIONS
    }
    drift = round(100.0 - sum(result.values()), 1)
    if drift:
        result[COGNITIVE_DIMENSIONS[0]] = round(
            result[COGNITIVE_DIMENSIONS[0]] + drift, 1
        )
    return result


def compute_helplessness(student, attempts=None):
    """Repeated-failure concentration per dimension, on a 0–1 scale.

    Two things matter and are measured separately, because a plain
    failed/total ratio saturates at 1.0 for a student whose only history in a
    dimension is failure — it cannot then tell one failure from three:

    * **rate** — what share of the student's load in this dimension was failed;
    * **depth** — how often the *same* course had to be retaken.

    A student who failed one calculation course reads lower than one who failed
    the same calculation course three times, even though both failed everything
    they attempted.
    """
    if attempts is None:
        attempts = _attempts_by_course(student)

    failed_load = {d: 0.0 for d in COGNITIVE_DIMENSIONS}
    escalated_load = {d: 0.0 for d in COGNITIVE_DIMENSIONS}
    total_load = {d: 0.0 for d in COGNITIVE_DIMENSIONS}
    failure_counts = defaultdict(int)

    for course_attempts in attempts.values():
        failures_so_far = 0
        for attempt in course_attempts:
            course = attempt.course
            is_failure = attempt.status in FAIL_STATUSES or _grade_point(attempt) <= 0
            for dim in COGNITIVE_DIMENSIONS:
                weight = _dim_weight(course, dim)
                if weight <= 0:
                    continue
                total_load[dim] += weight
                if is_failure:
                    escalation = 1.0 + REPEAT_FAIL_ESCALATION * failures_so_far
                    failed_load[dim] += weight
                    escalated_load[dim] += weight * escalation
            if is_failure:
                failures_so_far += 1
                dominant = max(
                    COGNITIVE_DIMENSIONS, key=lambda d: getattr(course, d, 0)
                )
                failure_counts[dominant] += 1

    helplessness = {}
    for dim in COGNITIVE_DIMENSIONS:
        if total_load[dim] <= 0 or failed_load[dim] <= 0:
            helplessness[dim] = 0.0
            continue
        rate = failed_load[dim] / total_load[dim]
        depth = escalated_load[dim] / failed_load[dim]  # 1.0 when never retaken
        depth_factor = 1.0 - (1.0 / depth)
        severity = HELPLESSNESS_RATE_WEIGHT + (
            1.0 - HELPLESSNESS_RATE_WEIGHT
        ) * depth_factor
        helplessness[dim] = round(min(1.0, rate * severity), 3)

    return helplessness, dict(failure_counts)


def expected_success(course, mastery, helplessness):
    """Probability-like 0-100 estimate that the student will do well.

    This is a demand-weighted expectation: ``Σ (course load on dim × mastery of
    dim)``. A course that is 60% quantitative for a student at 25% quantitative
    mastery reads as much harder than one that leans on a strong dimension.

    Helplessness does not discount the score itself — a weak dimension already
    reads as weak through mastery, so an extra penalty would double-count it.
    Instead, helplessness decides *how much* of that dimension's load the plan
    may carry at once, through the strain budgets.
    """
    weights = {d: getattr(course, d, 0) / 100.0 for d in COGNITIVE_DIMENSIONS}
    total_weight = sum(weights.values())
    if total_weight <= 0:
        return 50.0, 0.0

    base = sum(weights[d] * mastery.get(d, 50.0) for d in COGNITIVE_DIMENSIONS)
    base /= total_weight

    strain = sum(weights[d] * helplessness.get(d, 0.0) for d in COGNITIVE_DIMENSIONS)
    strain /= total_weight

    return round(max(0.0, min(100.0, base)), 1), round(strain, 3)


def strain_budgets(mastery, helplessness, scale=1.0):
    """Maximum cognitive load, per dimension, the plan may carry this semester.

    Load is measured in credit-unit equivalents: a 3-unit course that is 60%
    quantitative contributes 1.8 to the quantitative budget.
    """
    budgets = {}
    for dim in COGNITIVE_DIMENSIONS:
        capacity = (mastery.get(dim, 50.0) / 100.0) * (1.0 - helplessness.get(dim, 0.0))
        ratio = STRAIN_BASE_RATIO + STRAIN_SPAN_RATIO * capacity
        budgets[dim] = round(MAX_UNITS * ratio * scale, 2)
    return budgets


# ─────────────────────────────────────────────────────────────────────────────
# Eligibility
# ─────────────────────────────────────────────────────────────────────────────

def _programme_filter(student):
    programme = student.get_programme_display().replace("B.Sc. ", "").strip()
    return [programme, "Computer Science", "General"]


def build_candidates(student, mastery, helplessness, attempts=None, semester=None,
                     level=None):
    """Legal, not-yet-passed courses for the given semester, each scored.

    Enforces the hard academic rules:
      * only courses for the semester being planned (a second-semester course can
        never be taken in the first semester, carryover or not);
      * new courses come from the student's current level only;
      * carryovers may come from any *earlier* level, never a later one;
      * every prerequisite must already be passed;
      * a course already passed is never offered again.
    """
    if attempts is None:
        attempts = _attempts_by_course(student)
    semester = semester or student.current_semester
    level = level or student.current_level

    passed_ids = set()
    outstanding = {}
    for course_id, course_attempts in attempts.items():
        latest = course_attempts[-1]
        if latest.status in PASS_STATUSES and _grade_point(latest) > 0:
            passed_ids.add(course_id)
        elif latest.status in FAIL_STATUSES:
            outstanding[course_id] = len(course_attempts)

    departments = _programme_filter(student)

    current_level_courses = Course.objects.filter(
        level=level,
        semester=semester,
        department_classification__in=departments,
    ).prefetch_related("prerequisites")

    carryover_courses = Course.objects.filter(
        id__in=outstanding.keys(),
        semester=semester,
        level__lte=level,
    ).prefetch_related("prerequisites")

    pool = {}
    for course in current_level_courses:
        pool[course.id] = course
    for course in carryover_courses:
        pool[course.id] = course

    candidates, blocked = [], []
    for course in pool.values():
        if course.id in passed_ids:
            continue
        if not getattr(course, "is_active", True):
            continue
        if _is_vacation_delivered(course):
            # SIWES and other long-vacation attachments carry credit toward
            # graduation but are not registered against a semester's unit load.
            continue

        missing = [p for p in course.prerequisites.all() if p.id not in passed_ids]
        if missing:
            blocked.append({
                "id": course.id,
                "code": course.code,
                "title": course.title,
                "credit_units": course.credit_units,
                "reason": "prerequisite_not_met",
                "missing_prerequisites": [p.code for p in missing],
            })
            continue

        is_carryover = course.id in outstanding
        attempt_count = outstanding.get(course.id, 0)
        score, strain = expected_success(course, mastery, helplessness)

        # Familiarity from one prior attempt helps; chronic repetition does not.
        if attempt_count == 1:
            score = min(100.0, score + 5.0)
        elif attempt_count >= 3:
            score = max(0.0, score - 5.0 * (attempt_count - 2))

        levels_behind = max(0, (level - course.level) // 100)
        if is_carryover:
            priority = PRIORITY_CARRYOVER * (
                1.0
                + LEVEL_LAG_URGENCY * levels_behind
                + CARRYOVER_ATTEMPT_URGENCY * max(0, attempt_count - 1)
            )
        elif getattr(course, "is_compulsory", True):
            priority = PRIORITY_COMPULSORY
        else:
            priority = PRIORITY_ELECTIVE

        units = max(1, course.credit_units)
        candidates.append({
            "course": course,
            "id": course.id,
            "code": course.code,
            "title": course.title,
            "credit_units": course.credit_units,
            "level": course.level,
            "semester": course.semester,
            "description": course.description,
            "carryover": is_carryover,
            "attempts": attempt_count,
            "compulsory": bool(getattr(course, "is_compulsory", True)),
            "levels_behind": levels_behind,
            "compatibility": round(score, 1),
            "expected_success": round(score, 1),
            "strain_index": strain,
            "priority": round(priority, 3),
            "value": round(score * priority, 2),
            "density": round(score * priority / units, 3),
            "dominant_dim": max(
                COGNITIVE_DIMENSIONS, key=lambda d: getattr(course, d, 0)
            ),
            "cognitive_dims": {
                d: getattr(course, d, 0) for d in COGNITIVE_DIMENSIONS
            },
        })

    return candidates, blocked


# ─────────────────────────────────────────────────────────────────────────────
# Constrained greedy selection
# ─────────────────────────────────────────────────────────────────────────────

def _greedy_pass(candidates, budgets, max_units=MAX_UNITS, carryover_cap=None):
    """One greedy sweep: carryover tier first, then new courses.

    Within each tier, courses are taken in descending value-per-credit-unit —
    the standard greedy approximation for a knapsack, which the previous
    implementation skipped by ignoring credit units entirely. The carryover tier
    is additionally capped so a semester is never turned into a pile-on of
    outstanding work.
    """
    selected, rejected = [], []
    load = {d: 0.0 for d in COGNITIVE_DIMENSIONS}
    total_units = 0
    carryover_units = 0
    carryover_cap = carryover_cap if carryover_cap is not None else MAX_CARRYOVER_UNITS

    tiers = (
        # Carryovers: oldest debt first (levels behind, then attempts), and only
        # then by value density. Ranking them purely by likely success would
        # defer the hardest course every semester forever.
        (
            [c for c in candidates if c["carryover"]],
            lambda c: (-c["levels_behind"], -c["attempts"], -c["density"], c["code"]),
        ),
        (
            [c for c in candidates if not c["carryover"]],
            lambda c: (-c["density"], c["code"]),
        ),
    )

    for tier, sort_key in tiers:
        for cand in sorted(tier, key=sort_key):
            units = cand["credit_units"]

            if cand["carryover"] and carryover_units + units > carryover_cap:
                rejected.append({**cand, "defer_reason": "carryover_balance"})
                continue

            if total_units + units > max_units:
                rejected.append({**cand, "defer_reason": "unit_ceiling"})
                continue

            breached = [
                d for d in COGNITIVE_DIMENSIONS
                if load[d] + _dim_weight(cand["course"], d) > budgets[d]
            ]
            if breached:
                rejected.append({
                    **cand,
                    "defer_reason": "cognitive_strain_cap",
                    "strained_dimensions": breached,
                })
                continue

            for d in COGNITIVE_DIMENSIONS:
                load[d] += _dim_weight(cand["course"], d)
            total_units += units
            if cand["carryover"]:
                carryover_units += units
            selected.append(cand)

    return selected, rejected, total_units, load


def _apply_anchor_repair(selected, rejected, total_units):
    """Guarantee some winnable courses to counteract learned helplessness.

    If the plan contains fewer than ``MIN_ANCHORS`` courses the student is likely
    to pass, swap the weakest non-carryover selection for the strongest deferred
    course that fits. Carryovers are never swapped out — clearing them is
    non-negotiable.
    """
    swaps = []
    anchors = [c for c in selected if c["expected_success"] >= ANCHOR_THRESHOLD]
    if len(anchors) >= MIN_ANCHORS:
        return selected, rejected, total_units, swaps

    pool = sorted(
        [c for c in rejected if c["defer_reason"] != "prerequisite_not_met"],
        key=lambda c: -c["expected_success"],
    )

    for candidate in pool:
        if len([c for c in selected if c["expected_success"] >= ANCHOR_THRESHOLD]) >= MIN_ANCHORS:
            break
        if candidate["expected_success"] < ANCHOR_THRESHOLD:
            break

        swappable = sorted(
            [c for c in selected if not c["carryover"]],
            key=lambda c: c["expected_success"],
        )
        if not swappable:
            break
        weakest = swappable[0]
        if weakest["expected_success"] >= candidate["expected_success"]:
            break

        projected = total_units - weakest["credit_units"] + candidate["credit_units"]
        if projected > MAX_UNITS:
            continue

        selected = [c for c in selected if c["id"] != weakest["id"]]
        selected.append(candidate)
        rejected = [c for c in rejected if c["id"] != candidate["id"]]
        rejected.append({**weakest, "defer_reason": "displaced_by_confidence_anchor"})
        total_units = projected
        swaps.append({"out": weakest["code"], "in": candidate["code"]})

    return selected, rejected, total_units, swaps


def select_courses(candidates, mastery, helplessness):
    """Run the greedy under strain caps, relaxing them only if we'd break policy."""
    scale = 1.0
    relaxations = 0
    budgets = strain_budgets(mastery, helplessness, scale)
    carryover_cap = MAX_CARRYOVER_UNITS
    selected, rejected, total_units, load = _greedy_pass(
        candidates, budgets, carryover_cap=carryover_cap
    )

    available_units = sum(c["credit_units"] for c in candidates)
    reachable_floor = min(MIN_UNITS, available_units)

    while total_units < reachable_floor and relaxations < STRAIN_RELAX_ROUNDS:
        scale *= STRAIN_RELAX_FACTOR
        relaxations += 1
        budgets = strain_budgets(mastery, helplessness, scale)
        carryover_cap = round(MAX_CARRYOVER_UNITS * scale)
        selected, rejected, total_units, load = _greedy_pass(
            candidates, budgets, carryover_cap=carryover_cap
        )

    selected, rejected, total_units, swaps = _apply_anchor_repair(
        selected, rejected, total_units
    )

    selected.sort(key=lambda c: (not c["carryover"], -c["density"], c["code"]))

    return {
        "selected": selected,
        "rejected": rejected,
        "total_units": total_units,
        "cognitive_load": {d: round(load[d], 2) for d in COGNITIVE_DIMENSIONS},
        "budgets": budgets,
        "relaxations": relaxations,
        "anchor_swaps": swaps,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Session helpers & forward projection
# ─────────────────────────────────────────────────────────────────────────────

def next_session(session):
    """'2025/2026' → '2026/2027'. Falls back gracefully on unexpected formats."""
    match = re.match(r"^\s*(\d{4})\s*/\s*(\d{4})\s*$", session or "")
    if not match:
        return session or ""
    start, end = int(match.group(1)), int(match.group(2))
    return f"{start + 1}/{end + 1}"


def project_next_cycle(student, deferred, mastery, helplessness, attempts):
    """Plan the deferred courses alongside the *next* occurrence of this semester.

    Deferred work does not vanish — it lands in the same semester of the
    following session, where it competes with that session's own courses. This
    projection assumes current mastery (we cannot know grades not yet earned) and
    is advisory rather than binding.
    """
    semester = student.current_semester
    next_level = min(400, student.current_level + 100)

    future_candidates, _ = build_candidates(
        student, mastery, helplessness, attempts=attempts,
        semester=semester, level=next_level,
    )

    deferred_ids = {c["id"] for c in deferred}
    combined = [c for c in future_candidates if c["id"] not in deferred_ids]
    for item in deferred:
        promoted = dict(item)
        # Unresolved work outranks new courses when the next cycle is planned.
        promoted["carryover"] = True
        promoted["priority"] = round(PRIORITY_CARRYOVER, 3)
        promoted["value"] = round(promoted["expected_success"] * PRIORITY_CARRYOVER, 2)
        promoted["density"] = round(
            promoted["value"] / max(1, promoted["credit_units"]), 3
        )
        combined.append(promoted)

    outcome = select_courses(combined, mastery, helplessness)
    return {
        "session": next_session(student.session),
        "semester": semester,
        "level": next_level,
        "total_units": outcome["total_units"],
        "courses": [_public(c) for c in outcome["selected"]],
        "still_deferred": [_public(c) for c in outcome["rejected"]],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Presentation
# ─────────────────────────────────────────────────────────────────────────────

_DEFER_REASONS = {
    "cognitive_strain_cap": (
        "Deferred to protect your cognitive load — taking it now would push your "
        "{dims} demand past a manageable level for this semester."
    ),
    "carryover_balance": (
        "Deferred to keep this semester balanced — taking every outstanding "
        "course at once would overload the term. It is planned for the next "
        "session's same semester alongside its own courses."
    ),
    "unit_ceiling": (
        "Deferred because the {max_units}-unit registration ceiling was already "
        "reached by higher-priority courses."
    ),
    "displaced_by_confidence_anchor": (
        "Deferred so the plan keeps enough courses you are well positioned to "
        "pass, which protects your momentum this semester."
    ),
    "prerequisite_not_met": "Blocked until its prerequisites are passed.",
}


def _public(cand):
    """Strip the ORM object so the payload is JSON-serialisable."""
    return {k: v for k, v in cand.items() if k != "course"}


def _explain(cand, mastery):
    dim = cand["dominant_dim"]
    label = DIM_LABELS[dim]
    level_of = mastery.get(dim, 50.0)

    if cand["carryover"]:
        lead = (
            f"Carryover priority — {cand['code']} is outstanding from "
            f"{cand['level']} level and must be cleared."
        )
    elif cand["compulsory"]:
        lead = f"Core {cand['level']}-level course for your programme."
    else:
        lead = f"Elective aligned to your {cand['level']}-level plan."

    fit = (
        f"It is mainly {label} work, where your measured mastery is "
        f"{level_of:.0f}%. Projected performance: {cand['expected_success']:.0f}%."
    )
    return f"{lead} {fit}"


def _defer_explanation(cand):
    template = _DEFER_REASONS.get(cand.get("defer_reason"), "Deferred.")
    dims = ", ".join(
        DIM_LABELS.get(d, d) for d in cand.get("strained_dimensions", [])
    ) or "cognitive"
    return template.format(dims=dims, max_units=MAX_UNITS)


def _narrative(student, mastery, helplessness, outcome, deferred, warnings):
    ordered = sorted(COGNITIVE_DIMENSIONS, key=lambda d: mastery.get(d, 0))
    weakest, strongest = ordered[0], ordered[-1]

    parts = [
        f"Measured mastery is strongest in {DIM_LABELS[strongest]} "
        f"({mastery[strongest]:.0f}%) and weakest in {DIM_LABELS[weakest]} "
        f"({mastery[weakest]:.0f}%).",
        f"This plan covers {len(outcome['selected'])} course(s) totalling "
        f"{outcome['total_units']} units for {student.current_level} level, "
        f"semester {student.current_semester}.",
    ]

    struggling = [d for d in COGNITIVE_DIMENSIONS if helplessness.get(d, 0) >= 0.3]
    if struggling:
        names = ", ".join(DIM_LABELS[d] for d in struggling)
        parts.append(
            f"A pattern of repeated failure was detected in {names}; the load in "
            f"those areas has been capped deliberately."
        )

    if deferred:
        parts.append(
            f"{len(deferred)} course(s) were moved to {next_session(student.session)} "
            f"semester {student.current_semester} rather than overloading you now."
        )

    if outcome["anchor_swaps"]:
        parts.append(
            "The plan was adjusted to retain courses you are well positioned to "
            "pass, so the semester is not made up entirely of high-risk work."
        )

    parts.extend(warnings)
    return " ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def build_plan(student):
    """Produce a complete, explained registration plan for one student."""
    attempts = _attempts_by_course(student)
    mastery, evidence, confidence = compute_mastery(student, attempts)
    helplessness, failure_counts = compute_helplessness(student, attempts)
    profile = profile_from_mastery(mastery)

    candidates, blocked = build_candidates(student, mastery, helplessness, attempts)
    outcome = select_courses(candidates, mastery, helplessness)

    selected = outcome["selected"]
    deferred = outcome["rejected"]

    courses = []
    for cand in selected:
        item = _public(cand)
        item["explanation"] = _explain(cand, mastery)
        courses.append(item)

    deferred_payload = []
    for cand in deferred:
        item = _public(cand)
        item["explanation"] = _defer_explanation(cand)
        item["deferred_to_session"] = next_session(student.session)
        item["deferred_to_semester"] = student.current_semester
        deferred_payload.append(item)

    for item in blocked:
        blocked_item = dict(item)
        blocked_item["explanation"] = _DEFER_REASONS["prerequisite_not_met"]
        deferred_payload.append(blocked_item)

    warnings = []
    total_units = outcome["total_units"]
    if total_units < MIN_UNITS:
        available = sum(c["credit_units"] for c in candidates)
        if available < MIN_UNITS:
            warnings.append(
                f"Only {available} units are legally available to you this "
                f"semester, which is below the {MIN_UNITS}-unit minimum. Speak to "
                f"your advisor about a waiver or an approved substitution."
            )
        else:
            warnings.append(
                f"The plan sits at {total_units} units, below the {MIN_UNITS}-unit "
                f"minimum, because the remaining courses would overload areas you "
                f"are currently struggling with. Advisor review is required."
            )
    if outcome["relaxations"]:
        warnings.append(
            "Cognitive load caps were relaxed to reach the minimum unit "
            "requirement."
        )
    dropped_compulsory = [c["code"] for c in deferred if c.get("compulsory") and not c.get("carryover")]
    if dropped_compulsory:
        warnings.append(
            "Core course(s) deferred and needing advisor sign-off: "
            + ", ".join(sorted(dropped_compulsory)) + "."
        )

    anchors = [c for c in selected if c["expected_success"] >= ANCHOR_THRESHOLD]
    if selected and not anchors:
        warnings.append(
            f"No course available to you this semester clears the "
            f"{ANCHOR_THRESHOLD:.0f}% confidence mark, so every option carries "
            f"real risk. This student needs direct academic support, not just a "
            f"lighter timetable."
        )

    projection = project_next_cycle(
        student, deferred, mastery, helplessness, attempts
    )

    return {
        "courses": courses,
        "deferred_courses": deferred_payload,
        "total_units": total_units,
        "min_units": MIN_UNITS,
        "max_units": MAX_UNITS,
        "meets_policy": MIN_UNITS <= total_units <= MAX_UNITS,
        "level": student.current_level,
        "semester": student.current_semester,
        "session": student.session,
        "profile": profile,
        "mastery": mastery,
        "evidence": evidence,
        "confidence": confidence,
        "helplessness": helplessness,
        "failure_counts": failure_counts,
        "cognitive_load": outcome["cognitive_load"],
        "strain_budgets": outcome["budgets"],
        "anchor_swaps": outcome["anchor_swaps"],
        "relaxations": outcome["relaxations"],
        "warnings": warnings,
        "next_cycle": projection,
        "explanation": _narrative(
            student, mastery, helplessness, outcome, deferred, warnings
        ),
    }


def compute_cgpa(student):
    """Credit-unit-weighted CGPA over each course's standing (latest) attempt."""
    attempts = _attempts_by_course(student)
    points = 0.0
    units = 0
    for course_attempts in attempts.values():
        latest = course_attempts[-1]
        course_units = max(1, latest.course.credit_units)
        points += _grade_point(latest) * course_units
        units += course_units
    if units == 0:
        return 0.0
    return round(points / units, 2)
