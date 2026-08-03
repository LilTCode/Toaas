import re

COGNITIVE_DIMS = [
    "abstract_reasoning",
    "logical_reasoning",
    "theoretical_knowledge",
    "quantitative_calculation",
    "practical_application",
]

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
        "structured", "problem.solv", "debug", "syntax", "semantic",
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
        "quantitative", "calculation", "numerical", "math", "statistics",
        "algebra", "calculus", "probability", "data", "analytics",
        "equation", "formula", "measurement", "metric", "statistical",
        "regression", "optimization", "linear algebra", "discrete math",
        "number", "computation", "complexity", "big o",
    ],
    "practical_application": [
        "practical", "application", "implement", "project", "lab", "workshop",
        "exercise", "hands.on", "programming", "coding", "development",
        "design", "tool", "practice", "applied", "real.world", "engineering",
        "software", "web", "mobile", "database", "framework", "api",
        "deployment", "testing", "prototype", "build", "configure",
    ],
}


def classify_course(title, description="", major_topics="", learning_objectives=""):
    text = f"{title} {title} {description} {major_topics} {learning_objectives}".lower()
    text = re.sub(r"[^a-z0-9\s.]", " ", text)

    scores = {dim: 0 for dim in COGNITIVE_DIMS}
    for dim, keywords in DIM_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                weight = 3 if kw in title.lower() else 1
                scores[dim] += weight

    total = sum(scores.values())
    if total == 0:
        even = 100 // len(COGNITIVE_DIMS)
        remainder = 100 - even * len(COGNITIVE_DIMS)
        result = {dim: even for dim in COGNITIVE_DIMS}
        result[COGNITIVE_DIMS[-1]] += remainder
        return result

    result = {}
    allocated = 0
    sorted_dims = sorted(COGNITIVE_DIMS, key=lambda d: scores[d], reverse=True)
    for i, dim in enumerate(sorted_dims):
        if i == len(sorted_dims) - 1:
            result[dim] = 100 - allocated
        else:
            pct = max(1, round((scores[dim] / total) * 100))
            result[dim] = pct
            allocated += pct
    return result
