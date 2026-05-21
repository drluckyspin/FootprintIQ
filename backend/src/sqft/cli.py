"""Typer-based CLI. OWNED BY LANE C.

Surfaces each pipeline stage as its own command, plus `run-all` for the chained pipeline.

Wave 0 stub — `app` defined so `python -m sqft.cli --help` works for smoke tests.
"""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="sqft — building square footage estimator pipeline")


@app.command()
def geocode(
    input_csv: Path = typer.Argument(..., exists=True, dir_okay=False),
    config: Path | None = typer.Option(None, "--config"),
) -> None:
    """Run normalize + dedup + geocode stage. Output: data/interim/geocoded.parquet."""
    raise NotImplementedError("Lane C: implement geocode command")


@app.command()
def footprints(config: Path | None = typer.Option(None, "--config")) -> None:
    """Pull Overture footprints for the bbox of data/interim/geocoded.parquet."""
    raise NotImplementedError("Lane C: implement footprints command")


@app.command()
def join(config: Path | None = typer.Option(None, "--config")) -> None:
    """Spatial join + area + floors + flags."""
    raise NotImplementedError("Lane C: implement join command")


@app.command()
def estimate(config: Path | None = typer.Option(None, "--config")) -> None:
    """Write final data/output/estimates.parquet."""
    raise NotImplementedError("Lane C: implement estimate command")


@app.command(name="run-all")
def run_all(
    input_csv: Path = typer.Argument(..., exists=True, dir_okay=False),
    config: Path | None = typer.Option(None, "--config"),
    sample_size: int | None = typer.Option(None, "--sample-size"),
    max_cost_usd: float = typer.Option(50.0, "--max-cost-usd"),
) -> None:
    """Run the full pipeline end-to-end (resume-aware)."""
    raise NotImplementedError("Lane C: implement run-all command")


@app.command()
def validate(
    ground_truth: Path | None = typer.Option(None, "--ground-truth"),
    worksheet_size: int = typer.Option(200, "--worksheet-size"),
) -> None:
    """Generate HTML report + (optionally) stratified ground-truth worksheet."""
    raise NotImplementedError("Lane C: implement validate command")


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
