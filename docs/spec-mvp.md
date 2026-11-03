# MVP implementation boundary

The user approved starting the six-to-eight-week MVP discussed in chat, based on PRD v1.3. Choose Docker with WSL2 backend as the default dynamic runner on Windows; no custom junction/ACL dependency-sharing implementation. Implement sequential milestones: foundation, Docker/Laravel reference harness, internal test templates, revision loop, independent evaluator, pilot.

The foundation is an initial deliverable, not the finished MVP and not a percentage claim. JSON only, Python standard library, PHP tokenization without candidate execution. Structure checks use public index(), store(Request $request), show($id), update(Request $request, $id), destroy($id). Static success cannot imply functional correctness.

Use default qwen2.5:7b-instruct, temperature 0.2 and seed 42 for development only; final research settings remain undecided until pilot. The CLI must record actual configured options, request timeout, raw responses, code hash and environment. Never expose reference tests in generation prompts.

Harness update: Laravel 12.70.2/PHPUnit 11.5.57 dependencies now locked and installed locally. Docker image recipe, trusted products controller, 14 internal +7 readiness test cases, bounded-output Docker runner and CLI exist. Live reference readiness and image build remain unverified until Docker is available. Deferred: generic template generation, independent evaluation, actual revisions, A/B, extra corpora. No functional completion claim is allowed from the presence of harness files.
