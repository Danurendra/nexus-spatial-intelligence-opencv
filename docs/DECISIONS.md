# Decision Log — Nexus Spatial Intelligence

Record decisions that affect product scope, architecture, data, evaluation, deployment, or team workflow. Prefer an append-only log: add a new entry when a decision changes, and link the superseding entry rather than silently erasing history.

## Status labels

- **Proposed** — an initial default that still needs validation.
- **Accepted** — explicitly chosen for the current implementation.
- **Superseded** — replaced by a later decision; retain for context.

## D-001 — Start with a local video-processing MVP

- **Status:** Accepted
- **Date:** 2026-10-23
- **Context:** The project has a short delivery window and cloud/frontend complexity could conceal basic computer-vision failures.
- **Decision:** First verify a local, end-to-end pipeline that reads one video and writes inspectable visual and JSON outputs. Add API, UI, and AWS layers only in sequence after the core path works.
- **Rationale:** This makes the core OpenCV behavior easier to debug, test, and demonstrate.
- **Consequences:** Local output generation and reproducible commands are the first acceptance criteria. Cloud deployment is not considered complete merely because local code exists.
- **Status update (2026-10-23):** M1 local pipeline IMPLEMENTED and VERIFIED with real video processing. Synthetic test video generated, processed, and all artifacts verified.
- **Revisit when:** The local pipeline passes repeatable tests (DONE - 13 tests passing) or an explicit competition requirement forces a different order.

## D-002 — Describe measurements precisely

- **Status:** Accepted
- **Date:** 2026-10-23
- **Context:** Basic motion/foreground methods can be confused with actual object or person detection.
- **Decision:** Label outputs according to what the implemented algorithm measures. Do not claim people counts, detection accuracy, or safety certainty without the corresponding implementation and validation data.
- **Rationale:** Technically honest claims make the demo and evaluation reproducible.
- **Consequences:** Metrics and user-facing labels must include definitions and limitations.
- **Revisit when:** A validated detector or manually labeled evaluation dataset is introduced.

## D-003 — Treat the architecture as provisional until code is inspected

- **Status:** Accepted
- **Date:** 2026-10-23
- **Context:** These files are being prepared before the new repository's implementation has been inspected.
- **Decision:** Document architecture and AWS integration as proposed until source code, configuration, and test evidence confirm implementation.
- **Rationale:** Prevents the continuity documents from creating false claims about the repository's state.
- **Consequences:** Update `ARCHITECTURE.md` and `STATUS.md` after implementation and verification.
- **Revisit when:** The repository has working code and the actual component boundaries are known.

## D-004 — Implement optional S3 artifact storage before real AWS deployment

- **Status:** Accepted
- **Date:** 2026-10-23
- **Context:** M4 AWS integration needed before competition submission; real AWS deployment adds complexity and cost.
- **Decision:** Implement optional S3 storage component with mock testing first, then defer real EC2/Lambda deployment to separate work phase.
- **Rationale:** 
  - Decouples storage abstraction from compute deployment
  - Allows mock-based testing without AWS resources or credentials
  - Enables local testing and M5/M6 work in parallel
  - Reduces risk of cost overruns during development
- **Alternatives considered:**
  - Deploy to EC2 first (more resources, more complex, higher cost)
  - Use only local storage (no AWS component for competition)
  - Full Lambda serverless setup (additional complexity, timeout constraints)
- **Consequences:**
  - S3 storage is optional and environment-configurable
  - Default behavior unchanged (local storage only)
  - Future work required for real-world EC2/Lambda deployment
  - All 46 original tests still pass; 22 new S3 tests added
- **Revisit when:** Competition requirements clarified or real AWS testing phase begins.

## Decision entry template

### D-XXX — Short decision title

- **Status:** Proposed / Accepted / Superseded
- **Date:** YYYY-MM-DD
- **Context:** What prompted the decision?
- **Decision:** What was chosen?
- **Alternatives considered:** What other plausible options were considered?
- **Rationale:** Why was this option chosen?
- **Consequences:** What changes or trade-offs follow?
- **Revisit when:** What evidence or event could change the decision?
