"""Source connectors.

Importing the concrete modules here triggers their ``@register`` side effects,
so callers only need ``import brandpulse.sources`` to populate the registry.
"""

from brandpulse.sources import (  # noqa: F401  (registration side effects)
    hackernews,
    mastodon,
    reddit,
    rss,
)
from brandpulse.sources.base import (
    Query,
    SourceConnector,
    available,
    build,
    register,
)

__all__ = ["Query", "SourceConnector", "available", "build", "register"]
