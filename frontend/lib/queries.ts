/**
 * Parameterized SQL queries for Route Handlers.
 */

import "server-only";

import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";

import type { DuckDBValue } from "@duckdb/node-api";

import type {
  ListLocationsQuery,
  ListLocationsResponse,
  LocationDetailResponse,
  PostQaRequest,
} from "./api-contract";
import { FLAG_EXPLANATIONS } from "./flag-copy";
import { getConnection, parquetFromSql, parquetPath, repoRoot } from "./duckdb";
import { sqftLog } from "./log";
import {
  CandidateBuildingSchema,
  EstimateRowSchema,
  FlagKeySchema,
  GeocodeResultSchema,
  type EstimateRow,
  type FlagKey,
} from "./schema";

function normalizeDuckRow(row: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(row)) {
    if (typeof value === "bigint") {
      out[key] = Number(value);
    } else {
      out[key] = value;
    }
  }
  return out;
}

function rowToEstimate(row: Record<string, unknown>): EstimateRow {
  return EstimateRowSchema.parse(normalizeDuckRow(row));
}

function activeFlags(row: EstimateRow): { key: FlagKey; explanation: string }[] {
  const out: { key: FlagKey; explanation: string }[] = [];
  for (const key of FlagKeySchema.options) {
    const col = `flag_${key.toLowerCase()}` as keyof EstimateRow;
    if (row[col] === true) {
      out.push({ key, explanation: FLAG_EXPLANATIONS[key] });
    }
  }
  return out;
}

export async function listLocations(q: ListLocationsQuery): Promise<ListLocationsResponse> {
  sqftLog.info("queries", `listLocations limit=${q.limit} offset=${q.offset}`, q);
  const conn = await getConnection();
  const est = parquetFromSql("estimates");
  sqftLog.debug("queries", `reading estimates parquet ${est}`);
  const conditions: string[] = [];
  const params: DuckDBValue[] = [];

  if (q.search) {
    conditions.push(
      "(lower(location_id) LIKE ? OR lower(address_input) LIKE ? OR lower(formatted_address) LIKE ?)",
    );
    const term = `%${q.search.toLowerCase()}%`;
    params.push(term, term, term);
  }
  if (q.confidence?.length) {
    conditions.push(`confidence IN (${q.confidence.map(() => "?").join(",")})`);
    params.push(...q.confidence);
  }
  if (q.location_type?.length) {
    conditions.push(`location_type IN (${q.location_type.map(() => "?").join(",")})`);
    params.push(...q.location_type);
  }
  if (q.state?.length) {
    conditions.push(
      `lower(split_part(address_key, '|', 3)) IN (${q.state.map(() => "?").join(",")})`,
    );
    params.push(...q.state.map((s) => s.toLowerCase()));
  }
  if (q.flag?.length) {
    for (const flag of q.flag) {
      conditions.push(`flag_${flag.toLowerCase()} = TRUE`);
    }
  }

  const where = conditions.length ? `WHERE ${conditions.join(" AND ")}` : "";
  const countSql = `SELECT count(*)::BIGINT AS total FROM read_parquet(${est}) ${where}`;
  const countReader = await conn.runAndReadAll(countSql, params);
  const total = Number(countReader.getRowObjects()[0]?.total ?? 0);

  const sql = `SELECT * FROM read_parquet(${est}) ${where} ORDER BY location_id LIMIT ? OFFSET ?`;
  const reader = await conn.runAndReadAll(sql, [...params, q.limit, q.offset]);
  const rows = reader.getRowObjects().map((r) => rowToEstimate(r as Record<string, unknown>));
  sqftLog.info("queries", `listLocations returned ${rows.length} of ${total}`);
  return { rows, total };
}

