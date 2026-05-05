# AGENTS.md — Agent Team Coordination

This file defines the agent team, their roles, and the workflow for implementing Python projects in this repository. It is read by OpenCode (with the `@opencode_weave/weave` plugin) on every session and informs the behavior of every agent.

You interact primarily with **Loom**. Loom plans, delegates, and supervises. The other agents work behind the scenes.

---

## Team Structure

| Agent (config key) | Display name | Role | Model tier |
|---|---|---|---|
| `loom` | Coordinator | Main orchestrator — routes work and supervises | Workhorse |
| `pattern` | Architect | Strategic planning and architecture decisions | Frontier |
| `tapestry` | Execution | Drives plan execution step by step | Workhorse |
| `shuttle` | Developer | Domain specialist that writes the actual code | Frontier |
| `thread` | Scout | Fast, read-only codebase exploration | Budget |
| `spindle` | Research | External docs and reference lookups | Budget |
| `weft` | QA / Reviewer | Quality review and test validation (mandatory gate) | Frontier |
| `warp` | Security | Security audit (mandatory gate) | Frontier |

**Tiering rationale.** Frontier models are reserved for any agent that produces or gates code: design (Pattern), implementation (Shuttle), review (Weft), and security audit (Warp). Workhorse models handle orchestration and execution coordination, which is routing logic rather than generation. Budget models handle read-only retrieval (codebase search, doc fetching).

---

## Agent Definitions

### Loom — Coordinator

**When invoked:** Default entry point. You talk to Loom; Loom decides who else needs to act.

**Responsibilities:**
- Assess the user's request and decide whether planning is needed.
- Delegate planning to Pattern, exploration to Thread, research to Spindle, execution to Tapestry, review to Weft, and security audit to Warp.
- Coordinate the response back to the user.
- Escalate ambiguities or blockers to the user instead of guessing.

**Outputs:**
- Routing decisions and delegation calls.
- Summary responses synthesized from specialist outputs.

---

### Pattern — Architect

**When invoked:** By Loom, at the start of any non-trivial task that requires design decisions, before code is written.

**Responsibilities:**
- Analyze project requirements and constraints.
- Define system architecture and component boundaries.
- Select Python packages, frameworks, and dependencies.
- Design directory structure and module interfaces.
- Specify data models and flow.
- Document architectural decisions.

**Outputs:**
- `.weave/plans/<task>.md` — the implementation plan with research, dependency mapping, and ordered tasks (each with description, acceptance criteria, dependencies, and effort estimate).
- `docs/ARCHITECTURE.md` — durable architecture decisions for the project.
- `requirements.txt` or `pyproject.toml` updates.
- Project skeleton (directories and stub files) when starting a new project.

**Conventions:**
- PEP 8 for any code stubs.
- Prefer `pyproject.toml` over `setup.py`.
- Use a virtual environment (`.venv/`).
- Document every external dependency and the reason it was chosen.
- Each task in the plan must be small enough to complete in a single session and must have testable acceptance criteria.

**Constraint:** Pattern's `Write`/`Edit` permissions are restricted to `.weave/*.md` files and `docs/`. It plans; it does not implement.

---

### Tapestry — Execution

**When invoked:** When the user issues `/start-work`, or when Loom hands off an approved plan.

**Responsibilities:**
- Read the approved plan from `.weave/plans/`.
- Drive sequential execution of plan tasks.
- Maintain a todo list reflecting plan status: `[ ]` pending, `[/]` in progress, `[x]` done.
- Delegate the actual implementation of each task to Shuttle.
- Pause for Weft and Warp gates between tasks where the plan requires it.

**Outputs:**
- Updated plan file with task statuses.
- Coordinated implementation across multiple Shuttle invocations.

