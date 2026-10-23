# AGENTS.md — Nexus Spatial Intelligence

## Purpose

Build **Nexus Spatial Intelligence**, a reproducible computer-vision application for the OpenCV AI Competition 2026, powered by AWS. The initial goal is a small, working local MVP that processes a video and produces inspectable visual and structured results. Cloud integration and advanced agent behavior must follow only after the local pipeline is verified.

## Source of truth

- The source code, tests, configuration, and reproducible command output are the source of truth for implementation status.
- `ARCHITECTURE.md` describes the current or explicitly proposed architecture; keep proposed components labeled as proposed until implemented.
- `DECISIONS.md` records significant choices and their rationale.
- `ROADMAP.md` records priorities and acceptance criteria.
- `STATUS.md` records verified progress and open blockers.
- `SESSION_HANDOFF.md` records the exact next action for the next session.
- When documents conflict with code or tests, inspect the code and tests, resolve the discrepancy, and update the affected document.

## Before making changes

1. Inspect `git status --short --branch` and `git log -5 --oneline` when Git is initialized.
2. Inspect the repository tree, existing README, dependency files, application entry points, tests, and relevant configuration.
3. Read the relevant sections of `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `STATUS.md`, and `SESSION_HANDOFF.md`.
4. Identify the smallest task that advances the current priority. State its acceptance criteria and likely files before implementing.
5. Preserve unrelated changes. Do not reset, clean, overwrite, or reinitialize an existing repository to make work easier.

## Implementation rules

- Prefer small, testable changes over large rewrites.
- Reuse existing working code when appropriate; do not recreate functionality without inspecting the repository first.
- Keep computer-vision processing deterministic where practical, configurable, and testable without a cloud account.
- Verify the actual installed OpenCV version with `cv2.__version__`; never report OpenCV 5 compliance unless the runtime reports a 5.x version and the required operations work.
- Clearly distinguish motion/foreground occupancy from actual people counting or object detection. Do not claim detection accuracy without a suitable detector and labeled evaluation data.
- Do not add an LLM or an “agent” merely for appearance. If adaptive analysis is implemented, ensure the first observation changes the subsequent action and preserve a trace of that decision.
- Keep AWS resources and permissions minimal. Prefer IAM roles over hard-coded credentials. Never commit credentials, `.env` files, access keys, personal data, or private test videos.
- Validate uploaded files, constrain file sizes and paths, handle processing failures, release video resources, and clean up temporary files.
- Keep generated datasets, videos, caches, model weights, build outputs, and other large artifacts out of Git unless the repository explicitly needs a small, licensed sample.
- Pin tested dependencies and document the exact commands used to reproduce results.

## Verification and evidence

- Do not infer that functionality works merely because its code exists.
- Separate **implemented**, **tested**, and **verified in the target environment** status.
- Run focused tests after a change, then the relevant wider test suite when feasible.
- Report the actual commands and outcomes. Never fabricate logs, test results, performance numbers, AWS deployment state, or competition compliance.
- For performance claims, record the input, configuration, environment, measured value, and limitations.
- When a check cannot be run, label it **UNVERIFIED** and explain why.

## Documentation update rules

- Update `ARCHITECTURE.md` when components, data flow, interfaces, or dependencies change.
- Add a record to `DECISIONS.md` after a significant technical or product decision.
- Update `ROADMAP.md` when priorities or acceptance criteria change.
- Update `STATUS.md` after meaningful implementation or verification work.
- Update `SESSION_HANDOFF.md` at the end of each work session with the last verified checkpoint and one precise next action.
- Update `AGENTS.md` only when persistent workflow or coding conventions change.

## Git practices

- Make focused commits with descriptive messages once a change is verified.
- Inspect `git diff` and `git status` before committing.
- Do not rewrite shared history, force-push, or commit generated secrets/artifacts.
- Never claim a commit or push succeeded without checking the resulting command output.

## Communication style

At the end of a task, summarize: what changed, what was verified, what remains unverified, any blockers, and the next recommended action. Keep explanations practical and concise.
