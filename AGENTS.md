# Critic Agent project

This is the primary working directory selected by the user: C:\Perkuliahan\TA.
Read README.md, docs/progress.md, docs/spec-mvp.md, and PRD_Critic_Agent_v1.3.md before continuing.

Current implementation: Python stdlib CLI, strict JSON spec validator, Ollama client with run archives, PHP lint/tokenization without executing generated controllers. Foundation only: dynamic Laravel tests, revision loop, and independent reference evaluator are not implemented yet. Never claim functional LOLOS based solely on static success.

Run verification: python -m unittest discover -s tests -v
Check prerequisites: python -m critic_agent doctor

Next milestone: prove Docker/Laravel reference readiness, then generic internal test generation and revision loop. Harness source, locked dependencies, trusted products controller, PHPUnit cases, DockerRunner and CLI now exist; read harness/README.md. Docker is absent and real Laravel tests have NOT passed in this environment (PHP is_readable returns false even for readable files, blocking PHPUnit bootstrap). 45 Python tests pass; they do not prove live Docker correctness. Docker with WSL2 backend is the preferred Windows runner. Avoid custom junction/autoload hardening work. Do not install system software automatically. Candidate execution must never fall back to host PHP. The local trusted reference may be tested on host with normal PHP/Composer.

Use work/ for scratch, runs/ for generation archives. Keep real reference tests and their results out of model prompts and revision feedback. Preserve raw model output and experiment configuration. Temperature 0.2/seed 42 are development defaults only; final settings await pilot.
