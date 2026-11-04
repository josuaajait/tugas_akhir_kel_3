# Spec-driven resource harness and loop

Execute inline under the approved MVP/PRD and instruction to continue. Routine implementation decisions are delegated. Existing products commands, independent evaluator and archives stay compatible.

## Design

Generate a bounded spec-specific Laravel overlay and Docker image from the locked internal base: model, migration, routes, trusted controller, fixtures and Internal/Readiness tests. Hand-maintained resource copies duplicate behavior; full-project execution mounts expose unnecessary host data. Use a generated image with a contract fingerprint instead. Candidate execution stays Docker-only with the existing restrictions.

Generic internal policy mirrors products: five CRUD cases, each required field on store/update and three missing-ID cases (8+2*field_count). Type/unique/min/max edges and retaining own unique values validate the trusted reference at readiness only. These are development readiness cases, not independent evaluation. Reference evaluation remains products-only.

Fixture bounds: strings/integer v1; string bounds up to256; required strings must admit a nonempty value; unique integer domains must hold five fixtures. Reject unsupported/unsatisfiable contracts, PHP reserved classes and scaffold path conflicts before build/model calls. Specify model table explicitly. Rendered runtime copies the trusted helper and replaces its candidate destination with the validated class path; do not change the original helper/evaluator fingerprint.

## Tasks

1. Tests/test_resources.py:2/4-field specs, counts12/16, deterministic artifacts, satisfiable distinct fixtures, narrow integer/string bounds, exact table/routes/controller, PHP lint, wrong image fingerprint, restricted mount, no evaluation suite. Red before implementation.
2. critic_agent/resources.py: validate_resource_spec(spec), render_resource(spec)->dict[path,str], resource_contract(spec)->dict, build_resource(spec,output_root,...)->Path, ResourceDockerRunner(spec,...). Unique archived build contexts, immutable source hashes, separate base/target image, contract label checked at readiness.
3. resource_templates/: shared fixtures, Internal/Readiness tests. JSON requests, persisted DB snapshots, target/unrelated checks. Add books/inventory_items example specs. Reflect trusted providers to verify counts without candidate execution on host.
4. orchestrator: preserve run_products validator/count14; add run_resource wrapper with matching runner spec and variable count, share private loop/stopping/archive logic. Record count/contract in manifest. Generalize feedback field mapping.
5. CLI resource-build, resource-check (optional --code), run-resource; image critic-resource-{resource}:dev. Build/check never call Ollama. Existing CLI unchanged.
6. Complete Python suite, authored PHP lint, fresh reviewer (requesting-code-review). Update prior live evidence31/33->33/33 and CLI readiness21/21; document exact new Docker gate and no functional pass claims from mocks/lint.

## Review focus

- Fixture type/min/max/unique constraints: narrow negative integer range, one-char strings, impossible max0, singleton unique integer.
- PHP injection/name conflicts: validated identifiers/rules; reject reserved/scaffold names. Model table must match resource, not inferred pluralization.
- Wrong spec/count/fingerprint cannot LOLOS; runner spec mismatch rejected before model calls.
- Candidate Internal excludes readiness/reference-only cases; no final evaluator imports or prompt leakage; legacy products/evaluation sources unchanged.
- No source archives overwritten. Build directories unique; argv arrays; candidate execution never falls back to host.

## Execution checkpoint

Tasks1–6 implemented inline.96 Python tests pass;26 authored PHP files and9 rendered PHP files per example pass lint. Trusted providers expand books12+15 and inventory16+30. Fresh review fixes and red/green evidence cover evaluator-base aliases, one-sided unique integer bounds, mutable base reference, and target tag aliases. Ruling: use a private UUID tag created from inspected base ID, then cleanup, rather than treating a config image ID as a registry manifest digest in FROM. Source fingerprint for products evaluator is unchanged. Docker functional gate remains userCLI due desktop sandbox; current build smoke records ERROR without model calls. See docs/resource-harness.md for commands and deferred evaluation scope.
