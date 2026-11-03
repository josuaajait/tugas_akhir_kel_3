# Laravel Harness Implementation Plan

> For agentic workers: use executing-plans task by task with tests before implementation.

**Goal:** Working reference CRUD harness and isolated Docker runner interface for the products contract.
**Architecture:** Small Laravel 12 app with SQLite and PHPUnit; controller acuan is trusted code. Candidate execution has one path: disposable non-network Docker container. No host fallback for candidates.
**Tech stack:** PHP 8.3, Laravel 12, PHPUnit 11, Python stdlib, Docker Linux containers.
**Spec:** ../../spec-mvp.md; root PRD v1.3, sections 9.1.1 and 12.1. This slice supports examples/products.json only; generic resource test generation is a later milestone.

## Constraints and review focus
- Existing CLI commands remain available. No functional LOLOS from unit tests or static-only results.
- Reference readiness test is local trusted code only; explicitly refuse local candidate paths.
- Candidate inputs are mounted read-only; image dependencies/tests never taken from candidate.
- Container has no network, no Docker socket/host home mounts, nonroot user, read-only root, bounded tmpfs, CPU/RAM/PID limits, external timeout and cleanup.
- JUnit counts, errors, skipped/empty suites and missing reports must not silently pass.
- Unknown spec variation rejected rather than running products tests against the wrong contract.

## Task 1 — Reference contract
Files: harness/laravel/{composer.json,bootstrap/app.php,config/*,routes/api.php,app/Models/Product.php,database/migrations/*,tests/Feature/ProductsContractTest.php,tests/TestCase.php,phpunit.xml,artisan}.
- [ ] Write PHPUnit cases for all CRUD operations, required fields, 404, response contents and database preservation; add reference-only edge cases separately.
- [ ] Install locked dependencies with scripts/plugins disabled, project-local Composer cache. Run tests with missing controller and observe failure.
- [ ] Add trusted ProductController implementing exact scalar-ID signature and full rules; run readiness suite twice (fresh data).

## Task 2 — Docker runner and JUnit
Files: critic_agent/sandbox.py; tests/test_sandbox.py; harness/Dockerfile; harness/entrypoint.php; harness/.dockerignore.
Interfaces: parse_junit(bytes)->dict; DockerRunner.check_reference()->dict; DockerRunner.check_candidate(path)->dict; SandboxError(RuntimeError).
- [ ] Tests: passing/failing/error/skipped/zero/missing/malformed JUnit, restrictive args, missing Docker and timeout cleanup, candidate mount points/read-only flags.
- [ ] Implement runner preserving stdout/stderr and reports. Candidate container results considered untrusted observations, not tamper-proof verification. No host fallback.
- [ ] Dockerfile builds locked dependencies into image; disposable container stages app on tmpfs and installs candidate only there. Use direct PHPUnit.

## Task 3 — CLI and handoff
Files: critic_agent/cli.py; README.md; AGENTS.md; docs/progress.md; harness/README.md.
- [ ] Add harness-build, harness-check (Docker reference readiness) and check-products (candidate requires prior Docker reference readiness).
- [ ] Check CLI nonzero environment errors; archive results/provenance with unique run IDs and configured limits.
- [ ] Run Python suite, real local trusted PHPUnit suite, lint PHP, and Docker checks if available. Document Docker not verified when unavailable; no manufactured live results.

## Decisions
- User authorized continuing in C:/Perkuliahan/TA. Work on current feature branch; no project relocation or new approval needed.
- System software is not installed automatically. Local trusted reference tests are development evidence, not proof of Docker isolation or generated-code success.
- Both base and edge suites validate the reference controller. Only the base suite is used for internal candidate checks; independent final reference evaluation remains deferred.
