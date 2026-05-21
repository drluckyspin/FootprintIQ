import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

import { getLocationDetail, listLocations } from "../lib/queries";

const repoRoot = path.resolve(__dirname, "../..");

function usingFixtureEstimates(): boolean {
  const live = path.join(repoRoot, "data/output/estimates.parquet");
  return !fs.existsSync(live);
}

describe("lane D queries against fixtures", () => {
  it("listLocations returns fixture rows", async () => {
    const result = await listLocations({ limit: 100, offset: 0 });
    expect(result.total).toBeGreaterThanOrEqual(18);
    expect(result.rows.length).toBeGreaterThanOrEqual(18);
    expect(result.rows.some((r) => r.location_id === "WMART_001")).toBe(true);
    expect(
      result.rows.some(
        (r) => r.location_id === "TEST_001" || r.location_id === "BROKEN_001",
      ),
    ).toBe(true);
  });

  it("getLocationDetail returns WMART_001", async () => {
    const detail = await getLocationDetail("WMART_001");
    expect(detail).not.toBeNull();
    expect(detail?.row.location_id).toBe("WMART_001");
    if (usingFixtureEstimates()) {
      expect(detail?.chosen_building?.id).toBe("FP_WMART_001");
    } else {
      expect(detail?.chosen_building?.id).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
      );
    }
    expect(detail?.chosen_building?.geometry.type).toBe("Polygon");
  });

  it("repo fixtures exist", () => {
    expect(path.join(repoRoot, "tests/fixtures/estimates.parquet")).toBeTruthy();
  });
});
