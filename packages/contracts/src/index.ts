import { z } from "zod";
export const TargetSchema = z
  .object({
    name: z.string().trim().min(1).max(120),
    kind: z.enum(["model", "agent", "application"]),
    provider: z.enum(["demo", "demo-failing", "openai", "ollama", "custom"]),
    endpoint: z
      .string()
      .url()
      .max(2048)
      .refine((value) => {
        try {
          const url = new URL(value);
          return (
            ["http:", "https:"].includes(url.protocol) &&
            !url.username &&
            !url.password &&
            !url.search &&
            !url.hash
          );
        } catch {
          return false;
        }
      }, "Endpoint must be HTTP(S) without credentials, query or fragment")
      .optional(),
    model: z.string().max(200).default(""),
    capabilities: z
      .array(
        z.enum([
          "text",
          "json",
          "tools",
          "code",
          "web",
          "image",
          "video",
          "audio",
        ]),
      )
      .max(8)
      .default(["text"]),
  })
  .strict();
export const RunRequestSchema = z
  .object({
    target_id: z.string().uuid(),
    suite_slug: z.string().regex(/^[a-z0-9-]{1,100}$/),
    suite_version: z.string().max(40),
    seed: z.number().int().min(0).max(2147483647).default(73),
    idempotency_key: z.string().uuid(),
  })
  .strict();
export const AssertionSchema = z
  .object({
    name: z.string().max(200),
    passed: z.boolean(),
    expected: z.unknown().optional(),
    actual: z.unknown().optional(),
  })
  .strict();
export const EvidenceSchema = z
  .object({
    run_id: z.string().uuid(),
    manifest_sha256: z.string().regex(/^[a-f0-9]{64}$/),
    runner_version: z.string().max(100),
    tasks: z
      .array(
        z
          .object({
            id: z.string().max(100),
            output: z.string().max(100000),
            assertions: z.array(AssertionSchema).max(100),
            latency_ms: z.number().nonnegative().max(86400000),
          })
          .strict(),
      )
      .max(1000),
  })
  .strict();
export const VoteSchema = z
  .object({
    choice: z.enum(["a", "b", "tie", "both_bad"]),
    rationale: z.string().max(2000).optional(),
  })
  .strict();
export type Target = z.infer<typeof TargetSchema>;
export type Evidence = z.infer<typeof EvidenceSchema>;
export const MAX_EVIDENCE_BYTES = 1024 * 1024;
