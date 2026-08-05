import re

COGNITIVE_DIMS = [
    "abstract_reasoning",
    "logical_reasoning",
    "theoretical_knowledge",
    "quantitative_calculation",
    "practical_application",
]

# Inflections a keyword may legitimately carry. Deliberately excludes "al"/"ical"
# so "logic" does not also fire on "logical" (both are listed independently).
_SUFFIXES = r"(?:s|es|ed|ing|ion|ions|ation|ations|ity|ies)?"

_PATTERN_CACHE = {}


def _pattern(keyword):
    """Word-boundary matcher for one keyword.

    Plain substring matching used to fire "data" on "database", "math" on
    "mathematics" and "logic" on "logical", inflating whichever dimension owned
    the shorter keyword.
    """
    compiled = _PATTERN_CACHE.get(keyword)
    if compiled is None:
        compiled = re.compile(r"\b" + re.escape(keyword) + _SUFFIXES + r"\b")
        _PATTERN_CACHE[keyword] = compiled
    return compiled

DIM_KEYWORDS = {
    "abstract_reasoning": [
        "abstract", "concept", "conceptual", "paradigm", "principle", "framework",
        "model", "symbolic", "formal", "reasoning", "algorithm", "analysis",
        "analytical", "decomposition", "theorem", "axiom", "theory",
        "mathematical model", "computational thinking", "abstraction",
        "design pattern", "architecture",
    ],
    "logical_reasoning": [
        "logic", "logical", "argument", "deduction", "deductive", "inference",
        "critical", "syntax", "grammar", "proof", "verification", "systematic",
        "structured", "problem solv", "debug", "semantic",
        "boolean", "predicate", "reasoning", "constraint", "specification",
        "correctness", "validation",
    ],
    "theoretical_knowledge": [
        "theory", "theoretical", "theorem", "foundation", "fundamental",
        "knowledge", "scientific", "mathematics", "physics", "methodology",
        "philosophy", "principle", "law", "concept", "epistemology",
        "scientific method", "research", "literature", "survey",
    ],
    "quantitative_calculation": [
        "quantitative", "calculation", "numerical", "math", "mathematic",
        "statistics", "algebra", "calculus", "probability", "data", "analytics",
        "equation", "formula", "measurement", "metric", "statistical",
        "regression", "optimization", "linear algebra", "discrete math",
        "number", "computation", "complexity", "big o",
    ],
    "practical_application": [
        "practical", "application", "implement", "project", "lab", "workshop",
        "exercise", "hands on", "programming", "coding", "development",
        "design", "tool", "practice", "applied", "real world", "engineering",
        "software", "web", "mobile", "database", "framework", "api",
        "deployment", "testing", "prototype", "build", "configure",
    ],
}


def _even_split():
    even = 100 // len(COGNITIVE_DIMS)
    result = {dim: even for dim in COGNITIVE_DIMS}
    result[COGNITIVE_DIMS[-1]] += 100 - even * len(COGNITIVE_DIMS)
    return result


def classify_course(title, description="", major_topics="", learning_objectives=""):
    """Infer a course's cognitive demand split. Always returns five values totalling 100."""
    title = title or ""
    raw = f"{title} {title} {description} {major_topics} {learning_objectives}".lower()
    text = re.sub(r"[^a-z0-9\s]", " ", raw)
    text = re.sub(r"\s+", " ", text)
    title_text = re.sub(r"[^a-z0-9\s]", " ", title.lower())

    scores = {dim: 0 for dim in COGNITIVE_DIMS}
    for dim, keywords in DIM_KEYWORDS.items():
        for kw in keywords:
            pattern = _pattern(kw)
            if pattern.search(text):
                scores[dim] += 3 if pattern.search(title_text) else 1

    total = sum(scores.values())
    if total == 0:
        return _even_split()

    # Largest-remainder allocation. The previous version handed the leftover to
    # the last dimension, which could drive it negative once the other four had
    # each been rounded up to a floor of 1%.
    exact = {dim: scores[dim] / total * 100 for dim in COGNITIVE_DIMS}
    result = {dim: int(exact[dim]) for dim in COGNITIVE_DIMS}
    remainder = 100 - sum(result.values())
    by_fraction = sorted(
        COGNITIVE_DIMS, key=lambda d: (exact[d] - int(exact[d]), scores[d]), reverse=True
    )
    for i in range(remainder):
        result[by_fraction[i % len(by_fraction)]] += 1
    return result
