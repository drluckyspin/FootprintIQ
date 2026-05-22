/**
 * Singleton DuckDB connection for Route Handlers.
 */

import "server-only";

import fs from "node:fs";
import path from "node:path";

import { DuckDBInstance, type DuckDBConnection } from "@duckdb/node-api";

import { sqftLog } from "./log";

let _connectionPromise: Promise<DuckDBConnection> | null = null;

export function repoRoot(): string {
  return path.resolve(process.cwd(), "..");
}

/** Repo-root `data/` (or SQFT_DATA_DIR). Relative paths are resolved from repo root, not `frontend/`. */
export function dataDir(): string {
  const root = repoRoot();
  const raw = process.env.SQFT_DATA_DIR?.trim();
  if (!raw) {
    return path.join(root, "data");
  }
  return path.isAbsolute(raw) ? raw : path.resolve(root, raw);
}

export async function getConnection(): Promise<DuckDBConnection> {
  if (_connectionPromise) return _connectionPromise;
  _connectionPromise = (async () => {
    sqftLog.info("duckdb", "opening in-memory DuckDB connection");
    const instance = await DuckDBInstance.create(":memory:");
    const conn = await instance.connect();
    await conn.run("INSTALL spatial; LOAD spatial;");
    sqftLog.debug("duckdb", "spatial extension loaded");
    return conn;
  })();
  return _connectionPromise;
}

function sqlPath(p: string): string {
  return p.replace(/\\/g, "/").replace(/'/g, "''");
}

type ParquetName = "estimates" | "footprints" | "geocoded" | "qa_reviews";

type DataBundle = {
  label: string;
  paths: Partial<Record<ParquetName, string>>;
};

function exists(p: string): boolean {
  return fs.existsSync(p);
}

/** Resolve a consistent parquet set so estimates, footprints, and geocoded never mix tiers. */
function resolveBundle(): DataBundle {
  const data = dataDir();
  const root = repoRoot();
  const fixtureDir = path.join(root, "tests", "fixtures");

  const liveEstimates = path.join(data, "output", "estimates.parquet");
  const liveFootprints = path.join(data, "interim", "footprints.parquet");
  const liveGeocoded = path.join(data, "interim", "geocoded.parquet");

  if (exists(liveEstimates) && exists(liveFootprints) && exists(liveGeocoded)) {
    const bundle: DataBundle = {
      label: "live-run",
      paths: {
        estimates: liveEstimates,
        footprints: liveFootprints,
        geocoded: liveGeocoded,
        qa_reviews: path.join(data, "output", "qa_reviews.parquet"),
      },
    };
    sqftLog.info(
      "duckdb",
      `data bundle: live pipeline dataDir=${data} estimates=${liveEstimates}`,
    );
    return bundle;
  }

  const fixtureEstimates = path.join(fixtureDir, "estimates.parquet");
  const fixtureFootprints = path.join(fixtureDir, "footprints.parquet");
  const fixtureGeocoded = path.join(fixtureDir, "geocoded.parquet");

  if (exists(fixtureEstimates)) {
    const bundle: DataBundle = {
      label: "fixture",
      paths: {
        estimates: fixtureEstimates,
        footprints: fixtureFootprints,
        geocoded: fixtureGeocoded,
        qa_reviews: path.join(data, "output", "qa_reviews.parquet"),
      },
    };
    if (exists(liveEstimates)) {
      sqftLog.warn(
        "duckdb",
        `data bundle: fixtures (incomplete live run at dataDir=${data}). Run: make sample`,
      );
    } else {
      sqftLog.warn(
        "duckdb",
        `data bundle: fixtures only (dataDir=${data}). Run: make sample for live satellite alignment`,
      );
    }
    return bundle;
  }

  sqftLog.warn("duckdb", `no estimates.parquet under dataDir=${data} or tests/fixtures`);
  return {
    label: "missing",
    paths: { estimates: liveEstimates },
  };
}

/** Prefer pipeline output; fall back to committed fixtures for local dev/CI. */
export function parquetPath(name: string): string {
  const bundle = resolveBundle();
  const fromBundle = bundle.paths[name as ParquetName];
  if (fromBundle && exists(fromBundle)) {
    return fromBundle;
  }

  if (name === "qa_reviews") {
    const qaOut = path.join(dataDir(), "output", "qa_reviews.parquet");
    if (exists(qaOut)) return qaOut;
  }

  const fallback = path.join(dataDir(), "output", `${name}.parquet`);
  return fallback;
}

export function parquetFromSql(name: string): string {
  return `'${sqlPath(parquetPath(name))}'`;
}

export function dataBundleLabel(): string {
  return resolveBundle().label;
}

export function interimParquet(name: string): string {
  return parquetPath(name);
}

export function outputParquet(name: string): string {
  return parquetPath(name);
}
