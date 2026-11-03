# MVP implementation boundary

The user approved starting the six-to-eight-week MVP discussed in chat, based on PRD v1.3. Choose Docker with WSL2 backend as the default dynamic runner on Windows; no custom junction/ACL dependency-sharing implementation. Implement sequential milestones: foundation, Docker/Laravel reference harness, internal test templates, revision loop, independent evaluator, pilot.

The foundation is an initial deliverable, not the finished MVP and not a percentage claim. JSON only, Python standard library, PHP tokenization without candidate execution. Structure checks use public index(), store(Request $request), show($id), update(Request $request, $id), destroy($id). Static success cannot imply functional correctness.

Use default qwen2.5:7b-instruct, temperature 0.2 and seed 42 for development only; final research settings remain undecided until pilot. The CLI must record actual configured options, request timeout, raw responses, code hash and environment. Never expose reference tests in generation prompts.

Deferred: Docker image and Laravel dependencies until Docker is available; independent evaluation, actual revisions, A/B, extra corpora. These remain backlog items, not implemented features.
