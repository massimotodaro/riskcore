# Claude Code Project Setup Instructions

> Give this file to Claude Code when starting a new project.
> It will create the optimal development structure and processes.

---

## Instructions for Claude Code

When the user starts a new project, create the following file structure and development processes. This setup is based on proven practices from production projects and the GSD (Get Shit Done) framework principles.

---

## Step 1: Create Core Project Files

### 1.1 CLAUDE.md (Project Context)

Create `CLAUDE.md` in the project root with this structure:

```markdown
# [PROJECT_NAME]

> [One-line description of the project]

## What Problem We Solve

[2-3 sentences describing the problem and why this solution matters]

---

## Core Principles

[List 3-5 core principles that guide development decisions]

- **Principle 1:** [Description]
- **Principle 2:** [Description]
- **Principle 3:** [Description]

---

## Tech Stack

| Layer | Solution | Notes |
|-------|----------|-------|
| Database | [e.g., PostgreSQL, Supabase, SQLite] | [Why this choice] |
| Backend | [e.g., Python + FastAPI, Node + Express] | [Notes] |
| Frontend | [e.g., React + Tailwind, Vue + Vuetify] | [Notes] |
| Auth | [e.g., Supabase Auth, Auth0, Custom] | [Notes] |
| Hosting | [e.g., Vercel, Railway, AWS] | [Notes] |
| Repo | [GitHub URL] | |

---

## What We BUILD (Unique Value)

[List features that are unique to this project - your differentiation]

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

---

## What We DON'T Build (Use Libraries)

**DO NOT REBUILD THESE — use existing open-source:**

| Need | Library | Notes |
|------|---------|-------|
| [Need] | [Library name] | [Why this library] |

---

## Architecture Overview

[Brief description of system architecture]

```
Layer 1: [Name]
  - Component A
  - Component B

Layer 2: [Name]
  - Component C
  - Component D
```

---

## Current Implementation State

**Last Updated:** [DATE]

### Backend

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| [Component] | `path/to/file.py` | ✅/⬜ | [Notes] |

### Frontend

| Component | Status | Notes |
|-----------|--------|-------|
| [Component] | ✅/⬜ | [Notes] |

### Database

| Migration | Purpose | Status |
|-----------|---------|--------|
| `[migration_name]` | [Purpose] | ✅ Applied / ⬜ Pending |

---

## Knowledge Sync

**For session continuity, these files contain project state:**

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `CLAUDE.md` | Architecture, decisions, context | When architecture changes |
| `ROADMAP.md` | Milestones, progress, verification | After each milestone |
| `STATE.md` | Current position, session log | After each session |
| `ISSUES.md` | Tech debt, deferred items | As issues discovered |

**Quick context restore:** Read `STATE.md` first, then `ROADMAP.md`.

---

## Key Documentation

| Doc | Location | Contents |
|-----|----------|----------|
| Architecture | `/docs/ARCHITECTURE.md` | System design, data flow |
| Decisions | `/docs/DECISIONS.md` | Key decisions with rationale |
| Tech Stack | `/docs/TECH_STACK.md` | Technology choices explained |

---

## Recent Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| [DATE] | [Decision] | [Why] |

---

## Commands

```bash
# Start backend
[command]

# Start frontend
[command]

# Run tests
[command]

# Other common commands
[command]
```

---

## Context for Claude Code

When working on this project:

1. **Always check /docs first** before implementing anything
2. **Don't rebuild** what existing libraries already do well
3. **[Project-specific guidance]**
4. **Ask if unsure** — check DECISIONS.md or ask for clarification

---

## Subagent Strategy

Use these subagent types strategically:

| Subagent | Use For | Example |
|----------|---------|---------|
| **Explore** | Finding files, understanding patterns across 3+ files | "Where is X handled?" |
| **Plan** | Architecture decisions, algorithm design | Complex feature design |
| **Bash** | Git operations, running commands | Tests, builds |
| **general-purpose** | Complex multi-step research | Library integration |

### When to Use Plan Agent

Before implementing complex features, **always use Plan agent first**:
- Features with multiple valid approaches
- Algorithm design
- Database schema changes
- API design decisions
```

---

### 1.2 ROADMAP.md (Progress Tracking)

Create `ROADMAP.md` with this structure:

```markdown
# [PROJECT_NAME] Development Roadmap

> Living document tracking development progress.
> **Last Updated:** [DATE]

---

## Quick Status

| Phase | Name | Status | Summary |
|-------|------|--------|---------|
| 1 | [Phase Name] | ✅/🔄/⬜ | [Brief summary] |
| 2 | [Phase Name] | ⬜ | [Brief summary] |
| 3 | [Phase Name] | ⬜ | [Brief summary] |

**Current Focus:** [Current phase/task]

---

## Phase 1: [Name] [STATUS]

**Target:** [What this phase delivers]
**Dates:** [Start] to [End]

### Milestones

- [ ] Milestone 1
- [ ] Milestone 2
- [ ] Milestone 3

### Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

### Verification Criteria (MUST PASS before Phase 2)

```
VERIFY-1.1: [Name]
  [ ] Run: [test command]
  [ ] Expected: [expected result]
  [ ] Manual: [manual verification step]

