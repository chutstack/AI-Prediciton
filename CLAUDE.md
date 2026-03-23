# CLAUDE.md — AI Prediction Project

This file provides guidance for AI assistants (Claude and others) working in this repository. Follow these conventions when reading, writing, or reviewing code.

---

## Project Overview

**Repository:** `chutstack/AI-Prediciton`
**Purpose:** AI-powered prediction system (project is in early initialization; this document will evolve as code is added).

---

## Repository Structure

As of initial setup, the repository is empty except for this file. The expected structure as the project grows:

```
AI-Prediciton/
├── CLAUDE.md              # This file — AI assistant guidance
├── README.md              # Human-facing project documentation
├── .gitignore
├── src/                   # Main source code
│   ├── models/            # ML/AI model definitions and training
│   ├── data/              # Data loading, preprocessing, pipelines
│   ├── api/               # API server / service layer
│   └── utils/             # Shared utilities
├── tests/                 # Test suite (mirrors src/ structure)
├── notebooks/             # Jupyter notebooks for exploration
├── scripts/               # One-off utility scripts
├── config/                # Configuration files (non-secret)
└── docs/                  # Extended documentation
```

> Update this section when the actual structure diverges from the above.

---

## Development Workflow

### Branch Strategy

- `main` / `master` — stable, production-ready code
- `claude/<description>-<id>` — AI-assisted feature branches (never push directly to main without review)
- Feature branches: `feat/<short-description>`
- Bug fix branches: `fix/<short-description>`

### Getting Started

Once dependencies are defined, the standard setup will be:

```bash
# Clone and enter
git clone <repo-url>
cd AI-Prediciton

# Install dependencies (update when package manager is chosen)
pip install -r requirements.txt     # Python
# OR
npm install                          # Node.js

# Run tests
pytest                               # Python
# OR
npm test                             # Node.js

# Start dev server / main entry point
python src/main.py
# OR
npm run dev
```

> Update this section with real commands once the project stack is established.

### Making Changes

1. Create a feature branch from `main`/`master`
2. Make focused, single-purpose commits
3. Write or update tests for any changed logic
4. Ensure all tests pass before pushing
5. Open a pull request with a clear description

---

## Code Conventions

### General

- Keep functions small and single-purpose
- Prefer explicitness over cleverness
- Do not add features, refactoring, or cleanup beyond what the task requires
- Delete unused code rather than commenting it out or adding backwards-compat shims

### Commit Messages

Use the imperative mood and be concise:

```
Add prediction endpoint for time-series data
Fix off-by-one error in sliding window preprocessor
Remove deprecated model loader
```

Avoid: `Fixed stuff`, `WIP`, `misc changes`

### Testing

- Tests live in `tests/` mirroring the `src/` structure
- Every public function/class should have at least one test
- Use descriptive test names: `test_predict_returns_confidence_score`
- Tests must not depend on external services unless clearly marked as integration tests

### ML / AI Specific

- Track model versions and training configs in code (not just file names)
- Never commit trained model weights unless they are small and intentional; prefer artifact storage
- Data pipelines must be reproducible: pin random seeds, document data sources
- Separate concerns: data loading, preprocessing, training, and inference should be independent modules
- Evaluation metrics must be logged and reproducible

---

## Environment Variables

Secrets and environment-specific config must never be committed. Use a `.env` file locally (add to `.gitignore`) and document required variables in `.env.example`:

```env
# .env.example — copy to .env and fill in values
MODEL_PATH=./models/latest
API_KEY=your_api_key_here
DATABASE_URL=postgresql://localhost/ai_prediction
LOG_LEVEL=INFO
```

> Add new required variables to `.env.example` whenever they are introduced.

---

## CI/CD

Once configured, CI should:

1. Run the full test suite on every push and PR
2. Lint and type-check the codebase
3. Block merges if tests fail

> Update this section when CI configuration is added (e.g., `.github/workflows/`).

---

## Key Files to Know

| File / Path | Purpose |
|---|---|
| `CLAUDE.md` | This file — AI assistant instructions |
| `README.md` | Project overview for humans |
| `.env.example` | Required environment variables |
| `src/models/` | Core prediction model code |
| `tests/` | Test suite |

---

## Notes for AI Assistants

- **Read before editing.** Always read existing files before modifying them.
- **Minimal changes.** Only change what is necessary for the task.
- **No speculation.** Do not add error handling, abstractions, or features for hypothetical future needs.
- **Ask on ambiguity.** If the task is unclear or the approach has meaningful trade-offs, ask rather than guess.
- **Security.** Never introduce SQL injection, XSS, command injection, hardcoded secrets, or other OWASP top-10 vulnerabilities.
- **This file evolves.** Update CLAUDE.md when project structure, tooling, or conventions change significantly.
