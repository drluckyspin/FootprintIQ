/**
 * Wave 0 smoke tests for the frontend. Each lane will add their own tests.
 */

import { describe, expect, it } from "vitest";

import {
  ConfidenceSchema,
  EstimateRowSchema,
  FlagKeySchema,
  RawAddressSchema,
} from "../lib/schema";

describe("schema smoke", () => {
  it("exports core schemas", () => {
    expect(RawAddressSchema).toBeDefined();
    expect(EstimateRowSchema).toBeDefined();
    expect(ConfidenceSchema).toBeDefined();
    expect(FlagKeySchema).toBeDefined();
  });

  it("EstimateRow has a flag_ boolean for every FlagKey", () => {
    const shape = EstimateRowSchema.shape;
    for (const key of FlagKeySchema.options) {
      const col = `flag_${key.toLowerCase()}`;
      expect(shape).toHaveProperty(col);
    }
  });

  it("Confidence enum includes unmatched", () => {
    expect(ConfidenceSchema.options).toContain("unmatched");
  });
});
