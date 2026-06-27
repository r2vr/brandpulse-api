"""Command-line interface.

A thin adapter over :mod:`brandpulse.service`. It only handles argument parsing
and presentation; all orchestration lives in the service layer, shared with the
HTTP API.
"""

from __future__ import annotations

import asyncio

import typer

from brandpulse import service, sources

app = typer.Typer(add_completion=False, help="Brand monitoring & content curation engine.")


@app.command(name="sources")
def list_sources() -> None:
    """List the source connectors currently registered."""
    for kind in sources.available():
        typer.echo(f"- {kind}")


@app.command()
def monitor(
    terms: list[str] = typer.Argument(..., help="Keywords/brands to track."),
    limit: int = typer.Option(20, "--limit", "-n", help="Items to show."),
    per_source: int = typer.Option(50, "--per-source", help="Fetch cap per source."),
) -> None:
    """Fan out across all sources, curate, and print the ranked shortlist."""
    ranked = asyncio.run(service.monitor(terms, per_source=per_source, limit=limit))
    if not ranked:
        typer.echo("No matching content found.")
        raise typer.Exit(code=0)
    for rank, scored in enumerate(ranked, start=1):
        i = scored.item
        typer.echo(f"{rank:>2}. [{scored.score:.3f}] ({i.source}) {i.title}")
        typer.echo(f"     {i.url}")


if __name__ == "__main__":
    app()
