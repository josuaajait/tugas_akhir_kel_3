# Critic Agent — working instructions

Read docs/HANDOFF.md first, then README.md, docs/spec-mvp.md and PRD_Critic_Agent_v1.3.md. docs/progress.md is chronological history; later dated outcomes supersede old pending paragraphs. Original user workspace is C:\Perkuliahan\TA; use the actual current clone root elsewhere.

## Latest verified state — 5 November 2026

- Python stdlib CLI0.5.0; component protocol1.0. Preserve version/suite fingerprints for unrelated work. Changes require coordinated new hashes/images; keep historical results.
- JSON contract, Ollama archives, PHP lint/tokenizer, Docker-only Laravel harness, max3 loop and independent development evaluators are implemented/live-verified.
- Products internal13/14→14/14 after1revision, LOLOS; reference31/33→33/33, repair1/1.
- Books internal12/12 initially,0revisions, LOLOS; reference35/35→35/35, repair0/0N-A.
- Inventory internal11/16→12/16 then identical_code at revision2, BELUM LOLOS; reference51/57→53/57, repair0/1. All4required update rules remain missing. Never edit source candidates to force success.
- Component evidence COMPLETE16cases in component-evidence/20261104T082952Z_reference-evidence_26a23f11d3ab49929f39605cde0bf690:4reference passes,11failures,1deliberate syntax fault,0environment errors,1duplicate reuse.
- Successful component run: component-runs/20261105T005526Z_component_4a131234b1c14b5a95421e211dcdf739, COMPLETE16/0 prediction_errors. Report provisional_unreviewed. Portable copy: docs/evidence/component-provisional-2026-11-05.json; provenance in docs/evidence/README.md.
- Synthetic matrixTP6/FP0/TN2/FN2:precision6/6,recall6/8,FPR0/2. Two FN are reference_only omissions max:title/min:pages; keep them in metrics. Qwen formative matrixTP3/FP0/TN2/FN0 on5unique cases after1duplicate:precision3/3,recall3/3,FPR0/2. No pooling across origins; held-out0/N-A. Samples are small/selected/development.
- Active curated corpus: corpora/annotations/20261104T085829Z_mikhael-ai-assisted_e7a9c4248c344f21aa2b3df91fca627c/corpus.json.16 filled labels,4 correct/12 problematic, all draft. Mikhael Josua Roganda attribution was user-requested; prepared_by=OpenAI Codex, human_author_review_attested=false. Do not invent reviewer, human inspection, timestamp or blind attestation. Reviewed metrics require actual distinct human author/reviewer, matching independent evidence and review before a fresh prediction run.
- Original evidence review/decisions.json was ALSO filled with AI-assisted draft proposals at user's request. Former blank form is backed up in review-backups/. Do not describe that folder as an unlabeled blind packet; prepare a clean packet for independent review.
- Historical code verification:134Python tests pass without skips on4November2026. Doc-only handoff changes are not a new code test run. Verify actual state in receiving environment.

## Next work

1. Recover setup/artifacts using docs/HANDOFF.md. Images/model/raw archives do not accompany Git clone. Curated corpora and docs report can be committed.
2. Implement/run pilot temperature/seed/diversity/cost manifest and aggregation; no pilot CLI/aggregator currently exists. PRD12.7 proposes2–3development specs × 3 seeds × temperatures0/0.2/0.5. Keep all failures/retries; calculate initial-failure and identical-code frequencies.
3. Complete actual label/assertion review and P-06/P-07/K2 decisions. Audit legacy products/internal collection assertion coverage before final freeze.
4. Implement/decide A/B generic feedback before freeze, or document attribution limitation. Initial→final uplift alone does not show causal benefit of specific feedback.
5. Separate held-out/final data, freeze protocol/model/suite/images and execute full manifest before final conclusions.

## Commands and safeguards

Run from project root: python -m unittest discover -s tests -v; python -m critic_agent doctor; python -m critic_agent --help. Docker readiness:products 21/21,books 27/27,inventory 46/46. Reference candidates:33/35/57. Base Laravel 12.70.2/PHPUnit 11.5.57 are locked.

Use Docker Desktop Linux/WSL2 on Windows. Never execute candidates on host PHP. Do not install system software automatically or change global security. Do not mount entire repo/socket/home into candidate containers. Clean only owned UUID containers/tags; no prune.

Missing dockerDesktopLinuxEngine pipe means endpoint unavailable: open Docker Desktop and confirm Client+Server from user terminal. Permission denied while Engine running is a separate sandbox limitation. User CLI has worked; desktop process may still be denied. CLI registry startup lookup may fail for per-user installs despite installed Docker. Avoid repeated unusable approval requests or declaring installation missing from one default path check.

Reference tests/results stay out of model prompts and internal feedback. Static pass cannot imply LOLOS. Do not change max3/byte-identical stopping to improve results. Qwen2.5:7b-instruct,temperature0.2/seed42 are development defaults; verify actual model digest/quantization/environment before final run.

Preserve raw response, prompt, history, code/spec hashes, ERROR and incomplete repairs. runs/,evaluations/,component-runs/,component-evidence/,builds/,work/ and vendor are Git-ignored. Include required code/corpora/docs in commits; do not assume ignored archives exist for a teammate. Never hand-edit old manifests/hashes for moved absolute paths. Use relative corpus snapshots or new development runs.
