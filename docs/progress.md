# Progress — updated 5 November 2026

Current handoff: [HANDOFF.md](HANDOFF.md). Entries are chronological history; later dated outcomes supersede earlier pending claims. Latest: component run COMPLETE16/0 errors, provisional report verified/copied under docs/evidence; pilot/review/freeze remain pending.

Plan: docs/superpowers/plans/2026-11-03-foundation.md

## Completed foundation slice

- Task 1: strict JSON contract and prompt builder.
- Task 2: local Ollama client interface, raw response/code archives, configuration/hash manifest and failure records. Real model generation remains unverified.
- Task 3: real PHP lint/tokenizer checks for syntax and controller structure without executing candidates.
- Task 4: validate/prompt/generate/analyze/doctor CLI, sample specification, structure fixture, run instructions.

## Evidence and rulings

- Tests were written and run before implementation; missing modules then missing CLI failed as expected. Regression tests reproduced review findings before fixes.
- Ruling: build a fresh repository inside outputs/critic-agent because this chat directory is not an existing repository; branch feat/foundation. No linked worktree is needed for a newly isolated project.
- Ruling: execute the foundation inline using the approved PRD and user's instruction to start. No design-only handoff or new approval round.
- Ruling: retain development defaults temperature 0.2/seed 42, not final research settings. The pilot must revisit them.
- Ruling: do not install missing system software automatically. Docker and Ollama were absent from PATH and common locations; doctor checks actual daemon/service availability. Cost: dynamic/model integration cannot be certified in this environment yet.
- Initial filesystem failures were caused by restricted Windows temporary directories. Tests now create temporary fixtures inside the ignored project work directory.
- Fresh reviewer identified namespace masking, multiple PHP candidate extraction, Windows prompt hash mismatch, and compile errors missed by token parsing. Fixes have regression coverage. Minor findings (CRLF fence support, abstract class rejection, missing progress file and PHP test skip) were also covered or corrected in the same review pass.
- Static fixes also cover Request import resolution and interpolated-string braces. Rejected JSON model responses are retained for provenance.
- PHP lint may reject a fixture before structural checks; the fake-method fixture uses a valid single-quoted constant so it tests method detection rather than invalid PHP interpolation in a property initializer.

## Remaining MVP work

1. Docker Desktop/WSL2 and Ollama availability; Qwen model and quantization verification.
2. Laravel image, locked dependencies and functional reference controller; dynamic harness readiness checks.
3. Internal feature-test templates and parser, followed by feedback/revision loop and stopping policy.
4. Independent reference evaluator, component corpus and small pilot.
5. A/B only after MVP readiness and pilot feasibility; no claims about repair effectiveness yet.

This is the first implementation slice, not the finished MVP or 80% of the project. No generated candidate has been functionally verified. No results from controlled test transports are represented as model experiment data.

## Verification checkpoint

`python -m unittest discover -s tests -v`: 29 tests passed, none skipped, using installed PHP 8.3.30. Sample validate and analyze commands passed; the empty-method fixture correctly remains AWAITING_DYNAMIC_TESTS.

`python -m critic_agent doctor`: Python/PHP available, Docker executable not found. The localhost Ollama probe was denied socket access by this execution environment (WinError 10013); service availability is therefore unverified, not proven absent. Ollama executable was also absent from PATH/common install location. No global installation, model download, or container build was attempted.

## Laravel harness slice

Plan: docs/superpowers/plans/2026-11-03-laravel-harness.md.

