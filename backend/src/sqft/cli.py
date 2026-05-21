"""Typer-based CLI."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from sqft.config import load_settings
from sqft.log import get_logger
from sqft.overture import build_stac_cache
from sqft.pipeline import run_pipeline, use_fixtures
from sqft.validate import generate_qa_worksheet, generate_report

app = typer.Typer(help="sqft — building square footage estimator pipeline")
logger = get_logger("cli")


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


@app.command("stac-cache")
def stac_cache(config: Path | None = typer.Option(None, "--config")) -> None:
    """Build Overture building parquet index (cached under data/interim/)."""
    settings = load_settings(config or _repo_config())
    path = build_stac_cache(settings.overture)
    typer.echo(f"Wrote {path}")


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
    no_resume: bool = typer.Option(
        False,
        "--no-resume",
        help="Re-run all stages even if data/output/estimates.parquet exists",
    ),
) -> None:
    """Run the full pipeline end-to-end (resume-aware)."""
    if fixtures:
        os.environ["SQFT_USE_FIXTURES"] = "1"
    settings = load_settings(config or _repo_config())
    if sample_size is not None:
        settings.pipeline.sample_size = sample_size
    settings.pipeline.max_cost_usd = max_cost_usd
    resume = False if no_resume else None
    logger.info(
        "run-all input=%s fixtures_mode=%s sample_size=%s max_cost_usd=%s resume=%s data_dir=%s",
        input_csv,
        use_fixtures(),
        settings.pipeline.sample_size,
        max_cost_usd,
        resume if resume is not None else settings.pipeline.resume,
        settings.data_dir,
    )
    out = run_pipeline(input_csv, settings=settings, config_path=config, resume=resume)
    logger.info("run-all finished output=%s", out)
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
        logger.warning("estimates not at %s — using fixture %s", est, fixture_est)
        est = fixture_est
    logger.info("validate estimates=%s worksheet_size=%d ground_truth=%s", est, worksheet_size, ground_truth)
    report = generate_report(est, settings.data_dir / "output" / "report.html", ground_truth)
    worksheet = generate_qa_worksheet(
        est, settings.data_dir / "output" / "qa_worksheet.csv", n=worksheet_size
    )
    logger.info("validate done report=%s worksheet=%s", report, worksheet)
    typer.echo(f"Report: {report}")
    typer.echo(f"Worksheet: {worksheet}")


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
