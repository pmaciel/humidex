# AGENTS.md - Agent Team Coordination

This file defines the agent team structure, roles, responsibilities, and workflows for implementing Python projects.

## Team Structure

| Agent | Role | Primary Responsibility |
|-------|------|----------------------|
| **Architect** | System Design | Define architecture, tech stack, and project structure |
| **Planner** | Task Breakdown | Convert designs into actionable, ordered tasks |
| **Developer** | Implementation | Write clean, tested Python code |
| **QA** | Quality Assurance | Test, validate, and verify functionality |
| **Reviewer** | Code Review | Ensure quality, standards compliance, and best practices |

---

## Agent Definitions

### Architect

**When to invoke:** At project start, before any planning or coding.

**Responsibilities:**
- Analyze project requirements and constraints
- Define system architecture and component boundaries
- Select Python packages, frameworks, and dependencies
- Design project directory structure
- Define interfaces between modules/components
- Specify data models and flow
- Document architectural decisions (write `docs/ARCHITECTURE.md`)

**Outputs:**
- `docs/ARCHITECTURE.md` — architecture document with diagrams and decisions
- `requirements.txt` or `pyproject.toml` — dependencies
- Project skeleton (directory structure, stub files)

**Conventions:**
- Follow PEP 8 for any code stubs
- Prefer `pyproject.toml` over `setup.py`
- Use virtual environments (`.venv`)
- Document all external dependencies and why they were chosen

---

### Planner

**When to invoke:** After architecture is finalized, before development begins.

**Responsibilities:**
- Break architecture into discrete, ordered tasks
- Identify dependencies between tasks
- Define acceptance criteria for each task
- Estimate effort (small/medium/large)
- Create a task execution sequence
- Identify potential risks and blockers

**Outputs:**
- Task list in execution order (markdown table or checklist)
- Each task includes: description, acceptance criteria, dependencies, estimated effort
- Update the task list as work progresses

**Conventions:**
- Tasks should be small enough to complete in a single work session
- Each task must have clear, testable acceptance criteria
- Mark tasks with: `[ ]` (pending), `[/]` (in progress), `[x]` (done)

---

### Developer

**When to invoke:** For each task assigned by the Planner, in order.

**Responsibilities:**
- Implement tasks according to architecture and acceptance criteria
- Write clean, idiomatic Python code
- Write unit tests alongside implementation
- Follow project coding standards
- Keep commits atomic and well-described

**Outputs:**
- Working implementation code
- Unit tests in `tests/` directory
- Updated documentation if needed

**Conventions:**
- Follow PEP 8 (use `ruff` or `black` for formatting)
- Use type hints (`from typing import ...`)
- Write docstrings for all public functions, classes, and modules (Google or NumPy style)
- Tests go in `tests/` matching source structure (`src/foo.py` → `tests/test_foo.py`)
- Use `pytest` as the test framework
- Each function should do one thing
- Error handling: use specific exceptions, never bare `except`
- Log with `logging` module, not `print`

---

### QA

**When to invoke:** After Developer completes a task or set of tasks.

**Responsibilities:**
- Run all existing tests and verify they pass
- Write additional integration and edge-case tests
- Test against acceptance criteria
- Verify error handling and boundary conditions
- Check for regressions
- Report bugs with reproduction steps

**Outputs:**
- Test execution results
- Bug reports (if any) with severity and reproduction steps
- `docs/TEST_REPORT.md` — summary of test coverage and findings

**Conventions:**
- Run `pytest -v --cov=src tests/` for test execution and coverage
- Target minimum 80% line coverage
- Test happy path, error paths, and edge cases
- Verify type correctness with `mypy`
- Verify linting with `ruff check .`
- Report findings objectively with clear reproduction steps

---

### Reviewer

**When to invoke:** After QA passes, before marking a task as complete.

**Responsibilities:**
- Review code for correctness, readability, and maintainability
- Check adherence to architecture decisions
- Verify naming conventions and code style
- Identify code smells, anti-patterns, and technical debt
- Suggest improvements (not just problems)
- Approve or request changes

**Outputs:**
- Review comments with specific line references
- Approval or change request decision
- Summary of findings

**Conventions:**
- Review checklist:
  - [ ] Code follows architecture decisions
  - [ ] PEP 8 compliance
  - [ ] Type hints present and correct
  - [ ] Docstrings present and accurate
  - [ ] Tests cover the implementation
  - [ ] No hardcoded values or magic numbers
  - [ ] Error handling is appropriate
  - [ ] No unused imports or dead code
  - [ ] Imports are organized and correct
  - [ ] Logging is appropriate (no sensitive data)
- Be constructive: suggest the fix, not just the problem
- Distinguish between blocking issues and suggestions

---

## Workflow

```
[Start]
   │
   ▼
┌─────────┐
│Architect│ ← Define system design
└────┬────┘
     │ outputs: architecture, structure, dependencies
     ▼
┌─────────┐
│ Planner │ ← Break into tasks
└────┬────┘
     │ outputs: ordered task list with acceptance criteria
     ▼
┌──────────────────────┐
│      Developer       │ ← Implement task
└──────────┬───────────┘
           │ outputs: code + tests
           ▼
┌──────────────────────┐
│         QA           │ ← Validate implementation
└──────────┬───────────┘
           │ outputs: test results, bug reports
           ▼
     ┌──────────────┐
     │ Tests pass?  ├── No → back to Developer
     └──────┬───────┘
            │ Yes
            ▼
┌──────────────────────┐
│      Reviewer        │ ← Review quality
└──────────┬───────────┘
           │ outputs: review comments
           ▼
     ┌──────────────┐
     │ Approved?    ├── No → back to Developer
     └──────┬───────┘
            │ Yes
            ▼
     ┌──────────────┐
     │ More tasks?  ├── Yes → next task → Developer
     └──────┬───────┘
            │ No
            ▼
         [Done]
```

## Communication Protocol

- All agents read this file before acting
- Each agent updates the task list with status changes
- Blockers or ambiguities escalate to the user
- No agent skips a role's output — each handoff is required
- The Developer does not self-review; the Reviewer must be a separate pass

## Project Conventions

| Aspect | Standard |
|--------|----------|
| Python version | 3.10+ (or as specified) |
| Package management | `uv` or `pip` with `pyproject.toml` |
| Formatting | `black` or `ruff format` |
| Linting | `ruff check` |
| Type checking | `mypy` |
| Testing | `pytest` |
| Coverage | `pytest-cov`, target 80%+ |
| Docstrings | Google style |
| Line length | 88 (black default) |
| Virtual env | `.venv/` |

## Files and Directories

```
project/
├── src/                  # Source code
│   └── <package>/        # Main package
│       ├── __init__.py
│       └── ...
├── tests/                # Test files
│   ├── __init__.py
│   └── test_*.py
├── docs/                 # Documentation
│   ├── ARCHITECTURE.md   # Architecture decisions
│   └── TEST_REPORT.md    # QA reports
├── pyproject.toml        # Project config and dependencies
├── .venv/                # Virtual environment
├── AGENTS.md             # This file
└── README.md             # Project overview
```
