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
  const output = path.join(dataDir(), "output", `${name}.parquet`);
  if (fs.existsSync(output)) {
    sqftLog.debug("duckdb", `parquet ${name} -> output ${output}`);
    return output;
  }
  const interim = path.join(dataDir(), "interim", `${name}.parquet`);
  if (fs.existsSync(interim)) {
    sqftLog.debug("duckdb", `parquet ${name} -> interim ${interim}`);
    return interim;
  }
  const fixture = path.join(repoRoot(), "tests", "fixtures", `${name}.parquet`);
  if (fs.existsSync(fixture)) {
    sqftLog.debug("duckdb", `parquet ${name} -> fixture ${fixture}`);
    return fixture;
  }
  sqftLog.warn("duckdb", `parquet ${name} not found, using missing path ${output}`);
  return output;
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
