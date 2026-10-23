# Session Handoff — Nexus Spatial Intelligence

**Last updated:** 2026-10-23  
**Session state:** Starter documentation prepared; implementation work has not been verified in the new repository.

## What this project is

Nexus Spatial Intelligence is intended to be a reproducible video-analysis application for the OpenCV AI Competition 2026, powered by AWS. The first deliverable is a local MVP that processes one video and produces inspectable visual and JSON outputs.

## Last verified checkpoint

- The six starter-document contents have been prepared: `AGENTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `STATUS.md`, and `SESSION_HANDOFF.md`.
- The target repository has **not** been identified or inspected in this session, so no claim is made about the application code, installed dependencies, tests, or deployment.

## Exact next steps

1. Create the new repository on GitHub or locally and put these six files at its root.
2. Open a terminal at the repository root and run the following read-only inspection commands:

   ```powershell
   git status --short --branch
   git log -5 --oneline
   Get-ChildItem -Force
   python --version
   python -m pip --version
   python -c "import cv2; print(cv2.__version__)"
   ```

   If Git is not initialized, note that fact instead of initializing over existing files. If `cv2` is missing, record the error; do not silently install or switch versions before inspecting the dependency setup.

3. Inspect the README, dependency files, source entry points, tests, and Docker configuration; update `STATUS.md` with observed facts.
4. Confirm the OpenCV 5 runtime requirement and video I/O support. Then implement the smallest working single-video pipeline.
5. After the first successful run, save the exact test command, output artifact names, elapsed time, and any warnings in `STATUS.md`.

## Commands not to run blindly

- `git reset --hard`
- `git clean -fdx`
- Repository reinitialization over existing history
- Commands that delete videos, artifacts, environment files, or cloud resources
- Cloud deployment commands before confirming account, region, IAM permissions, and cost limits

## Session completion checklist

Before ending a future work session:

- Record files changed and why.
- Record tests/commands actually run and their observed outcomes.
- Identify what is implemented versus tested versus independently verified.
- Update `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, and `STATUS.md` as appropriate.
- Replace this handoff with the exact last verified checkpoint and the single next action.
- Leave Git changes safe and explain whether a commit was created.

## Resume prompt

> Read `AGENTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `STATUS.md`, and `SESSION_HANDOFF.md`. Inspect the actual repository state without destructive changes. Do not assume any unverified status is complete. Continue from the exact next step in `SESSION_HANDOFF.md`, verify the result, and update the continuity files before the session ends.
