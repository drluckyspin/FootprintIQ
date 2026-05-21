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

export function dataDir(): string {
  return process.env.SQFT_DATA_DIR
    ? path.resolve(process.env.SQFT_DATA_DIR)
    : path.resolve(repoRoot(), "data");
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

/** Prefer pipeline output; fall back to committed fixtures for local dev/CI. */
export function parquetPath(name: string): string {
  const candidates: { label: string; path: string }[] = [
    { label: "output", path: path.join(dataDir(), "output", `${name}.parquet`) },
    { label: "interim", path: path.join(dataDir(), "interim", `${name}.parquet`) },
    {
      label: "backend/output (legacy)",
      path: path.join(repoRoot(), "backend", "data", "output", `${name}.parquet`),
    },
    {
      label: "backend/interim (legacy)",
      path: path.join(repoRoot(), "backend", "data", "interim", `${name}.parquet`),
    },
    { label: "fixture", path: path.join(repoRoot(), "tests", "fixtures", `${name}.parquet`) },
  ];
  for (const { label, path: p } of candidates) {
    if (fs.existsSync(p)) {
      if (label === "fixture") {
        const live = candidates.find(
          (c) => c.label.startsWith("output") || c.label.startsWith("backend"),
        );
        if (live && fs.existsSync(live.path)) {
          sqftLog.warn(
            "duckdb",
            `parquet ${name}: using fixture ${p} but live data exists at ${live.path} — set SQFT_DATA_DIR or re-run make sample`,
          );
        } else {
          sqftLog.warn(
            "duckdb",
            `parquet ${name}: using fixture ${p} (fictional coords/buildings). Run make sample for live data.`,
          );
        }
      } else {
        sqftLog.info("duckdb", `parquet ${name} -> ${label} ${p}`);
      }
      return p;
    }
  }
  sqftLog.warn("duckdb", `parquet ${name} not found, using missing path ${candidates[0].path}`);
  return candidates[0].path;
}

export function parquetFromSql(name: string): string {
  return `'${sqlPath(parquetPath(name))}'`;
}

export function interimParquet(name: string): string {
  return parquetPath(name);
}

export function outputParquet(name: string): string {
  return parquetPath(name);
}
