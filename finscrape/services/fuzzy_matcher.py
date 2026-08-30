"""
Fuzzy Matcher — Extracted from RapidFuzz patterns.

Fuzzy string matching with:
- Levenshtein distance
- Token-based similarity
- Partial ratio matching
- Process-based matching
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def ratio(s1: str, s2: str) -> float:
    """Similarity ratio between two strings (0-100)."""
    if not s1 and not s2:
        return 100.0
    if not s1 or not s2:
        return 0.0
    distance = levenshtein_distance(s1.lower(), s2.lower())
    max_len = max(len(s1), len(s2))
    return (1 - distance / max_len) * 100


def partial_ratio(s1: str, s2: str) -> float:
    """Best partial match score."""
    if not s1 or not s2:
        return 0.0

    s1_lower = s1.lower()
    s2_lower = s2.lower()
    shorter = min(s1_lower, s2_lower, key=len)
    longer = max(s1_lower, s2_lower, key=len)

    best_score = 0.0
    for i in range(len(longer) - len(shorter) + 1):
        window = longer[i:i + len(shorter)]
        score = ratio(shorter, window)
        if score > best_score:
            best_score = score

    return best_score


def token_sort_ratio(s1: str, s2: str) -> float:
    """Sort tokens and compare."""
    sorted1 = " ".join(sorted(s1.lower().split()))
    sorted2 = " ".join(sorted(s2.lower().split()))
    return ratio(sorted1, sorted2)


def token_set_ratio(s1: str, s2: str) -> float:
    """Compare token sets (ignoring duplicates and order)."""
    tokens1 = set(s1.lower().split())
    tokens2 = set(s2.lower().split())

    intersection = tokens1 & tokens2
    diff1 = tokens1 - tokens2
    diff2 = tokens2 - tokens1

    sorted_inter = " ".join(sorted(intersection))
    sorted_diff1 = " ".join(sorted(diff1))
    sorted_diff2 = " ".join(sorted(diff2))

    combined_diff = f"{sorted_inter} {sorted_diff1}"
    combined_other = f"{sorted_inter} {sorted_diff2}"

    return max(ratio(combined_diff, sorted_inter), ratio(combined_other, sorted_inter))


def WRatio(s1: str, s2: str) -> float:
    """Weighted ratio combining multiple methods."""
    r1 = ratio(s1, s2)
    r2 = partial_ratio(s1, s2)
    r3 = token_sort_ratio(s1, s2)
    r4 = token_set_ratio(s1, s2)

    # Weighted average
    return 0.6 * r1 + 0.1 * r2 + 0.15 * r3 + 0.15 * r4


def extract(
    query: str,
    choices: List[str],
    scorer=None,
    score_cutoff: float = 0,
    limit: int = 5,
) -> List[Tuple[str, float, int]]:
    """Extract best matches from choices."""
    if scorer is None:
        scorer = WRatio

    results: List[Tuple[str, float, int]] = []
    for i, choice in enumerate(choices):
        score = scorer(query, choice)
        if score >= score_cutoff:
            results.append((choice, score, i))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def extractOne(
    query: str,
    choices: List[str],
    scorer=None,
    score_cutoff: float = 0,
) -> Optional[Tuple[str, float, int]]:
    """Extract single best match."""
    results = extract(query, choices, scorer, score_cutoff, limit=1)
    return results[0] if results else None


def cdist(
    queries: List[str],
    choices: List[str],
    scorer=None,
    score_cutoff: float = 0,
) -> List[List[Tuple[str, float, int]]]:
    """Compute distance matrix between queries and choices."""
    if scorer is None:
        scorer = WRatio
    return [extract(q, choices, scorer, score_cutoff, limit=len(choices)) for q in queries]


def editops(s1: str, s2: str) -> List[Tuple[str, int, int]]:
    """Get edit operations needed to transform s1 into s2."""
    ops: List[Tuple[str, int, int]] = []
    s1_lower = s1.lower()
    s2_lower = s2.lower()

    if s1_lower == s2_lower:
        return ops

    # Simplified edit operation extraction
    i, j = 0, 0
    while i < len(s1_lower) and j < len(s2_lower):
        if s1_lower[i] != s2_lower[j]:
            if i + 1 < len(s1_lower) and s1_lower[i + 1] == s2_lower[j]:
                ops.append(("delete", i, i))
                i += 1
            elif j + 1 < len(s2_lower) and s1_lower[i] == s2_lower[j + 1]:
                ops.append(("insert", i, j))
                j += 1
            else:
                ops.append(("replace", i, j))
                i += 1
                j += 1
        else:
            i += 1
            j += 1

    while i < len(s1_lower):
        ops.append(("delete", i, i))
        i += 1

    while j < len(s2_lower):
        ops.append(("insert", len(s1_lower), j))
        j += 1

    return ops