export async function getLocationDetail(
  locationId: string,
): Promise<LocationDetailResponse | null> {
  sqftLog.info("queries", `getLocationDetail id=${locationId}`);
  const conn = await getConnection();
  const est = parquetFromSql("estimates");
  const fp = parquetFromSql("footprints");
  const geo = parquetFromSql("geocoded");

  const estReader = await conn.runAndReadAll(
    `SELECT * FROM read_parquet(${est}) WHERE location_id = ?`,
    [locationId],
  );
  const estRows = estReader.getRowObjects();
  if (!estRows.length) return null;
  const row = rowToEstimate(estRows[0] as Record<string, unknown>);

  let geocode = null;
  try {
    const geoReader = await conn.runAndReadAll(
      `SELECT * FROM read_parquet(${geo}) WHERE address_key = ?`,
      [row.address_key],
    );
    const geoRows = geoReader.getRowObjects();
    if (geoRows.length) {
      geocode = GeocodeResultSchema.parse(geoRows[0]);
    }
  } catch {
    geocode = null;
  }

  let chosen_building: LocationDetailResponse["chosen_building"] = null;
  if (row.building_id) {
    const fpReader = await conn.runAndReadAll(
      `SELECT id,
              ST_AsGeoJSON(ST_GeomFromWKB(geometry_wkb)) AS geometry,
              overture_class,
              overture_subtype
       FROM read_parquet(${fp})
       WHERE id = ?`,
      [row.building_id],
    );
    const fpRow = fpReader.getRowObjects()[0] as Record<string, unknown> | undefined;
    if (fpRow?.geometry) {
      chosen_building = {
        id: String(fpRow.id),
        geometry: JSON.parse(String(fpRow.geometry)),
        area_sqft: row.footprint_area_sqft ?? 0,
        overture_class: fpRow.overture_class ? String(fpRow.overture_class) : null,
        overture_subtype: fpRow.overture_subtype ? String(fpRow.overture_subtype) : null,
      };
    }
  }

  const candidates = CandidateBuildingSchema.array().parse(
    JSON.parse(row.candidates_json || "[]"),
  );

  const manifestGlob = path.join(repoRoot(), "data", "output", "run_*", "manifest.json");
  const manifest_url = fs.existsSync(path.join(repoRoot(), "data", "output"))
    ? `/api/runs`
    : "/api/runs";

  return {
    row,
    geocode,
    chosen_building,
    candidates,
    parcel: null,
    flags: activeFlags(row),
    manifest_url,
  };
}

export async function appendQaReview(review: PostQaRequest): Promise<string> {
  const conn = await getConnection();
  const outPath = parquetPath("qa_reviews");
  const review_id = randomUUID();
  const reviewed_at_utc = new Date().toISOString();
  const escaped = outPath.replace(/\\/g, "/").replace(/'/g, "''");

  const values = {
    review_id,
    reviewed_at_utc,
    location_id: review.location_id,
    pipeline_run_id: review.pipeline_run_id,
    reviewer: review.reviewer ?? null,
    building_selection: review.building_selection,
    sqft_assessment: review.sqft_assessment,
    actual_sqft: review.actual_sqft ?? null,
    notes: review.notes ?? null,
  };

  if (fs.existsSync(outPath)) {
    await conn.run(`
      COPY (
        SELECT * FROM read_parquet('${escaped}')
        UNION ALL BY NAME
        SELECT ?::VARCHAR AS review_id,
               ?::TIMESTAMP AS reviewed_at_utc,
               ?::VARCHAR AS location_id,
               ?::VARCHAR AS pipeline_run_id,
               ?::VARCHAR AS reviewer,
               ?::VARCHAR AS building_selection,
               ?::VARCHAR AS sqft_assessment,
               ?::DOUBLE AS actual_sqft,
               ?::VARCHAR AS notes
      ) TO '${escaped}' (FORMAT PARQUET)
    `, [
      values.review_id,
      values.reviewed_at_utc,
      values.location_id,
      values.pipeline_run_id,
      values.reviewer,
      values.building_selection,
      values.sqft_assessment,
      values.actual_sqft,
      values.notes,
    ]);
  } else {
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    await conn.run(`
      COPY (
        SELECT ?::VARCHAR AS review_id,
               ?::TIMESTAMP AS reviewed_at_utc,
               ?::VARCHAR AS location_id,
               ?::VARCHAR AS pipeline_run_id,
               ?::VARCHAR AS reviewer,
               ?::VARCHAR AS building_selection,
               ?::VARCHAR AS sqft_assessment,
               ?::DOUBLE AS actual_sqft,
               ?::VARCHAR AS notes
      ) TO '${escaped}' (FORMAT PARQUET)
    `, [
      values.review_id,
      values.reviewed_at_utc,
      values.location_id,
      values.pipeline_run_id,
      values.reviewer,
      values.building_selection,
      values.sqft_assessment,
      values.actual_sqft,
      values.notes,
    ]);
  }

  return review_id;
}

export async function listRuns(): Promise<{ runs: unknown[] }> {
  const root = path.join(repoRoot(), "data", "output");
  const runs: unknown[] = [];
  if (!fs.existsSync(root)) return { runs };
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory() || !entry.name.startsWith("run_")) continue;
    const manifestPath = path.join(root, entry.name, "manifest.json");
    if (fs.existsSync(manifestPath)) {
      runs.push(JSON.parse(fs.readFileSync(manifestPath, "utf-8")));
    }
  }
  return { runs };
}