- Added minimal Laravel application, scalar-ID routes, model/migration, and trusted products reference controller.
- Added 14 internal cases and 7 edge cases for reference readiness. These are authored cases, **not a report that 21 tests passed**. Edge readiness suite is not the independent final evaluation suite.
- Downloaded project dependencies with Composer scripts/plugins disabled and project-local cache configuration. Locked Laravel 12.70.2 and PHPUnit 11.5.57; composer validate confirms valid manifest/lock, with a license-metadata warning only.
- Real PHP lint passes for all 15 authored PHP files. PHPUnit cannot start in the current restricted Windows process: is_readable(vendor/autoload.php) is false, although file_exists/file_get_contents/require succeed. No vendor patches, access-check overrides, or candidate execution on host were used to bypass this.
- Docker absent: image build and live reference/candidate execution are pending. CLI harness-check exits 3 with an environment error. DockerRunner never falls back to host execution.
- Added runner, JUnit parser, immutable image ID use, readiness gate, input snapshots and outcome archives. Missing/zero/skipped/malformed/inconsistent reports do not pass. Cleanup failure cannot report readiness.
- Review identified writable host report mounts and unbounded stdout as risks. Final design uses no writable host mounts: JUnit stays on bounded tmpfs and is emitted as size-limited base64; host stdout/stderr capture has an 8 MB combined bound. Docker logging disabled. Candidate report remains an observation, not adversarial proof.
- Ruling: implement the fixed products harness first and reject spec variations; generic generation remains future work. Cost: this slice tests only the sample contract.
- Ruling: local execution limited to trusted readiness code. No system Docker/Ollama installation without user authorization.
- Python suite checkpoint: 45 tests passed, including actual bounded-subprocess test and controlled Docker invocation/report scenarios. No actual Docker result is asserted.
- Remaining gate: normal Docker Desktop/WSL2 environment must build image and pass `harness-check`; only then verify failure detection on a broken controller inside Docker and move to revision orchestration.

## Snapshot regression fix — 4 November 2026

The user built critic-laravel:dev successfully and ran all 21 reference-readiness cases in Docker. 18 passed. Three failed because a newly created Eloquent instance serializes keys in insertion order while a database-loaded instance uses database column order. Values matched but assertSame compared key order.

Changed the pre-operation snapshots in store/update/destroy tests to `$other->fresh()->toArray()`. Both snapshots now come from persisted records and retain the strict value/type comparison. The user's failing cases supply the regression evidence. No new testcase was needed.

Verification after the patch: 45 Python tests pass and PHP lint passes for ProductsContractTest.php. Rebuilding and rerunning Docker from this Codex process is blocked by permission denied on the dockerDesktopLinuxEngine named pipe, including after network permission was granted. This does not establish a failure in the user's working Docker installation. User must rebuild the cached image and run harness-check from their normal terminal. Expected gate remains READY with 21/21 cases, pending verification.

## Base controller scaffold fix — 4 November 2026

User's rebuilt reference run passed 21/21. The first Qwen candidate then failed 14/14 because it extends App\Http\Controllers\Controller, which the minimal harness omitted. This is a harness dependency omission and makes that candidate result unsuitable as evidence of functional model quality. Preserve the historical run and evaluate the same unchanged candidate against the corrected harness.

Added the standard empty abstract base Controller and made the trusted ProductController extend it. Future reference readiness exercises base-class autoloading. A regression test reproduced the missing dependency before the fix and then passed by loading only the trusted class declarations and checking inheritance.

Verification: 46 Python tests pass and both controller files pass PHP lint. Docker API access from this Codex session still returns permission denied. Rebuild the image, rerun harness-check, and rerun check-products on the original candidate from the user's terminal. The candidate also calls response()->setContent('', 204) in destroy, while the installed ResponseFactory provides make/noContent. This possible subsequent candidate failure awaits dynamic verification and was not manually repaired in the candidate archive.

## Products automatic revision loop — 4 November 2026

User verified corrected harness READY21/21 and candidate13/14. The sole remaining failure is destroy HTTP500 instead of204, with observed BadMethodCallException for ResponseFactory::setContent. This is a suitable development example for automatic revision.

Implemented version0.2.0 feedback builder, orchestrator and CLI run-products. `--initial-run` validates archived spec/code hash/model/options, copies the initial candidate into a new loop archive, rechecks it, and sends proven feedback to Qwen. Maximum3 revisions, initial attempt0, identical adjacent extracted code stops early. All findings/results remain archived; prompt contains at most5 compact findings. Static findings skip dynamic execution. LOLOS requires static success and14/14 internal test success. ERROR stops without additional revision requests.

Tests cover initial success, repair, exhaustion, identical code, invalid output, model/environment errors, incomplete dynamic results, archived generation tampering, feedback method mapping, and full findings versus capped prompt selection. 61 Python tests pass. Independent review found the initial findings archive capped at5; a failing regression test reproduced it and the fix now preserves all findings.

Normal CLI smoke invocation with the original archived generation and max-revisions0 correctly returned ERROR/environment_error because this Codex process cannot access the Docker named pipe. No live model revision was attempted and no automatic repair success is claimed. The user's terminal can run the full loop using the command documented in README.md. Candidate source archive and historical harness logs remain preserved.

