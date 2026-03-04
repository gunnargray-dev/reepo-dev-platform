"""Reepo similar repos — find similar repos using topic overlap and star proximity."""
import math

from src.db import _connect, _row_to_dict, get_repo, DEFAULT_DB_PATH


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def _star_proximity(stars_a: int, stars_b: int) -> float:
    """Compute proximity score based on log-scale star distance."""
    if stars_a <= 0 or stars_b <= 0:
        return 0.0
    log_a = math.log10(max(stars_a, 1))
    log_b = math.log10(max(stars_b, 1))
    distance = abs(log_a - log_b)
    max_distance = 6.0  # log10(1M)
    return max(0.0, 1.0 - distance / max_distance)


def find_similar(
    path: str = DEFAULT_DB_PATH,
    owner: str = "",
    name: str = "",
    limit: int = 10,
) -> list[dict]:
    """Find repos similar to the given repo based on topics, category, and star count.

    Score = 0.7 * jaccard_topics + 0.3 * star_proximity
    Category match required (same primary or overlapping secondary).
    """
    target = get_repo(owner, name, path)
    if not target:
        return []

    target_topics = set(target.get("topics") or [])
    target_category = target.get("category_primary", "")
    target_stars = target.get("stars", 0)

    conn = _connect(path)
    rows = conn.execute(
        "SELECT * FROM repos WHERE id != ? AND category_primary = ?",
        (target["id"], target_category),
    ).fetchall()
    conn.close()

    candidates = []
    for row in rows:
        repo = _row_to_dict(row)
        repo_topics = set(repo.get("topics") or [])
        repo_stars = repo.get("stars", 0)

        jaccard = _jaccard_similarity(target_topics, repo_topics)
        star_prox = _star_proximity(target_stars, repo_stars)
        similarity_score = round(0.7 * jaccard + 0.3 * star_prox, 4)

        if similarity_score > 0:
            repo["similarity_score"] = similarity_score
            candidates.append(repo)

    candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    return candidates[:limit]