VERIFY-1.2: [Name]
  [ ] Run: [test command]
  [ ] Expected: [expected result]
```

### Files to Create

| File | Purpose | Status |
|------|---------|--------|
| `path/to/file` | [Purpose] | ✅/⬜ |

### Technical Notes

[Any important technical decisions or notes for this phase]

---

## Phase 2: [Name] ⬜ NOT STARTED

[Same structure as Phase 1]

---

## Success Metrics (End of Project)

| Metric | Target | Status |
|--------|--------|--------|
| [Metric] | [Target] | ⬜ |

---

*Last milestone completed: [Description] ([DATE])*
```

---

### 1.3 STATE.md (Session State)

Create `STATE.md` with this structure:

```markdown
# [PROJECT_NAME] State

> Living document tracking current development state.
> **Purpose:** Quick session context restoration, decision tracking, blocker visibility.

---

## Current Position

| Field | Value |
|-------|-------|
| **Phase** | [Current phase] |
| **Status** | [IN PROGRESS / COMPLETE / BLOCKED] |
| **Next** | [Next phase/task] |
| **Tests** | [X passing] |
| **Last Commit** | [commit hash] |

---

## Session Log

### [DATE] (Latest)

**Completed:**
- [What was done]
- [What was done]

**Tests Added:**
- `test_file.py` - X tests

**Key Decisions:**
- [Decision made and why]

**Blockers:** [None / Description]

---

## Architecture Decisions (Recent)

| Date | Decision | Rationale |
|------|----------|-----------|
| [DATE] | [Decision] | [Why] |

---

## Next Phase Preparation

### Dependencies
- [x] Dependency 1
- [ ] Dependency 2

### Files to Create
| File | Purpose |
|------|---------|
| `path/to/file` | [Purpose] |

---

## Verification Checklist (Current Phase)

- [ ] Verification item 1
- [ ] Verification item 2

---

## Quick Commands

```bash
# Run all tests
[command]

# Start server
[command]
```

---

*Last updated: [DATE]*
```

---

### 1.4 ISSUES.md (Tech Debt & Deferred Items)

Create `ISSUES.md` with this structure:

```markdown
# [PROJECT_NAME] Issues & Deferred Items

> Track technical debt, enhancements, and deferred work.
> **Purpose:** Don't lose good ideas. Review before each phase starts.

---

## Priority Levels

| Level | Meaning |
|-------|---------|
| P0 | Blocking - must fix before next milestone |
| P1 | High - should address this phase |
| P2 | Medium - address when convenient |
| P3 | Low - nice to have, future consideration |

---

## Open Issues

### P1 - High Priority

*None currently*

### P2 - Medium Priority

#### ISSUE-001: [Title]
**Created:** [DATE]
**Component:** `path/to/file`
**Description:** [What's the issue]
**Impact:** [What's affected]
**Suggested Fix:** [How to fix]

### P3 - Low Priority

*None currently*

---

## Closed Issues

*Issues will be moved here when resolved.*

---

## Enhancement Ideas (Future)

| ID | Idea | Phase |
|----|------|-------|
| ENH-001 | [Enhancement description] | [Future phase] |

---

## Review Schedule

- **Before each phase:** Review P1/P2 issues
- **End of project:** Review all issues, prioritize for next version

---

*Last updated: [DATE]*
```

---

## Step 2: Create Documentation Structure

### Create `/docs` folder with these files:

```
docs/
├── ARCHITECTURE.md      # System design, layers, data flow
├── DECISIONS.md         # Key decisions with rationale
├── TECH_STACK.md        # Technology choices explained
├── API.md               # API documentation (when applicable)
└── [DOMAIN_SPECIFIC].md # Domain-specific docs as needed
```

### 2.1 ARCHITECTURE.md Template

```markdown
# [PROJECT_NAME] Architecture

## Overview

[High-level description of the system]

## System Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Layers

### Layer 1: [Name]
[Description and responsibilities]

### Layer 2: [Name]
[Description and responsibilities]

## Data Flow

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| [Decision] | [Why] |
```

### 2.2 DECISIONS.md Template

```markdown
# [PROJECT_NAME] Decisions Log

## Decision Template

When adding a decision, use this format:

### [DATE] - [Decision Title]

**Context:** [What situation required this decision]
**Decision:** [What was decided]
**Rationale:** [Why this choice]
**Alternatives Considered:** [What else was considered]
**Consequences:** [What this means going forward]

---

## Decisions

### [DATE] - [First Decision]

**Context:** [Context]
**Decision:** [Decision]
**Rationale:** [Rationale]
```

### 2.3 TECH_STACK.md Template