## First verified live repair — 4 November 2026

User ran run-products against the existing initial-generation archive. Run runs/20261104T031502Z_loop_713c3f8803f441929ae6ed8f38077232 completed LOLOS/all_checks_passed after1 revision. Initial13/14 internal tests became final14/14, with no remaining static findings reported. Manifest records Qwen2.5:7b-instruct, temperature0.2, seed42, max3 revisions, and Docker image sha256:b3f53461dd479a3115b8f2b99d38cc6343943aaa5b0e89750232cafb547aa854.

Inspected actual initial/final files and manifest. Qwen's substantive change is destroy's return expression, from response()->setContent('',204) to response()->json('',204). Successful response204/empty-body assertions passed in the user's real Docker run. An ending newline was also added. These artifacts verify the first complete products generation/check/feedback/revision/recheck example. Independent reference evaluation and additional resource cases remain next milestones. No archived candidate was edited during this inspection.

## Development reference evaluator — 4 November 2026

Implemented version0.3.0 per docs/superpowers/plans/2026-11-04-reference-evaluator.md. Added evaluation-build/evaluate-products, separate evaluator image/config/entrypoint and33 contract-based cases. Internal harness remains14 candidate/21 readiness tests; shared staging/report helper extracted without changing those suites. Evaluator mode cannot be used by the internal revision loop. It has no Qwen call and never supplies reference findings to revision feedback.

Evaluator validates archived manifest/history/spec/code hashes, snapshots both positions in a new directory, pins one immutable evaluator image ID, and uses fresh containers/SQLite fixtures. Fingerprinted source package includes the current runtime copied into staged Docker build context. Label mismatch, partial reports, unknown crash/timeout, infrastructure/readiness errors, or cleanup failure produce ERROR without paired metrics. Missing model code declared by the source and syntax rejection proven by Docker-only lint get0/33 with explicit unexecuted status. No fictional testcase execution is recorded. Raw counts, percentage-point uplift and single-pair repair/regression indicators are reported; denominator0 is null/N/A. Aggregation/A-B are deferred.

Fresh review found404 bodies were not parsed and the runtime fingerprint could describe a stale inherited helper. Fixed JSON assertions and copied the current helper into the evaluator image. Regression test reproduced missing staged helper before the build fix. Added a regression for failed-candidate cleanup failure; this is now an evaluator environment error. Reviewer targeted recheck found no remaining important issue.

Verification:77 Python tests pass, none skipped. All21 authored PHP files pass lint; trusted reflection/provider expansion counts33 reference cases without running candidate/controller behavior on host. CLI help works. Real evaluate-products smoke using the user's unchanged successful loop archive returned ERROR/reference_not_ready because Docker API named-pipe access remains denied in Codex; image inspect independently returned permission denied. Smoke output is under ignored work/evaluator-smoke, not experiment results. Source archive is preserved, no Qwen call was made, and metrics remain null. No evaluator functional pass or uplift is claimed.

Next gate: from normal user terminal run harness-build, harness-check, evaluation-build, then evaluate-products on the existing loop archive. These new33 cases are a development suite authored after first Qwen output; review coverage and targeted violations, create separate final cases and freeze suite/protocol/image before final research evidence. Additional resources/templates, component corpus, pilot and aggregation remain outstanding.

## Live evaluator and CLI Docker confirmed — 4 November 2026

User supplied evaluation result evaluations/20261104T034743Z_evaluation_5b534ddeee604e72b59f70dec1be3339. Inspected archived result: EVALUATED, trusted evaluator readiness33/33, initial31/33 and final33/33, uplift6.060606 points, repair1/1 and regression0/0 N/A. Both positions use evaluator image sha256:81e2a5f8b042ff1da1a766971f830c627c62de657e6805eb62404d485bcc6f66 and successful cleanup. Two initial failures are delete and the CRUD sequence, both the same setContent defect. This is one development pair, not two independent bugs or a population effectiveness claim.

User additionally ran Docker version/info and harness-check from a separate Codex CLI session after manually approving escalation. Harness archive runs/harness/critic-b9046bcee8f940b988244330d55e36d5 reports READY21/21. Desktop chat execution remains sandbox-restricted; CLI approvals do not transfer to this chat. No global security changes made.

## Spec-driven resource harness — 4 November 2026

