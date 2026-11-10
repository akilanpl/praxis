import { it, expect } from "vitest";
import { recordMatches } from "../src/records";
it("searches nested assertion/output fields and identifiers without dropping existing content search", () => {
  const record = {
    target_name: "Owned model",
    result: {
      tasks: [
        {
          id: "case-1",
          output: { nested: "FAILURE detail" },
          assertions: [{ actual: false, expected: 42 }],
        },
      ],
    },
  };
  for (const query of [
    "owned model",
    "failure DETAIL",
    "CASE-1",
    "false",
    "42",
    "expected",
  ])
    expect(recordMatches(record, query)).toBe(true);
  expect(recordMatches(record, "absent")).toBe(false);
  expect(recordMatches([{ value: "forty" }], "0")).toBe(false);
  expect(recordMatches(record, "  ")).toBe(true);
  expect(recordMatches(null, "null")).toBe(true);
  expect(recordMatches(undefined, "undefined")).toBe(false);
  const cyclic: any = {};
  cyclic.self = cyclic;
  expect(recordMatches(cyclic, "not-there")).toBe(false);
});
