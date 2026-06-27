"""Curation scoring.

Turns a raw stream of items into a ranked, deduplicated shortlist. The score is
intentionally transparent and explainable —a weighted sum of interpretable
signals— rather than an opaque model. That is the honest choice for a portfolio:
the ML can be swapped in later behind the same interface (see ``Scorer``).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp
from typing import Protocol

from brandpulse.domain.models import ContentItem


@dataclass(frozen=True, slots=True)
class ScoredItem:
    item: ContentItem
    score: float
    signals: dict[str, float]


class Scorer(Protocol):
    """Stable seam for swapping the heuristic for a trained model later."""

    def score(self, item: ContentItem, terms: Sequence[str]) -> ScoredItem: ...


@dataclass(frozen=True, slots=True)
class HeuristicScorer:
    """Explainable baseline scorer.

    Weights are explicit so the ranking can be reasoned about and tuned. A real
    model would implement the same :class:`Scorer` protocol and slot in cleanly.
    """

    recency_weight: float = 0.5
    relevance_weight: float = 0.5
    half_life_hours: float = 24.0

    def score(self, item: ContentItem, terms: Sequence[str]) -> ScoredItem:
        recency = self._recency(item.published_at)
        relevance = self._relevance(item, terms)
        total = self.recency_weight * recency + self.relevance_weight * relevance
        return ScoredItem(
            item=item,
            score=round(total, 4),
            signals={"recency": round(recency, 4), "relevance": round(relevance, 4)},
        )

    def _recency(self, published_at: datetime) -> float:
        """Exponential decay in [0, 1]; 1.0 = just now, 0.5 at one half-life."""
        age_hours = (datetime.now(tz=UTC) - published_at).total_seconds() / 3600
        age_hours = max(age_hours, 0.0)
        return exp(-age_hours / self.half_life_hours * 0.6931)

    @staticmethod
    def _relevance(item: ContentItem, terms: Sequence[str]) -> float:
        if not terms:
            return 0.0
        haystack = f"{item.title}\n{item.body}".lower()
        hits = sum(haystack.count(term.lower()) for term in terms)
        # Saturating: diminishing returns past a few mentions.
        return 1.0 - exp(-0.5 * hits)


def curate(
    items: Iterable[ContentItem],
    terms: Sequence[str],
    scorer: Scorer | None = None,
    limit: int = 20,
) -> list[ScoredItem]:
    """Deduplicate by fingerprint, score, and return the top ``limit`` items."""
    scorer = scorer or HeuristicScorer()
    seen: dict[str, ScoredItem] = {}
    for item in items:
        scored = scorer.score(item, terms)
        existing = seen.get(item.fingerprint)
        if existing is None or scored.score > existing.score:
            seen[item.fingerprint] = scored
    ranked = sorted(seen.values(), key=lambda s: s.score, reverse=True)
    return ranked[:limit]