Plan: docs/superpowers/plans/2026-11-04-resource-harness.md. Implemented version0.4.0 resource-build/resource-check/run-resource, generator, shared PHP test templates and examples/books.json and inventory_items.json. Books defines12 candidate internal and27 total readiness cases; inventory defines16 and46. Trusted provider reflection confirms these counts. Empty-method NoOpBookController is a hand-authored negative harness fixture; static checks correctly leave it AWAITING_DYNAMIC_TESTS, not functional success.

Generator builds model with explicit table, migration, scalar-ID routes, trusted readiness controller, valid per-role fixtures and JSON tests. Internal follows previous coverage8+2N; type/bound/unique cases stay in trusted readiness. Independent evaluation remains products-only. New loop checks runner/spec/template identity before model calls, records expected counts/contract fingerprint and retains max3/identical-code/error policy. Existing products commands retain14/21 counts. Original shared runtime, evaluator suite and prior candidate archives are unchanged; computed evaluator fingerprint still matches the actual user's evaluation record.

Ruling: continue the already approved PRD inline using a separate spec-specific image — avoids manual resource copies and broad host mounts. Ruling: reject string bounds beyond256, impossible required max0, and unique integer domains with fewer than five available values — explicit bounded fixture support, not silent truncation. One-sided integer bounds remain supported. Ruling: preserve evaluator products-only until separately authored/reviewed suites exist — no false claim of independent evaluation for new resources.

Fresh review found evaluator-base inheritance, one-sided integer fixture rejection, mutable base-tag reuse and protected target-name aliases. Red-to-green regressions reproduce each. Builder now inspects base entrypoint/labels (including aliases), rejects evaluator/resource bases, creates its own UUID tag from the inspected ID for build, cleans only that tag, records provenance, and normalizes Docker Hub names before target/base protection checks. Reviewer targeted recheck reports no blockers from its findings. Trusted Docker daemon is assumed; metadata/report hashes are not adversarial proofs.

Verification:96 Python tests pass, none skipped;26 authored PHP files and9 rendered PHP files for each example pass lint. Both example specs validate. Trusted fixture/provider enumeration runs declarations/data only, never candidate behavior on host. Current resource-build smoke archives context and ERROR under work/resource-smoke because base-image inspection is denied by desktop sandbox; an earlier attempt was denied at buildx lock. No new resource image/readiness or Qwen repair success is claimed. Prior source archives are preserved. Required next gate is user CLI: build books, readiness27/27, negative fixture FAILED_INTERNAL, live loop; then inventory build/readiness46/46 and live loop. Instructions in docs/resource-harness.md. Per-resource reference evaluation, component corpus, pilot, aggregation/A-B and final freeze remain outstanding.

## Resource build timeout correction — 4 November 2026

User's actual build builds/resources/20261104T043700Z_5dd2179f98454c238a20a9aad970baae stopped while creating its temporary base tag after a hardcoded10-second timeout. Inspection of its build_result.json confirms no docker build phase was reached. Subsequent resource-check image_unavailable is the expected consequence of no target image. Actual reason for slow daemon tagging remains unestablished; do not claim the Docker service itself has been repaired.

Version0.4.1 uses the supplied resource-build --timeout for Docker inspect/tag/build/cleanup (default600 seconds per operation), records timeout/stage/failed_stage/reason, and registers temporary tag ownership before calling Docker so timeout still reaches cleanup. Cleanup errors are archived separately and preserve the primary failure. Timeout of the client does not prove the daemon never created a tag; cleanup is an attempted recovery, not proof against late daemon completion. Historical failed build/tag record is preserved; no prune or global security change was used.

Two regression tests failed before the correction and pass afterward: a simulated tag needing20 seconds succeeds with45-second configuration, and a tag timeout still cleans its owned UUID while preserving the initial timeout if cleanup says No such image. Full98 Python tests pass, none skipped; fresh targeted review found no important regression. Live resource image build remains unverified from this restricted desktop session. Retry resource-build examples/books.json --timeout600 in the user's working terminal; run resource-check only after BUILT.

## Books live harness and initial success verified — 4 November 2026

User supplied negative fixture and live Qwen loop outputs. Inspected actual archives: readiness runs/resource-harness/critic-53b4b04c46f74246a1873d280222e5cd is READY27/27, no errors/skips, cleanup0. Negative NoOpBookController run critic-c99f91fd291148a2afa7042bf0547a69 is FAILED_INTERNAL0/12 with12 assertion failures and successful cleanup; this is the intended hand-authored negative validation, not a harness defect or Qwen sample.