**Constraint:** Tapestry cannot spawn subagents (this is locked in Weave's design). It executes plans directly and delegates only to Shuttle.

---

### Shuttle — Developer

**When invoked:** By Loom for one-off implementation requests, or by Tapestry for each task in a plan.

**Responsibilities:**
- Implement tasks according to the architecture and acceptance criteria.
- Write clean, idiomatic Python.
- Write unit tests alongside implementation.
- Keep changes atomic and well-scoped.

**Outputs:**
- Working implementation code under `src/`.
- Unit tests under `tests/` mirroring source structure.
- Updated documentation when behavior changes.

**Conventions:**
- PEP 8, formatted with `ruff format` (or `black`).
- Type hints on all public functions and methods.
- Google-style docstrings for all public functions, classes, and modules.
- Tests mirror source layout: `src/foo.py` → `tests/test_foo.py`.
- `pytest` is the test framework.
- Each function does one thing.
- Use specific exceptions; never bare `except`.
- Use the `logging` module, not `print`.
- No hardcoded secrets, no magic numbers — use named constants or config.

---

### Thread — Scout

**When invoked:** By Loom or other agents when codebase exploration is needed (finding files, searching for patterns, understanding existing code).

**Responsibilities:**
- Read-only navigation and search using `grep`, `glob`, and `read`.
- Answer questions about the codebase quickly and cheaply.

**Outputs:**
- File paths, code snippets, and structural summaries returned to the requesting agent.

**Constraint:** Read-only. No `Write` or `Edit` access.

---

### Spindle — Research

**When invoked:** When external documentation, library references, or web research is needed.

**Responsibilities:**
- Look up library docs, API references, and authoritative sources.
- Synthesize findings with citations.

**Outputs:**
- Synthesized research with source citations, returned to the requesting agent.

---

### Weft — QA / Reviewer (Mandatory Gate)

**When invoked:** Automatically after Shuttle completes any code change. Runs as a mandatory gate before the workflow completes — Loom cannot skip it.

**Responsibilities:**
- Run all existing tests and verify they pass.
- Verify additional integration and edge-case tests exist where the acceptance criteria require them.
- Verify type correctness with `mypy`.
- Verify linting with `ruff check .`.
- Check coverage and report gaps.
- Review code for correctness, readability, and maintainability.
- Check adherence to architecture decisions in `docs/ARCHITECTURE.md`.
- Identify code smells, anti-patterns, and technical debt.
- Distinguish blocking issues from suggestions.

**Outputs:**
- Test execution results.
- Bug reports with severity and reproduction steps.
- Review comments tied to specific files and lines.
- An overall decision: **approved**, **changes requested**, or **blocked**.
- `docs/TEST_REPORT.md` — running summary of coverage and findings (updated, not replaced, between runs).

**Conventions:**
- Run `pytest -v --cov=src tests/` for tests and coverage.
- Target a minimum of 80% line coverage.
- Test happy path, error paths, and edge cases.
- Reject only on true blocking issues; surface non-blocking concerns as suggestions.

**Review checklist:**
- [ ] Code follows architecture decisions.
- [ ] PEP 8 compliance.
- [ ] Type hints present and correct.
- [ ] Google-style docstrings present and accurate.
- [ ] Tests cover the implementation.
- [ ] No hardcoded values or magic numbers.
- [ ] Error handling uses specific exceptions.
- [ ] No unused imports or dead code.
- [ ] Imports are organized correctly.
- [ ] Logging is appropriate (no sensitive data).

---

### Warp — Security (Mandatory Gate)

**When invoked:** Automatically after Weft passes, before the workflow completes.

**Responsibilities:**
- Audit code for security issues: injection, unsafe deserialization, secret leakage, weak crypto, unsafe subprocess use, path traversal, SSRF, and dependency vulnerabilities.
- Verify no credentials, tokens, or keys are committed.
- Flag risky patterns even when they aren't strict vulnerabilities (e.g., overly broad permissions, unbounded input).

**Outputs:**
- Security findings with severity (critical / high / medium / low / informational).
- Remediation suggestions with the fix, not just the problem.
- An overall decision: **approved**, **changes requested**, or **blocked**.

---

## Workflow

```
[User talks to Loom]
       │
       ▼
   ┌───────┐
   │ Loom  │  Decides: simple task, or needs a plan?
   └───┬───┘
       │
       ├──── simple ──────────────────────────┐
       │                                      │
       ▼                                      │
   ┌─────────┐                                │
   │ Pattern │  Produces .weave/plans/*.md   │
   └────┬────┘  + docs/ARCHITECTURE.md        │
        │                                      │
        ▼                                      │
   ┌─────────┐                                │
   │  User   │  Reviews and approves the plan │
   │ approves│                                │
   └────┬────┘                                │
        │                                      │
        ▼                                      │
   ┌──────────┐                               │
   │ Tapestry │  Drives plan execution        │
   └────┬─────┘                               │
        │                                      │
        ▼                                      │
   ┌─────────┐  ◄─── Thread (search)          │
   │ Shuttle │  ◄─── Spindle (docs)           │
   └────┬────┘                                 │
        │                                      │
        ▼ ◄────────────────────────────────────┘
   ┌──────┐
   │ Weft │  Tests, lint, types, review
   └──┬───┘
      │
   ┌──┴────────┐
   │ Approved? │── No ──► back to Shuttle
   └──┬────────┘
      │ Yes
      ▼
   ┌──────┐
   │ Warp │  Security audit
   └──┬───┘
      │
   ┌──┴────────┐
   │ Approved? │── No ──► back to Shuttle
   └──┬────────┘
      │ Yes
      ▼
   [Loom summarizes to user]
```

**Mandatory gates.** Weft and Warp run automatically after code is written. They are not optional and Loom cannot skip them. Shuttle does not self-review.

**Continuation.** Tapestry resumes from `.weave/plans/` if a session is interrupted. The plan file is the source of truth for execution state.

---

## Communication Protocol

- All agents read this file at the start of every session.
- Plans live in `.weave/plans/`, written by Pattern, executed by Tapestry.
- Architecture decisions live in `docs/ARCHITECTURE.md`, written by Pattern, referenced by everyone.
- QA findings accumulate in `docs/TEST_REPORT.md`, updated by Weft.
- Blockers and ambiguities escalate to the user — no agent guesses.
- Each handoff has a defined output. No agent skips a downstream agent's work.

---

## Project Conventions

| Aspect | Standard |
|---|---|
| Python version | 3.10+ (or as specified in `pyproject.toml`) |
| Package management | `uv` or `pip` with `pyproject.toml` |
| Formatting | `ruff format` (or `black`) |
| Linting | `ruff check` |
| Type checking | `mypy` |
| Testing | `pytest` |
| Coverage | `pytest-cov`, target ≥ 80% |
| Docstrings | Google style |
| Line length | 88 (black default) |
| Virtual env | `.venv/` |
| Logging | `logging` module (never `print`) |
| Exceptions | Specific exceptions only (never bare `except`) |

---

## Repository Layout

```
project/
├── src/                  # Source code
│   └── <package>/        # Main package
│       ├── __init__.py
│       └── ...
├── tests/                # Test files mirroring src/
│   ├── __init__.py
│   └── test_*.py
├── docs/
│   ├── ARCHITECTURE.md   # Pattern's architecture decisions
│   └── TEST_REPORT.md    # Weft's running QA report
├── .weave/               # Created by Weave on first use
│   ├── plans/            # Pattern's plans, executed by Tapestry
│   └── state/            # Tapestry's execution state
├── pyproject.toml        # Project config and dependencies
├── .venv/                # Virtual environment
├── opencode.json         # OpenCode + Weave configuration
├── AGENTS.md             # This file
└── README.md             # Project overview
```

---

## OpenCode Configuration Reference

The agent roles, models, and behavior described above are wired up in `opencode.json` at the project root. That file controls model selection, fallbacks, and per-agent prompt overrides; this file (`AGENTS.md`) is the human-readable contract that every agent reads on every session. If the two ever drift, this file is the source of truth for *what* each agent should do; `opencode.json` controls *how* (which model, which tools).

