# ADR 0004: Dependency resolution cutoff for Windows Smart App Control

- Status: Accepted
- Date: 2026-09-29
- Owner: architect

## Context
Windows Smart App Control is enforced on the development machine (`VerifiedAndReputablePolicyState = 1`). It blocks native extension DLLs that don't yet have cloud reputation. The very latest wheels, `pyarrow 25.0.1` and `orjson 3.12.0`, failed with "An Application Control policy has blocked this file". Older releases of the same packages (`pyarrow 18.1`, `21.0`, `24.0`; `orjson 3.10`) loaded normally. This will hit other native wheels too, especially the Phase 2 ML stack.

Turning Smart App Control off is a one-way switch on Windows 11: it can't be re-enabled without reinstalling. That is Om's call, not ours.

## Decision
1. `backend/pyproject.toml` sets `[tool.uv] exclude-newer` to a date about three months back. uv then only resolves releases published before that date, which have had time to build reputation.
2. Version floors in `dependencies` stay loose so the cutoff can pick the newest safe release.
3. `orjson` was dropped. It isn't needed, because FastAPI's default JSON response is enough.
4. When a phase adds native dependencies (torch, onnxruntime, igraph, hdbscan), an import smoke test runs in the venv before any code depends on them.
5. The cutoff moves forward deliberately, at phase boundaries only, and every native import is re-verified after the move.

## Consequences
- The newest security fixes arrive with up to about three months' delay locally. Before the hosted build, the Docker image (Linux, no Smart App Control) is audited with `pip-audit`, and the cutoff can be lifted for the image if an audit finding requires it.
- The Docker images stay reproducible because the same lock file is used.

## Update (2026-09-30)
The `[tool.uv] exclude-newer` cutoff described above was never present in
`pyproject.toml`, and uv is not installed on the dev machine. The blocks
actually observed, and the version pins that fix them (ruff 0.12.0,
pandas < 3, scikit-learn < 1.7), are recorded in docs/DECISIONS.md D-25.
The import smoke test is `tests/test_imports_smoke.py`.