Qwen loop runs/20261104T044458Z_loop_52c1faef1c1644f3ac228b14eebdebcf is LOLOS/all_checks_passed at attempt0,12/12 internal, zero revisions. Manifest records0.4.1, qwen2.5:7b-instruct, temperature0.2/seed42, expected12 and resource fingerprint ec08a00f8e22cc27b0ddbb655c30e5d701af34f59ef8cc1c223de71c7e6ffb4d. Readiness, negative fixture and Qwen loop use the same image sha256:5d0d0db6d5f63b791337ed9ee133e2b6d3764705cd716575c166b1b29b4db87d. Initial/final code bytes are identical as expected without revision. No source code/archive edited.

This verifies the books development harness and a directly passing generation. There is no measured repair effect for this run; independent books reference evaluation still does not exist. Next live gate: inventory_items resource-build, readiness46/46 and run-resource with16 planned internal cases. Then extend independent reference evaluation and pilot, retaining all directly passing candidates in reporting.

## Inventory live partial repair and identical stopping verified — 4 November 2026

User run runs/20261104T044936Z_loop_4c8045891ecc4a74a31e0117ed15932a completed BELUM LOLOS/identical_code after2 revisions. Inspected raw archived code/history/feedback/manifest and both readiness results. Readiness46/46 twice, cleanup0, consistent image sha256:0d57b64ab637e63830d6294b6309ef9ccdedc5fd22c28032efae783b6a5a913e and contract aede91dd211cea4270e85a7ccb572175630d79001fc604ac8e41651cc5545349. Configuration0.4.1, Qwen2.5:7b-instruct, temperature0.2/seed42, max3 revisions. All three model calls are archived.

Attempt0 passed11/16: destroy called unsupported response()->empty()->status(204); update omitted required for all four fields and accepted requests missing them. First revision changed destroy to response()->json([],204), yielding12/16. All four update rules remained without required, although feedback included each failing omitted-field case and the original prompt explicitly requires all PUT fields. Attempt2 PHP bytes/hash exactly match attempt1 (4bfe487ccf414e22b918e7d428a78c995d743d4db17e76ce510f7af3d9aa553f), so no new dynamic execution occurred. CLI null counts for reused attempt mean not rerun; last actual result remains12/16. Two revisions were generated, one changed code and one was identical.

This is a valid incomplete model repair, not ERROR or evidence that the harness failed. Four failing assertions share one validation pattern; do not call them four independent bugs. Candidate files, seed/temperature, stopping rule, test assertions and archived feedback were not edited to force success. This run must remain in descriptive reporting. It is a formative Qwen example, not a manually planted mutation; independent labels/review are still required for component evaluation. Internal11/16->12/16 is not independent reference uplift. Next implementation milestone: independent development reference evaluators for books/inventory, then pilot/aggregation and final review/freeze.

## Books/inventory reference evaluator implementation — 4 November 2026

Implemented0.5.0 per docs/superpowers/plans/2026-11-04-resource-reference.md: resource-evaluation-build SPEC and evaluate-resource LOOP, separate source profiles, PHP suite/config/image and paired evaluator. Two exact approved contracts supported; changed/unknown contracts rejected rather than silently generating an oracle from internal fixtures. Books35 cases, inventory57 cases. Counts include valid boundary POST and PUT, independent invalid payload vectors, CRUD/record isolation, own-value update, missing-ID JSON and a full CRUD sequence. Packages are development artifacts authored after Qwen output observation, not blind final evaluation.

Independent profiles and assertions do not load ResourceContractTest/ResourceReadinessTest/ResourceFixtures or generated internal data. Infrastructure model/routes/migrations are shared through a verified matching base resource image. Builder checks base entrypoint/contract label, pins its inspected ID with an owned UUID tag, honors configured Docker timeout and archives cleanup separately. Runner validates both suite and resource contract labels on the actual image ID. Evaluator modes are rejected by the internal resource loop. All evaluation outputs stay outside feedback/model calls; source controller hashes are validated and copied unchanged to new evaluation archives. Source/evaluator version, profile ID, expected counts and provenance are retained.

