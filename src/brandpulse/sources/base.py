"""The pluggable source layer.

This is the architectural keystone of the project. Every platform —open and
restrictive alike— is reduced to one small contract: given a query, yield
normalised :class:`~brandpulse.domain.models.ContentItem` objects. The rest of
the system never imports a connector directly; it asks the registry. That
indirection is what makes adding Reddit, Mastodon or a (scoped) Instagram
adapter a localised change instead of a refactor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass

from brandpulse.domain.models import ContentItem, SourceKind


@dataclass(frozen=True, slots=True)
class Query:
    """What to look for. Connectors interpret ``terms`` per their capabilities.

    Some sources do full-text search (Reddit, Mastodon); others only match
    hashtags or a fixed feed (Instagram Graph, RSS). A connector that cannot
    honour a query simply yields nothing rather than raising — callers fan out
    across many sources and tolerate partial coverage.
    """

    terms: tuple[str, ...]
    limit: int = 50


class SourceConnector(ABC):
    """Contract every source must satisfy.

    Subclasses implement :meth:`fetch`. They MUST NOT leak transport details
    (HTTP clients, auth tokens) through their public surface — those belong in
    ``__init__`` so the connector stays unit-testable with a fake client.
    """

    kind: SourceKind

    @abstractmethod
    def fetch(self, query: Query) -> AsyncIterator[ContentItem]:
        """Yield items matching ``query``. Implemented as an async generator."""
        raise NotImplementedError

    async def healthcheck(self) -> bool:
        """Cheap liveness probe. Overridden by connectors that hit a network."""
        return True


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
ConnectorFactory = Callable[[], SourceConnector]
_REGISTRY: dict[SourceKind, ConnectorFactory] = {}


def register(kind: SourceKind) -> Callable[[ConnectorFactory], ConnectorFactory]:
    """Decorator registering a zero-arg factory for a connector kind."""

    def decorator(factory: ConnectorFactory) -> ConnectorFactory:
        if kind in _REGISTRY:
            raise ValueError(f"Connector already registered for {kind!r}")
        _REGISTRY[kind] = factory
        return factory

    return decorator


def available() -> tuple[SourceKind, ...]:
    """Source kinds with a registered connector, sorted for stable output."""
    return tuple(sorted(_REGISTRY, key=str))


def build(kind: SourceKind) -> SourceConnector:
    """Instantiate the connector registered for ``kind``."""
    try:
        return _REGISTRY[kind]()
    except KeyError:
        raise LookupError(f"No connector registered for {kind!r}") from None
