# Reference evaluator implementation plan

> Execute inline using executing-plans and test-driven-development.

**Goal:** Separate command evaluates archived initial/final products code in identical fresh Docker environments and reports paired pass rates/uplift with raw counts.
**Architecture:** New evaluator-only Docker image derived from the locked harness image. Separate PHPUnit suite, entrypoint/config and image label with source-suite fingerprint. Reuse bounded DockerRunner via mode/count/status attributes. No evaluator import from feedback or orchestrator. Evaluation writes a new archive and never calls Qwen.
**Spec:** ../../spec-mvp.md and root PRD v1.3 FR15, section12.3 and12.6.

## Constraints and review focus
- Keep internal runtime image free of the new evaluation suite. Evaluator entrypoint accepts evaluation modes only, so passing that image to the internal loop fails readiness.
- New hand-authored suite covers full products contract independently of internal test code. This suite is authored after development outputs and must be reviewed/frozen with new final cases before final research conclusions.
- Verify original code hashes against history, reject missing/corrupted files when archives claim code exists. Missing model output declared by source archive gets0/33 with explicit not-run reason.
- Same immutable evaluator image and suite hash for initial and final. Separate container/SQLite fixture for each. Failed readiness, partial suite, or environment failure yields evaluation ERROR with metrics unavailable.
- Include raw numerator/denominator for repair/regression indicators. Denominator0 gives N/A. No aggregate population claims from a single run.
- Preserve generation/loop archives and never put evaluation reports into revision feedback.

## Tasks
1. Write evaluator tests for paired metrics, provenance/tampering, missing code, environment errors, immutable image, suite mismatch, isolated command modes and no model calls.
2. Extract trusted container staging/test/report runtime helper. Existing internal entrypoint keeps its old modes. Add evaluation-only image, configuration and33 independently authored test cases.
3. Parameterize existing DockerRunner only for modes/count/statuses and add reference runner with fingerprint validation.
4. Implement evaluate_products(loop_directory,output_root,runner), with code snapshots, per-position results and separate evaluation_result.json.
5. Add evaluation-build and evaluate-products CLI. Run all Python tests, PHP lint and source-suite case counting. Attempt Docker validation if access permits, otherwise document exact blocker and user verification commands.

## Implementation checkpoint

All five tasks implemented.77 Python tests pass;21 authored PHP files lint clean; trusted provider enumeration expands to33 cases. Fresh review fixes applied for JSON404 and staged runtime fingerprint. Actual Docker evaluation is pending: named-pipe permission denied from Codex. CLI smoke records ERROR with unavailable metrics and preserves source code. User commands documented in README and evaluation/README. Development suite is not frozen final evidence.