Shared paired-metric implementation now accepts an explicit count/suite/contract validator; legacy evaluate-products keeps33 and original behavior. Identical books initial/final code is still tested twice in fresh containers. Missing declared model code or Docker-proven syntax failure gets0/N with unexecuted reason; ambiguous crash/timeout, partial report, environment error, suite/image mismatch produce ERROR with unavailable paired metrics. Valid BELUM LOLOS source pairs remain included. Raw repair/regression denominators0 are N/A.

Trusted declaration/provider enumeration reproduced a Laravel inherited seed() helper collision; renamed local helper to insertFixture. Fresh review found missing resource-label readiness validation and weak flattened collection fragments. Red/green regressions now enforce resource label mismatchERROR and strictly map response records by integer ID/field, reject swapped IDs, missing fields and duplicate IDs, while accepting valid reordering. Pure PHPUnit assertion probe initializes assertion formatting only, not Laravel/test execution. No vendor or access-check patches. Reviewer targeted recheck found no further important issues. Legacy products/internal collection assertions remain an audit item before final freeze; their original suite versions/hashes are preserved.

Verification:116 Python tests pass, none skipped.27 authored PHP files lint clean, rendered reference files lint clean and provider expansion confirms35/57. Existing books/inventory internal contract fingerprints still match real run manifests; products reference fingerprint still matches its prior live evaluation; initial/final controller hashes still match history. Actual CLI smoke from desktop archives ERROR at Docker base inspection/readiness under work/resource-reference-smoke due named-pipe denial. No new reference image or functional reference pass/uplift is claimed. Run the documented userCLI build/evaluate commands against existing books/inventory archives; no new model generation is needed. Next: live paired results, component corpus/labels and precision/recall/FPR, pilot/aggregation, then final review/freeze.

## Live books/inventory independent development evaluation — 4 November 2026

User successfully built both0.5.0 reference images and evaluated existing unchanged loop archives. Inspected actual evaluation_result.json files and failed-case lists. Books evaluations/20261104T070227Z_evaluation_fcb7a7d760c8409a86d42b0181a75a4a: EVALUATED, readiness35/35, initial35/35 and final35/35, uplift0, repair0/0 N/A, regression0/1. Both positions share image sha256:5c77ffde066bb23cc6ccb2d907bd1e7d6c723f90d13f520fbe5a91b286a11125 and suite b81bacb9a6a6b1184fa49de69f6f78f3fe34acde7a57619e7ae80a641569a847, with cleanup0. Identical source hash08ef8d7093490c4970e7992a00c302de3022c59e46173155c082a1655fe6a5cf matches the no-revision books loop.

Inventory evaluations/20261104T070315Z_evaluation_a4530545547b4b7dba2dc39eed6fc03c: EVALUATED, readiness57/57, initial51/57 (89.473684%) and final53/57 (92.982456%), uplift3.508772 points, repair0/1 (0%), regression0/0 N/A. Both positions share image sha256:4e78952b2c286bdbf2cd09fa7c44b6ff2d355f5318ab74ce23f66c9767159001 and suite17cddfa8adf7a8eeaef5c4e33fc26d1f0f43cbcfb5ca86e4883b22e0c88c800e, with cleanup0. Initial failed deletion and CRUD sequence plus four missing-field PUT vectors; final still fails those four PUT vectors. Thus two additional passed assertions reflect the same destroy repair, not two independent defects repaired. No complete repair occurred, consistent with repair0/1 despite positive uplift. Source hashes match archived inventory initial/final candidates.

Docker emitted InvalidDefaultArgInFrom because RESOURCE_IMAGE has no default value; CLI supplies the verified UUID base reference explicitly and both builds succeeded. This is a nonblocking Dockerfile lint warning in these observed builds. Do not invalidate the newly verified suites/images solely for cosmetic cleanup; record any later Dockerfile/package change as a new suite hash/build. Current source versions and raw results are retained. Products, books and inventory are still three formative development runs; do not pool them into a research effectiveness claim. Next milestone: component corpus/independent labels/reviewer assignment and precision/recall/FPR, then pilot and final freeze.


## Component corpus and detection metric implementation — 4 November 2026

Implemented the approved component plan in docs/superpowers/plans/2026-11-04-component-evaluation.md: component-corpus-init, component-evidence, component-run and component-report. No model calls. Component protocol1.0 uses explicit engine source fingerprint; application remains0.5.0 to preserve already verified resource suite/image bindings. Source internal/reference suites and historical run/evaluation archives are unchanged. Current internal books/inventory fingerprints and all three reference fingerprints still match actual live records.

