"""Typer-based CLI."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from sqft.config import load_settings
from sqft.pipeline import run_pipeline, use_fixtures
from sqft.validate import generate_qa_worksheet, generate_report

app = typer.Typer(help="sqft — building square footage estimator pipeline")


def _repo_config() -> Path:
    return Path(__file__).resolve().parents[3] / "config.yaml"


@app.command()
def geocode(
    input_csv: Path = typer.Argument(..., exists=True, dir_okay=False),
    config: Path | None = typer.Option(None, "--config"),
) -> None:
    """Run normalize + dedup + geocode (fixture mode stops after geocode parquet)."""
    settings = load_settings(config or _repo_config())
    os.environ.setdefault("SQFT_USE_FIXTURES", "1")
    run_pipeline(input_csv, settings=settings, config_path=config, resume=False)


@app.command()
def footprints(config: Path | None = typer.Option(None, "--config")) -> None:
    typer.echo("Use run-all; footprints stage is not exposed standalone yet.")


@app.command()
def join(config: Path | None = typer.Option(None, "--config")) -> None:
    typer.echo("Use run-all; join stage is not exposed standalone yet.")


@app.command()
def estimate(config: Path | None = typer.Option(None, "--config")) -> None:
    typer.echo("Use run-all; estimate stage is not exposed standalone yet.")


@app.command(name="run-all")
def run_all(
    input_csv: Path = typer.Argument(..., exists=True, dir_okay=False),
    config: Path | None = typer.Option(None, "--config"),
    sample_size: int | None = typer.Option(None, "--sample-size"),
    max_cost_usd: float = typer.Option(50.0, "--max-cost-usd"),
    fixtures: bool = typer.Option(False, "--fixtures", help="Use tests/fixtures parquets"),
) -> None:
    """Run the full pipeline end-to-end (resume-aware)."""
    if fixtures:
        os.environ["SQFT_USE_FIXTURES"] = "1"
    settings = load_settings(config or _repo_config())
    if sample_size is not None:
        settings.pipeline.sample_size = sample_size
    settings.pipeline.max_cost_usd = max_cost_usd
    out = run_pipeline(input_csv, settings=settings, config_path=config)
    typer.echo(f"Wrote {out}")


@app.command()
def validate(
    ground_truth: Path | None = typer.Option(None, "--ground-truth"),
    worksheet_size: int = typer.Option(200, "--worksheet-size"),
    config: Path | None = typer.Option(None, "--config"),
) -> None:
    """Generate HTML report + stratified QA worksheet."""
    settings = load_settings(config or _repo_config())
    est = settings.data_dir / "output" / "estimates.parquet"
    if not est.exists():
        fixture_est = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "estimates.parquet"
        est = fixture_est
    report = generate_report(est, settings.data_dir / "output" / "report.html", ground_truth)
    worksheet = generate_qa_worksheet(
        est, settings.data_dir / "output" / "qa_worksheet.csv", n=worksheet_size
    )
    typer.echo(f"Report: {report}")
    typer.echo(f"Worksheet: {worksheet}")


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
