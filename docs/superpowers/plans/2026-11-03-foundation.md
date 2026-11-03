# Critic Agent Foundation Implementation Plan

> For agentic workers: use executing-plans to implement task by task, with tests before implementation.

**Goal:** Deliver the first runnable slice: JSON specification → prompt → Ollama response → immutable run archive → non-executing PHP static checks.

**Architecture:** Python 3.11+ standard library, argparse CLI, urllib Ollama client, PHP tokenizer subprocess. No generated controller is executed by this slice. Docker feature tests and revision orchestration follow after prerequisites are available.

**Spec:** ../../spec-mvp.md and the supplied PRD_Critic_Agent_v1.3.md (project root).

## Global constraints
- Local Qwen2.5-7B-Instruct; no LLM inside Critic.
- One controller, scalar fields, fixed namespace and signatures; max three future revisions.
- No LOLOS status without dynamic tests. Foundation output uses AWAITING_DYNAMIC_TESTS or STATIC_FAIL.
- Fail before any model request for invalid input; preserve raw responses and failed generation attempts.
- No arbitrary shell execution of generated PHP, no automatic global installation.

## Review focus
- Input identifiers/path injection and unsupported rules: reject explicitly.
- Fenced/prose/ambiguous multi-file output: extraction must not guess among multiple candidates.
- Service failure/timeout/incomplete JSON: archive failure and retain model error category.
- Comments and string literals imitating methods: tokenizer must ignore them.
- Existing output folders: new run IDs and exclusive creation prevent overwrite.

## Task 1 — Contract and prompt
Files: critic_agent/spec.py, prompts.py; tests/test_foundation.py; examples/products.json.
Interfaces: validate_spec(data) -> dict; build_prompt(spec) -> str; SpecError(ValueError).
- [ ] Add failing tests: accepted product spec; invalid identifiers/status/type/rule/unknown key rejected; prompt contains signatures and JSON contract.
- [ ] Run `python -m unittest discover -s tests -v`; verify missing modules/features fail.
- [ ] Implement strict supported JSON schema and prompt; rerun targeted tests.

## Task 2 — Generation and provenance
Files: critic_agent/ollama.py, generation.py; same tests.
Interfaces: OllamaClient.generate(prompt) -> dict; extract_php(response) -> str; generate(spec, output_root, client) -> Path.
- [ ] Add failing tests for raw/fenced code, ambiguous output, payload stream=false/options, retry once, empty/truncated response, archive success/format failure/service error, no overwrite.
- [ ] Implement client and exclusive UUID archive, manifest/prompt/raw response/hash.
- [ ] Run tests with injected HTTP transport; no actual Qwen results asserted.

## Task 3 — Static inspection
Files: critic_agent/static.py; tests/test_static.py.
Interfaces: analyze(code, spec, php='php') -> dict; StaticEnvironmentError(RuntimeError).
- [ ] Test correct controller, syntax error, missing/wrong class, private method, missing signature, fake methods in strings/comments, absent PHP executable.
- [ ] Use PHP tokenizer with TOKEN_PARSE via fixed subprocess argument list, never include/eval candidate.
- [ ] Run real PHP tests and verify syntax/structure without executing candidate statements.

## Task 4 — CLI and handoff
Files: critic_agent/__main__.py, cli.py, doctor.py, README.md, pyproject.toml.
- [ ] Test subprocess CLI validate/prompt/analyze, invalid input error, nonzero doctor when prerequisites absent.
- [ ] Implement commands doctor, validate, prompt, generate, analyze; add timeout configuration and friendly Indonesian errors.
- [ ] Run full suite, sample commands and doctor. Document which live integrations are not verified.
- [ ] Review and checkpoint repository on feature branch; next task is Docker/Laravel harness, not research A/B.

## Execution rulings
- Existing PRD and explicit instruction to start authorize implementation of this slice; no new design approval requested.
- No Git repository exists; create a new project directory under outputs and a feature branch, rather than a linked worktree.
- Docker/Ollama binaries absent from PATH and usual locations; prepare integration interfaces, do not install system software or claim live results.
