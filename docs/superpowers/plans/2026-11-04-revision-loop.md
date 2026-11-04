# Products revision loop implementation plan

> Execute inline using executing-plans, with tests before each implementation change.

**Goal:** One command verifies a products candidate, sends compact proven findings to Qwen, and rechecks up to three revisions.
**Architecture:** Reuse spec validation, prompt builder, OllamaClient, extract_php, static analyzer and DockerRunner. New feedback builder and orchestrator own only findings selection, iteration state and archives. All candidate execution stays in Docker.
**Spec:** ../../spec-mvp.md and root PRD v1.3 sections 8–10. Fixed products contract only. No reference-evaluator contents in the loop.

## Constraints and review focus
- LOLOS requires no static findings and actual PASSED_INTERNAL with 14/14 non-skipped internal cases. Unit-test doubles prove control flow only.
- Initial attempt index0, at most3 model revisions, up to4 examinations. Identical adjacent extracted code stops BELUM LOLOS before rechecking; failed model requests do not consume a completed revision.
- Raw responses/prompts, full findings and results are preserved. Only at most5 findings with compact evidence go into model feedback. Missing code is a format finding.
- Syntax errors skip dynamic testing, system/runner failures stop ERROR. Never reclassify an unknown/incomplete run as functional success.
- Resume from an archived generation only after checking exact spec and code hash. Preserve initial archive. Final is last accepted response, including unavailable code after format failure.
- Docker image must stay unchanged within loop. Existing runner checks reference readiness before each candidate. Pin first observed image ID for later attempts.

## Tasks
1. Add tests for feedback method/evidence mapping and omission of full stack traces. Implement feedback.py with build_feedback(static_findings,dynamic,iteration) and revision_prompt(spec,previous,feedback).
2. Add tests for repair, initial success, exhaustion, identical code, invalid output, skipped dynamics on static failure, model/environment errors, and resume hash checking. Implement orchestrator.run_products returning the archived folder.
3. CLI `run-products spec [--initial-run directory]` with image, output, model options and max-revisions0..3. Resume validates source provenance and rechecks in current corrected harness.
4. Run all Python tests, use current 13/14 candidate result to verify feedback content, and test environment errors. Live repair remains pending if Docker named-pipe access is still denied.

## Decisions
- Continue approved implementation scope without another design round.
- Repeated readiness checks trade runtime for use of existing checked runner API. Later attempts pin the first observed immutable Docker image ID.
- Default remains3 revisions, seed42, temperature0.2 for development. Independent evaluator and generic resource templates remain later milestones.