```markdown
# [PROJECT_NAME] Tech Stack

## Overview

| Category | Technology | Version |
|----------|------------|---------|
| Language | [e.g., Python] | [e.g., 3.11+] |
| Framework | [e.g., FastAPI] | [e.g., 0.100+] |
| Database | [e.g., PostgreSQL] | [e.g., 15+] |

## Why These Choices

### [Technology 1]

**Chosen because:**
- Reason 1
- Reason 2

**Alternatives considered:**
- [Alternative]: [Why not chosen]

### [Technology 2]

[Same format]

## Dependencies

### Core Dependencies

| Package | Purpose | Required |
|---------|---------|----------|
| [package] | [purpose] | Yes/No |

### Dev Dependencies

| Package | Purpose |
|---------|---------|
| [package] | [purpose] |
```

---

## Step 3: Set Up Testing Structure

### Create test structure based on project type:

**For Python projects:**
```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Shared fixtures
│   ├── test_[module].py # One test file per module
```

**For JavaScript/TypeScript projects:**
```
src/
├── __tests__/
│   ├── setup.ts         # Test setup
│   ├── [module].test.ts # One test file per module
```

### Test File Naming Convention

- Test files mirror source files: `positions.py` → `test_positions.py`
- Test classes group related tests: `class TestCreatePosition:`
- Test methods describe behavior: `def test_create_position_missing_required_fields:`

---

## Step 4: Initialize Git with Proper Structure

```bash
# Initialize repo
git init

# Create .gitignore
# (Include common ignores for your stack)

# Initial commit with structure
git add .
git commit -m "Initial project setup with development framework"

# Create develop branch
git checkout -b develop
```

### Recommended Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code only |
| `develop` | Integration branch for features |
| `feature/*` | Individual features |

---

## Step 5: Development Workflow

### Daily Workflow

1. **Start of session:** Read `STATE.md` for context
2. **Before coding:** Check `ROADMAP.md` for current phase
3. **During coding:** Update `ISSUES.md` with any discoveries
4. **After milestones:** Run verification criteria
5. **End of session:** Update `STATE.md` with progress

### Verification Before Moving Phases

**CRITICAL:** Never move to the next phase until ALL verification criteria pass.

```
For each VERIFY-X.X in ROADMAP.md:
  [ ] Run the specified command
  [ ] Confirm expected result
  [ ] Complete manual verification
  [ ] Mark as checked
```

### Commit Strategy

- Commit after each completed milestone
- Commit message format:
  ```
  [Type]: Brief description

  - Detail 1
  - Detail 2

  Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
  ```

- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

---

## Step 6: Subagent Usage Guidelines

### When to Spawn Subagents

| Situation | Subagent | Why |
|-----------|----------|-----|
| Search across 3+ files | Explore | Reduces context usage |
| Complex algorithm design | Plan | Better architecture decisions |
| Git operations | Bash | Focused execution |
| Multi-step research | general-purpose | Comprehensive investigation |

### When NOT to Use Subagents

- Reading a specific file (use Read directly)
- Simple edits (use Edit directly)
- Single command execution (use Bash directly)

---

## Step 7: Context Management

### Preventing Context Rot

1. **Use subagents** for complex tasks (fresh context)
2. **Compact regularly** with `/compact` before context limit
3. **Reference files** instead of repeating information
4. **Update STATE.md** to persist decisions across sessions

### Session Recovery

If starting a new session:

1. Read `STATE.md` - current position and recent decisions
2. Read `ROADMAP.md` - verification status and next steps
3. Read `ISSUES.md` - any blockers or known issues
4. Continue from where left off

---

## Quick Setup Checklist

When starting a new project, create these files in order:

- [ ] `CLAUDE.md` - Project context and architecture
- [ ] `ROADMAP.md` - Phases with verification criteria
- [ ] `STATE.md` - Initial state
- [ ] `ISSUES.md` - Empty template ready for issues
- [ ] `/docs/ARCHITECTURE.md` - System design
- [ ] `/docs/DECISIONS.md` - Decision log
- [ ] `/docs/TECH_STACK.md` - Technology choices
- [ ] `.gitignore` - Appropriate for tech stack
- [ ] `README.md` - Basic project description

---

## Example: Applying to a New Project

**User says:** "I want to build a task management app with React and Supabase"

**Claude Code should:**

1. Create folder structure
2. Create `CLAUDE.md` with:
   - Problem: Task management for [target users]
   - Tech stack: React, Tailwind, Supabase
   - Core features list
3. Create `ROADMAP.md` with phases:
   - Phase 1: Setup & Auth
   - Phase 2: Core CRUD
   - Phase 3: Advanced features
   - Phase 4: Polish & Deploy
4. Create `STATE.md` with initial state
5. Create `ISSUES.md` template
6. Create `/docs` folder with templates
7. Initialize git with proper structure
8. Commit initial setup

**Then ask:** "I've set up the project structure. Should I proceed with Phase 1, or would you like to review/modify the roadmap first?"

---

*This setup guide version: 1.0*
*Based on: RISKCORE development practices + GSD framework principles*
