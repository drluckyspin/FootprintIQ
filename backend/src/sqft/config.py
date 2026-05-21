"""Pydantic settings loaded from config.yaml with env-var overrides."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeocoderConfig(BaseModel):
    provider: Literal["google", "census"] = "google"
    api_key_env: str = "GOOGLE_GEOCODING_API_KEY"
    places_api_key_env: str = "GOOGLE_PLACES_API_KEY"
    min_acceptable_precision: Literal[
        "ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE"
    ] = "RANGE_INTERPOLATED"
    concurrency: int = 20
    rate_limit_qps: int = 40
    retry_attempts: int = 3
    cache_path: Path = Path("data/interim/geocode_cache.sqlite")
    chain_tokens: tuple[str, ...] = (
        "walmart",
        "target",
        "amazon",
        "costco",
        "kroger",
        "home depot",
        "lowe's",
        "best buy",
        "sam's club",
        "fedex",
        "ups",
    )


class OvertureConfig(BaseModel):
    release: str = "latest"
    s3_path_template: str = (
        "s3://overturemaps-us-west-2/release/{release}/theme=buildings/type=building/"
    )
    states_filter: tuple[str, ...] | None = None


class SpatialConfig(BaseModel):
    multi_building_rule: Literal[
        "largest", "sum_within_radius", "largest_within_parcel"
    ] = "largest_within_parcel"
    search_buffer_meters: float = 25.0
    parcel_buffer_meters: float = 75.0
    nearest_k: int = 5


class FloorsConfig(BaseModel):
    default: int = 1
    height_per_floor_meters: float = 4.0
    prefer: tuple[Literal["num_floors", "height"], ...] = ("num_floors", "height")
    max_floors_cap: int = 50
    max_height_meters_for_inference: float = 80.0


class OutputConfig(BaseModel):
    units: Literal["square_feet"] = "square_feet"
    decimals: int = 0


class PipelineConfig(BaseModel):
    resume: bool = True
    sample_size: int | None = None
    max_cost_usd: float = 50.0
    require_confirm_above_usd: float = 50.0


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SQFT_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    geocoder: GeocoderConfig = Field(default_factory=GeocoderConfig)
    overture: OvertureConfig = Field(default_factory=OvertureConfig)
    spatial: SpatialConfig = Field(default_factory=SpatialConfig)
    floors: FloorsConfig = Field(default_factory=FloorsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)

    data_dir: Path = Path("data")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from YAML at repo root config.yaml + env overrides."""
    if config_path is None:
        config_path = Path(__file__).resolve().parents[3] / "config.yaml"
    data: dict[str, Any] = {}
    if config_path.exists():
        raw = yaml.safe_load(config_path.read_text()) or {}
        if isinstance(raw, dict):
            data = raw
    return Settings(**data)
