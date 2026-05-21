/**
 * Singleton DuckDB connection for Route Handlers. OWNED BY LANE D (or D1).
 *
 * Reads parquet files from $SQFT_DATA_DIR/{interim,output}/*.parquet directly.
 * No separate API service needed; the pipeline writes parquet, Next.js reads it.
 *
 * Wave 0 stub.
 */

import "server-only";
import path from "node:path";

import type { DuckDBConnection } from "@duckdb/node-api";

let _connectionPromise: Promise<DuckDBConnection> | null = null;

export function dataDir(): string {
  return process.env.SQFT_DATA_DIR
    ? path.resolve(process.env.SQFT_DATA_DIR)
    : path.resolve(process.cwd(), "..", "data");
}

export async function getConnection(): Promise<DuckDBConnection> {
  if (_connectionPromise) return _connectionPromise;
  _connectionPromise = (async () => {
    // Lane D: open an in-memory DuckDB, install/load spatial, register the parquet paths.
    // Example:
    //   const instance = await DuckDBInstance.create(":memory:");
    //   const conn = await instance.connect();
    //   await conn.run("INSTALL spatial; LOAD spatial;");
    //   return conn;
    throw new Error("Lane D: implement getConnection (Wave 0 stub)");
  })();
  return _connectionPromise;
}

/** Convenience: path to an interim parquet (e.g. footprints, geocoded). */
export function interimParquet(name: string): string {
  return path.join(dataDir(), "interim", `${name}.parquet`);
}

/** Convenience: path to an output parquet (estimates, qa_reviews, run manifest). */
export function outputParquet(name: string): string {
  return path.join(dataDir(), "output", `${name}.parquet`);
}