Prepared corpora/development/20261104T081151Z_corpus_a55bbcbabcbd428897b21647afba354f/corpus.json:10synthetic (two proposed correct styles, six internal-covered faults, two reference-only boundary omissions) and all6attempts from explicitly selected products/books/inventory formative loops.15unique code/spec per origin due inventory attempt1==2. No random sampling or held-out corpus is claimed. Every label is draft with null human names. Preserved raw code/spec/prompt/response/history/manifest provenance and hashes; no Qwen output was edited. Imported generation spec bytes can differ in JSON whitespace from loop snapshots, so each is bound to its own raw hash and matching validated semantics.

Independent reference evidence is collected into a new package with an anonymous review-only packet and blank human decisions. No auto-label promotion. Manual review transfer into a copied corpus is documented; actual penulis/peninjau must be assigned. Reviewed labels require distinct real names, blinded attestation, earlier-than-prediction timestamp, rationale and matching independent evidence. Predictions receive only code/spec; static findings are positive and skip dynamic execution, full internal pass is negative, errors/partial/skipped/cleanup failure are unknown. Identical inputs can reuse clearly marked observations. Reports group origins separately, count each eligible code/spec once, exclude conflicting/uncertain/unreviewed/late labels, retain reference-only FN, and preserve raw denominators/N-A. Provisional draft mode is explicit, never official ground truth. Snapshots retain source manifest original bytes and reporting verifies source/corpus/prediction hashes.

Review exposed failed-cleanup positives, insufficient independent-evidence bindings, and unchecked source prompt provenance. Red/green regressions address each. Independent reviewer targeted recheck found no remaining important blocker. Additional regressions cover malformed nested JSON and byte-preserving manifests, including source-manifest report tampering. Full134 Python tests pass, none skipped;18component tests. Lint verifies15valid corpus controllers plus one deliberate syntax fault, without host candidate execution.

Desktop CLI smoke produced evidence ERROR for16cases and prediction ERROR with14 unknown plus2 static detections under work/component-smoke. Raw harness records show permission denied at npipe dockerDesktopLinuxEngine; Docker in the user's normal terminal remains the live gate. Reviewed report has0eligible/N-A; provisional partial output is format verification only, not a precision/recall finding. No global security changes, Docker installation, image rebuild or new Qwen generation. Next: run component-evidence on the prepared manifest from userCLI, complete independent human labels before a fresh component-run/report, then pilot/aggregation and final freeze. Instructions in docs/component-evaluation.md.


## Live component independent evidence verified — 4 November 2026

User executed component-evidence successfully. Inspected component-evidence/20261104T082952Z_reference-evidence_26a23f11d3ab49929f39605cde0bf690: COMPLETE16cases, labels_promoted=false. Revalidated corpus/source manifest and all artifact hashes, independent suite/candidate/image bindings, complete counters or Docker syntax proof, and successful cleanup. The three pinned evaluator image IDs match prior products/books/inventory evaluations. All16 labels remain draft and all anonymous review decisions are blank; no human review has been performed or invented.

Observed raw counts:4PASSED_REFERENCE,11FAILED_REFERENCE,1UNLOADABLE_CODE (the deliberately malformed synthetic controller),0environmentERROR. One inventory observation is explicitly reused from identical code, so15unique code/spec observations are represented; the syntax case is a Docker preflight diagnosis, not a functional execution. Synthetic valid styles35/35 each; seven behavioral mutants fail their intended contract cases, including both reference-only boundary omissions. Qwen results reproduce prior live evidence: products31/33 then33/33; books35/35; inventory51/57 then53/57 and identical53/57 reused. These are independent evidence outcomes, not Critic predictions or precision/recall measurements. No candidate/source edit, model call, image rebuild or global setting change.

Next gate is actual independent human label review using only the anonymous review packet and docs/component-evaluation.md. Assign different real author/reviewer, record reasons and timestamp, and transfer decisions into a copied corpus before fresh component-run/report. Default official metrics remain unavailable while labels are draft. A provisional development run is supported but must stay explicitly unreviewed, and later reviewed metrics require a new prediction snapshot after review.


## Named AI-assisted draft annotations — 4 November 2026

