# Nexus Spatial Intelligence

**Video analysis platform for the OpenCV AI Competition 2026, powered by AWS.**

A reproducible computer-vision application that analyzes video to produce spatial activity metrics, annotated outputs, and structured reports.

## Project Status

**Current Phase:** Milestone 1 — Local Video Pipeline Implementation  
**OpenCV Version:** 5.0.0 (verified)  
**Python Version:** 3.12.10  
**Last Updated:** 2026-10-23

See `docs/STATUS.md` for detailed component status and `docs/SESSION_HANDOFF.md` for next actions.

## Quick Start

### Prerequisites

- Python 3.12+
- Windows 10+ (or Linux/macOS with venv)
- Git

### Setup

```powershell
# Clone or navigate to the repository
cd nexus-spatial-intelligence-opencv

# Create and activate virtual environment
python -m venv venv
venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Verify OpenCV 5 installation
python verify_opencv.py
```

**Expected output:**
```
OpenCV version: 5.0.0
NumPy version: 2.5.4
...
[SUCCESS] All required OpenCV 5 features are available.
```

### Next: Implement M1

1. Obtain a test video and place it in `videos/`
2. Implement `src/video_analyzer.py` with motion analysis pipeline
3. Run: `python src/main.py videos/your_video.mp4`
4. Verify artifacts in `artifacts/{run_id}/`

See `docs/ROADMAP.md` for milestones and `docs/ARCHITECTURE.md` for system design.

## Project Structure

```
nexus-spatial-intelligence-opencv/
├── docs/                    # Continuity documentation
│   ├── AGENTS.md           # Persistent coding rules
│   ├── ARCHITECTURE.md     # System design and components
│   ├── DECISIONS.md        # Technical decision log
│   ├── ROADMAP.md          # Milestone planning
│   ├── STATUS.md           # Current verification status
│   └── SESSION_HANDOFF.md  # Next steps for future sessions
├── src/                     # Application source code
│   ├── __init__.py
│   ├── main.py             # CLI entry point (TODO)
│   └── video_analyzer.py   # Core pipeline (TODO)
├── tests/                   # Test suite (TODO)
├── videos/                  # Input video samples (not committed)
├── artifacts/              # Generated outputs (not committed)
├── requirements.txt        # Python dependencies
├── verify_opencv.py        # Verification script
├── .gitignore              # Git exclude patterns
└── README.md               # This file
```

## Key Technologies

- **OpenCV 5.0.0** — Computer vision processing, background subtraction, motion analysis
- **NumPy 2.5.4** — Array operations and numerical computation
- **Python 3.12.10** — Application runtime
- **Git** — Version control

AWS integration is deferred to a later milestone (M4).

## Development Notes

- All work is documented in continuity files before implementation
- Changes are verified by running the actual code, not by inspection alone
- Large artifacts (videos, model weights) are git-ignored
- Secrets and credentials are never committed

See `docs/AGENTS.md` for the complete coding workflow and `docs/DECISIONS.md` for architectural choices.

## License

This project is built for the OpenCV AI Competition 2026. See licensing information in submitted documentation.

## Contact / Questions

For implementation details, see the docs in the `docs/` folder.
