import { defineConfig } from "vitest/config";
export default defineConfig({
  test: {
    environment: "jsdom",
    include: [
      "apps/web/test/**/*.test.tsx",
      "apps/web/test/**/*.test.ts",
      "apps/website/test/**/*.test.tsx",
      "apps/api/test/review.vitest.ts",
    ],
    restoreMocks: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "json-summary", "html"],
      reportsDirectory:
        process.env.PRAXIS_TS_COVERAGE_DIR || "evidence/review/typescript",
      include: [
        "apps/web/src/**/*.{ts,tsx}",
        "apps/website/src/**/*.{ts,tsx}",
        "apps/api/src/**/*.ts",
        "packages/contracts/src/**/*.ts",
      ],
      exclude: [],
    },
  },
});
