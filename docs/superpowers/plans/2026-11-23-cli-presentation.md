# CLI Presentation Implementation Plan

> **For agentic workers:** Execute inline with test-driven-development and verification-before-completion. Preserve the user's existing uncommitted work.

**Goal:** Adapt PTerm-style presentation to all existing Python CLI commands.

**Architecture:** A standard-library console renderer controls automatic/explicit output modes and terminal-safe rendering. A context-local presentation session lets CLI, interactive entry and revision loop publish actual progress without changing result contracts.

**Tech Stack:** Python >=3.11 standard library, unittest, argparse.

**Spec:** ../specs/2026-11-23-cli-presentation-design.md

## Global Constraints

- Preserve CLI 0.5.0, component protocol 1.0, suite/image fingerprints, max3 and byte-identical stopping.
- Pure JSON on redirected stdout by default; raw prompt output; existing exit codes.
- No dependencies, candidate execution, archive rewrites or unrelated modifications.

## Review Focus

- Mixed root/subcommand flags, aliases and repeated main() calls must not leak presentation state.
- False/zero/null, long paths, nested records and unknown statuses must remain honest and readable.
- NO_COLOR, TERM=dumb, narrow terminals and terminal-control characters must degrade safely.
- Spinner must stop on results, errors, cancellation and before interactive input.
- Progress must not change persisted evidence or expose independent reference results to feedback.

## Task 1: Renderer and CLI modes

Files: new critic_agent/console.py, tests/test_console.py; modify critic_agent/cli.py.

- [x] Add behavior tests for pretty/JSON/auto modes, error exit codes, raw prompt and terminal fallback; verify RED.
- [x] Implement Console rendering, context scope, output flags and help styling.
- [x] Verify targeted tests GREEN.

## Task 2: Live progress

Files: critic_agent/orchestrator.py, critic_agent/interactive.py, tests/test_console.py.

- [x] Add controlled-loop integration test for stage messages and preserved result/archive semantics; verify RED.
- [x] Publish model/static/dynamic/attempt progress and style interactive messages/prompts.
- [x] Verify targeted tests GREEN, including identical-code/error outcomes and spinner cleanup.

## Task 3: Documentation and verification

Files: README.md, docs/progress.md, this plan.

- [x] Document automatic formatting, flags, pipe compatibility and scope.
- [x] Run full unittest suite, doctor/help and inspect representative pretty output.
- [x] Review changes and fix actionable issues; record final results below.

## Execution record

Work continues in the current checkout because it contains substantial pre-existing uncommitted implementation required by this CLI. Do not commit or relocate unrelated files.

23 November 2026: watched CLI tests fail on missing presentation flags and terminal formatting, then pass. The live-stage integration test failed on missing Qwen/Docker stage messages, then passed with real archive writes. Follow-up failing tests covered build-log separation and early help-mode preferences. All 16 presentation tests pass. Final full command `python -m unittest discover -s tests -v`: 193 tests, 78.676 seconds, OK, no skips; log `work/cli-presentation-final-tests.log`.

Initial full run (191 tests, before the two final build/help tests) timed out in `test_index_requires_complete_records_bound_to_integer_ids` and `test_reference_collection_binds_values_to_id_and_rejects_non_array`. Standalone rerun of all three products assertion/fingerprint tests passed in 8.030 seconds; both also pass in the final full run. No suite/test timeout was modified.

Doctor smoke: Python 3.13.7, PHP 8.3.30 and Docker server 29.9.2 ready; Ollama timed out, so no live model run is claimed. Pretty/JSON validate and help smokes passed. Independent code reviewer found no actionable issues. Suite/runtime/template sources and historical archives were not edited; no commit/push performed.