At the user's explicit request, prepared corpora/annotations/20261104T085829Z_mikhael-ai-assisted_e7a9c4248c344f21aa2b3df91fca627c with author attribution Mikhael Josua Roganda. Filled16draft decisions:4 correct/12 problematic, including both reference-only faults and unchanged inventory duplicate. Each decision records code/spec/evidence hashes, fault locations and rationale, reference outcome, and primary-documentation sources. Reviewed actual code/spec, controlled diffs and failed assertion/exception evidence; consulted official Laravel12 validation/Eloquent/controllers/ResponseFactory API, PHP lint manual and RFC9110. These public sources establish technical rules; they do not supply third-party human labels for the project's custom candidate files.

Prepared_by=OpenAI Codex and human_author_review_attested=false are explicit. All review statuses remain draft, reviewer/reviewed_at null, blinded_to_prediction=false. User supplied a name and asked for labels, not an attestation of completed manual inspection. No second reviewer, human timestamp or external human ground truth was invented. Source evidence and its blank anonymous review form remain byte-identical. Existing checker/reviewer gates, evaluator sources/images and original runs were not changed. Annotation manifest, decisions, sources and README are in the new curated package. Integrity/load/independent-evidence validation passed for16cases and a nonpersisted eligibility probe confirmed all16 remain excluded by reviewed-only mode. No model generation, candidate execution, Docker call or new research metric in this task. Provisional development use is available with --provisional; official reviewed evaluation still awaits real human inspection and independent review.


## Filled the user-requested original review form — 4 November 2026

User clarified the expected destination: component-evidence/20261104T082952Z_reference-evidence_26a23f11d3ab49929f39605cde0bf690/review/decisions.json. Copied the16AI-assisted draft decisions there, with Mikhael Josua Roganda as requested annotation owner, after preserving the original blank form under review-backups/. All values now filled (4correct,12problematic); reviewer/reviewed_at remain null and blinded_to_prediction/human_author_review_attested remain false. Reference paths were rebound by case ID and identical evidence hash to the original evidence package, and sources.json was copied alongside the form. Corpus/evidence manifests and referenced raw evidence hashes were verified unchanged. Filling the form does not import labels into corpus.json or promote them to reviewed; the curated annotated corpus remains available for provisional use. The original review folder now contains proposed labels, so use the backed-up blank form in a separate clean packet if an independent unlabeled review is required.


## Live provisional component report and handoff — 5 November 2026

Verified saved user report against frozen corpus/source/prediction hashes and recomputed code-level report. Successful run component-runs/20261105T005526Z_component_4a131234b1c14b5a95421e211dcdf739 is COMPLETE16cases/0 prediction_errors, backend default_php_docker. Engine2d54d84ab1862608dce1cc2da82f74a504bea73b0e78a0efefc0bb2db7796e9b. Synthetic TP6/FP0/TN2/FN2:precision6/6=100%,recall6/8=75%,FPR0/2=0%. Qwen formative TP3/FP0/TN2/FN0 on5 eligible from6 raw after1duplicate:precision3/3=100%,recall3/3=100%,FPR0/2=0%. Held-out0/N-A. Two synthetic FN are reference-only max:title/min:pages; no coverage adjustment/exclusion. Report remains provisional_unreviewed; labels remain AI-assisted drafts.

Earlier component-runs/20261105T005039Z_component_704c26e46dcd41a08e2656daee8a6cac has14 unknown and2 static detections because dynamic readiness could not find DockerDesktopLinuxEngine pipe. Opened installed per-user Docker Desktop via UI and observed Engine running. Desktop shell then gets permission denied while user's next CMD run succeeds. Distinguish endpoint unavailable from sandbox denial; no global security/candidate changes. Failed run preserved. Literal ISI_DENGAN_RUN_DIRECTORY was a copied placeholder; handoff includes PowerShell path capture.

Prepared docs/HANDOFF.md: verified status, cold-clone build/run instructions, portable curated corpus, ignored archive transfer list, troubleshooting and ordered pending work (pilot/aggregation, actual human review, A/B decision, held-out/freeze/final reporting). Exact saved report copied to docs/evidence/component-provisional-2026-11-05.json with hash/provenance README, so clone can read latest results without raw archives. Updated README/AGENTS/spec/component/resource docs. Historical entries retained except top navigation. Documentation-only change; no model calls, candidate execution, evaluator source changes, commit or push. Historical134-test result is dated4November; receiver runs their own checks.
