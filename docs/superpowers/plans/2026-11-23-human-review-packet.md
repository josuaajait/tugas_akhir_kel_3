# Human review packet preparation plan

**Goal:** Deliver the already-authorized external review packet for final-v1, ready for real human inspection, without granting approval or changing runtime behavior.

**Scope:** Repository-based Markdown/JSON forms and a self-contained ZIP. Reuse the five validated specs,358 traceability rows,70 internal mappings,10 positive controls and299 mutants. Link the existing separate16-case component-review packet; do not regenerate labels or predictions.

**Implementation ruling:** The user said “gas” after the concrete proposal to prepare checklist/evidence/external forms. Proceed directly with this artifact-only scope, preserve the dirty checkout and defer commits. No repeated design approval, application feature, new CLI, dependency, model call or Docker run is needed.

**Destination:** `docs/review-packets/final-v1-2026-11-23/`. Temporary construction and verification scripts/logs stay under `work/final-review-preparation/`.

## Deliverables

- [x] README/checklist explain per-case review, distinct human author/reviewer, actual dates, unresolved/rejected cases, old component-label exposure, and post-review rehash/freeze.
- [x] Five external pending forms clone the exact original case IDs and bind resource/package/spec/blank-form hashes. No human names, approvals, dates or rationale filled.
- [x] Five readable case worksheets cover each of358 assertions exactly once, distinguishing internal_covered/reference_only and linking payload, expected body/state, source assertion and controls.
- [x] Pending assignment and K2/FR20/component decision forms. Cross-reference P-06 and P-07 accurately; assignments remain unconfirmed.
- [x] New DRAFT protocol input copy preserves20-slot schedule/spec/image bindings and references the external forms/evidence. It remains BLOCKED; original draft unchanged.
- [x] Standalone reviewer ZIP includes the650 hash-bound package source files, exact validated traceability/report snapshots, technical summary and working forms/worksheets. Source snapshots retain original bytes/paths; mutable external forms have preparation-time hashes only.
- [x] Delivery manifest and verification summary bind ZIP/material/form hashes and describe what is included/excluded. No generated human attestation or “blind” assertion-review claim.

## Verification

- [x] Check every source/snapshot against recorded hashes and all650 package source hashes. Verify ZIP inventory and CRC, relative safe paths, all linked files and all358 case/expected/coverage/control bindings.
- [x] Verify all human fields/decisions are null/pending, original forms and both original manifests unchanged, packet SHA f2b648aeb042f4edcbb46b1b0160c87f93c326d084009cbc6de2f0f121e4a9b7 and adapter source SHA unchanged.
- [x] Run existing read-only protocol gate on the new draft: VERIFIED/BLOCKED,20slots,0model calls. No fresh code-test claim for this artifact-only change;253-test result remains the previous code checkpoint.
- [x] Update README/HANDOFF/status/progress with exact deliverables and remaining real human action. Run `git diff --check`.

Result: ZIP2,635,873bytes with1,389verified members,1,368material files and499verified authored links both locally and inside ZIP. SHA-2561d930dd5cf5316ac9aba08b9473a250c7ab7e96e79a800cf80f9a68e31500df3. Verification JSON records358cases/70internal/288reference_only,10positive controls/299mutants/648structured observations,16still-empty component labels and0human approvals. One construction correction included all observations, including internal passes for reference_only mutants that are not direct trace-row references; input evidence was unchanged. Construction ZIP/metadata retained in work/; final bundle is the only delivered version. No new application code, test run, model generation, candidate execution, commit or push.
