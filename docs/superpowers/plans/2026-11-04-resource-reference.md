# Books and inventory independent development evaluation

Execute inline under the approved PRD/MVP and explicit next-milestone instruction. Apply writing-plans, TDD, executing-plans and final requesting-code-review. No new design approval needed for the already requested evaluator scope.

## Design

Add separate hand-authored JSON profiles and a PHP reference suite for books and inventory. Do not reuse generated internal/readiness test classes, fixture generator or their expected outcomes as oracle. Profiles pin the two supported contracts and independently chosen fixture/payload vectors. Sharing model/routes/migration infrastructure is allowed; assertions and fixture values are separate. These development packages are authored after observed Qwen outputs, not blind final evaluation. Final cases/review/freeze remain required.

Images derive from the matching current internal resource image, validated by its entrypoint and exact resource contract label; evaluator/resource mismatch fails before build. New evaluator image/entrypoint modes cannot be selected by run-resource. Label binds spec, profile, reference sources and base resource-contract hash. Build pins inspected ID with an owned UUID tag, honors timeout in all Docker steps, archives provenance and cleanup independently. Do not edit resources.py, internal templates, legacy products evaluation files or raw run archives; their existing fingerprints/images must remain usable.

Candidate/reference run the same independent suite in separate fresh restricted containers. Suite covers empty/list/create/show/update/delete, three missing-ID routes, invalid vectors separately for store and update, valid boundaries separately for both, own-value update and full CRUD sequence. Profile counts: books9 invalid +3 valid ->35cases; inventory17 invalid +6 valid ->57cases (11+2invalid+2valid). This is a test count, not a correctness/independence proof.

## Tasks and interfaces

1. tests/test_resource_reference.py: profiles/fixtures/counts, exact contract rejection, PHP lint/provider expansion, same-code pairs still execute twice, paired metrics at variable denominator, source tampering, unavailable code/syntax, environment/partial/image/suite mismatch, image-mode isolation, base rejection incl aliases, UUID pin and timeout/cleanup, CLI no-model behavior. Red before implementation.
2. evaluation/resource-reference/{profiles/books.json,profiles/inventory_items.json,ResourceReferenceTest.php,phpunit.xml,Dockerfile}; profile vectors manually specify payloads/field expectations. Template uses only its own profile and DB queries, JSON requests, persisted snapshots and record-isolation assertions. Existing evaluation/entrypoint.php may be copied unchanged into the new context.
3. critic_agent/resource_reference.py: resource_reference_manifest(spec), render_resource_reference(spec), build_resource_reference(spec,output_root,...), ResourceReferenceRunner(spec,...), evaluate_resource(loop_directory,output_root,runner). Only two approved profile contracts; mismatch is explicit. Default target critic-resource-RESOURCE-evaluation:dev, base critic-resource-RESOURCE:dev. Protect all known internal/base/products tags after Docker name normalization.
4. Parameterize existing reference.py paired evaluator via private shared function(expected_tests,suite_sha256,validator), while evaluate_products keeps33 and exact old contract behavior. ReferenceDockerRunner gets an overridable suite hash accessor; syntax preflight handling retained. New runner inherits bounded execution/cleanup/syntax behavior and validates its own suite plus resource label. Keep legacy source-suite fingerprint unchanged.
5. CLI resource-evaluation-build SPEC [--base-image/--image/--timeout/--output], evaluate-resource LOOP [--image/--timeout/--output]. EVALUATED includes valid failed candidates; ERROR has null aggregate metrics; denominator0 is N/A. Output concise, detail archived. Preserve sources and never call Ollama or send reference findings to revision feedback.
6. Run full Python suite, authored/generated PHP lint, trusted declaration/provider enumeration. Independent reviewer checks profile fixtures, DB assertions, modes/labels/base provenance and status semantics. Update README/progress/AGENTS/spec and exact userCLI commands on existing books/inventory loop directories. No actual Docker pass claims from desktop sandbox or mocks.

## Review focus

- Shared metadata must not become a shared testing oracle; profile vectors/readiness assertions are genuinely separate source/data from internal templates.
- Invalid payloads must violate the named field, valid boundaries satisfy all other rules, unique update excludes current record and preserves neighbor.
- Raw counts/metrics use35/57, never inherited33/14/16; identical books source still evaluated in two fresh containers.
- Suite/base mismatch cannot pass readiness; evaluator images must reject resource-* modes; source internal fingerprints remain unchanged.
- Archives with claimed missing/tampered code rejected; declared absent code/syntax0 with executed=false; partial/unknown timeout/error unavailable, not functional zero.
- Timeout/cleanup preserve primary error, only own UUID tag removed; no global security changes or host candidate execution.

## Completion checkpoint

Tasks1–6 implemented in0.5.0.116 Python tests pass;27 authored PHP files lint clean; provider expansion35/57 confirmed. Fresh review fixes resource-label gating and collection record matching with red/green regressions. Products reference and internal resource fingerprints/source archives are unchanged. Actual desktop CLI smoke is ERROR at Docker inspection/readiness, with metricsnull; userCLI functional gate remains outstanding. See evaluation/resource-reference/README.md for exact commands and development-versus-final scope.
