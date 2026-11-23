# Final evaluation package implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Deliver the five approved CRUD contracts, separate internal/reference suites and auditable evaluator validation without model calls.

**Architecture:** New `final_package`, `final_controls`, `final_sandbox` and `final_validation` modules bind a new `evaluation/final-v1` package. Reuse trusted Docker transport and scaffold rendering; keep legacy hashed files unchanged. Final A/B execution and official freeze remain separate work.

**Tech Stack:** Python standard library, trusted PHP assertions, locked Laravel 12.70.2/PHPUnit 11.5.57, Docker Linux.

**Spec:** `docs/superpowers/specs/2026-11-23-final-evaluation-package-design.md` (approved by user: “oke lanjut implementasi”).

## Global constraints

- Application `0.5.0`, component protocol `1.0`; preserve all recorded legacy suite fingerprints.
- Specs categories/rooms/assets/courses/shipments, internal counts 12/12/14/14/18.
- Internal tests cover CRUD/omitted required/missing IDs; bounds/type/unique remain reference_only.
- Independent authored reference fixtures; no final Qwen generation or oracle feedback.
- Functional execution only in constrained Docker, fresh database per observation, immutable image ID; no host candidate execution or global software/security changes.
- Review metadata remains pending/null; ready_for_final is always false in validation evidence.
- Keep existing uncommitted work; no automatic commit, reset or worktree migration of the dirty baseline.

## Review focus

- JSON object numeric keys must not masquerade as a list; object/record/ID types checked from original JSON (Task 2).
- Unique database constraints can reject mutants for the wrong reason; require intended testcase failure and expected internal status (Tasks 2/4).
- Partial/cleanup-failed/test-skipped results and repeated instability must never pass validation (Tasks 3/4).
- Package/source/control tampering, changed base/image or unsafe output paths must be rejected or recorded as ERROR (Tasks 1/3/4).
- No model access or reference assets in internal image, including inherited files (Tasks 3/4).

### Task 1: Fixed package contracts and independent profiles

Files: create `critic_agent/final_package.py`, `evaluation/final-v1/specs/*.json`, `evaluation/final-v1/profiles/*.json`, `tests/test_final_package.py`.

Interfaces: `load_package(resource=None) -> list[dict]`; `package_manifest(resource) -> dict` includes spec/profile/hash/counts; `traceability(resource) -> list[dict]`.

- [x] Write tests for approved fields/counts, independent fixtures, every rule/vector mapped, tampered/unknown contracts rejected and legacy fingerprints unchanged.
- [x] Run `python -m unittest discover -s tests -p test_final_package.py -v`; observe RED for missing module.
- [x] Author fixed JSON assets and validation/hash functions; reference fixtures never call the internal generator.
- [x] Run task tests; expect GREEN.

### Task 2: Assertions, controls and mutations

Files: create `evaluation/final-v1/internal/*`, `evaluation/final-v1/reference/*`, `evaluation/final-v1/controls/*`, `evaluation/final-v1/mutants/*`, `critic_agent/final_controls.py`, `tests/test_final_controls.py`.

Interfaces: `control_catalog(resource) -> list[dict]` and `materialize_controls(resource, destination) -> dict` bind source/diff/targets/coverage. Profiles enumerate stable dataset names and target rule IDs.

- [x] Write trusted PHP assertion/provider/lint tests and mutation mapping/diff tests; observe RED.
- [x] Implement independent internal/reference PHP tests, strict original JSON shape assertions, two equivalent controllers per spec and one-fault mutants.
- [x] Generate and retain controls/mutants/traceability/review as package assets with hashes; metadata explicitly AI-prepared and unreviewed.
- [x] Run task tests; expect valid/reordered/extra-field controls accepted, malformed responses rejected, complete enumeration and PHP lint clean.

### Task 3: Isolated image build and runners

Files: create `critic_agent/final_sandbox.py`, package Dockerfiles/configuration/entrypoints, `tests/test_final_sandbox.py`.

Interfaces: `build_final(resource, role, output_root, *, base_image, timeout, execute) -> Path`; `FinalRunner(resource, role, **DockerRunner kwargs)` with exact count/hash verification.

- [x] Write tests for pinned base, tag cleanup, role/label mismatch, evaluator contamination, restricted mounts and partial reports; observe RED.
- [x] Render final scaffold and separate evaluator; labels bind package/spec/suite. Verify every observation against pinned ID and role.
- [x] Run task tests; expect GREEN and unchanged historical suite hashes.

### Task 4: Complete validation orchestration and CLI

Files: create `critic_agent/final_validation.py`, `tests/test_final_validation.py`; modify only additive routes in `critic_agent/cli.py`.

Interfaces: `validate_final(output_root, *, resources=None, build=False, local_only=False, base_image, timeout, build_timeout, runner_factory, builder) -> Path`. New `final-validate --package final-v1 [--resource NAME] [--build] [--local-only]`.

- [x] Write tests requiring two positive controls plus repeated observations, targeted negative failures, internal-pass checks for reference_only mutants, no model calls, failed cleanup/partial/instability ERROR and immutable archived inputs; observe RED.
- [x] Implement append-only UUID archives, local asset/lint checks and Docker validation, with per-case target IDs, raw provenance, counts and readiness independent of human freeze.
- [x] Run task tests; expect GREEN. Local-only status must say LOCAL_VALIDATED and functional validation NOT_RUN; no ready_for_final success.

### Task 5: Integration evidence, documentation and review

Files: package README/review form/manifest/traceability, docs evidence, README/HANDOFF/progress, approved design status.

- [x] Run the full Python suite, real local-only validation and CLI help; verify all legacy hashes.
- [x] Check Docker Server; if available run build/positive/mutant validation with same controls and record failures/retries. If unavailable retain ERROR evidence and exact rerun command, complete all unaffected work.
- [x] Obtain one fresh whole-change code review per executing-plans; fix important findings with RED→GREEN tests.
- [x] Update evidence/docs with actual outcomes and remaining human/freeze/A-B gates. Do not claim a live functional pass without Docker evidence.

Task commits are deferred because this checkout includes substantial user-owned uncommitted dependencies. Tests and an execution ledger preserve task progress without committing unrelated work.
