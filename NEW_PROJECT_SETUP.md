# New Project Setup Guide

> How to set up a new project with Claude Code using the RISKCORE workflow.
> This guide captures lessons learned from building RISKCORE.

---

## Quick Start Checklist

```
[ ] Create project directory
[ ] Initialize git repository
[ ] Create CLAUDE.md (project instructions)
[ ] Create ROADMAP.md (milestones & progress)
[ ] Create STATE.md (session continuity)
[ ] Create ISSUES.md (tech debt tracking)
[ ] Set up .claude/ directory for templates
[ ] Configure hooks for validation
```

---

## 1. Project Structure

```
project-root/
├── CLAUDE.md           # Project instructions for Claude
├── ROADMAP.md          # Week-by-week milestones
├── STATE.md            # Session state (quick context restore)
├── ISSUES.md           # Tech debt & deferred items
├── .claude/
│   ├── hooks/          # Validation hooks
│   │   └── validate-python.ps1
│   └── review-checklist.md  # Pre-commit review template
├── backend/            # Python/FastAPI backend
├── frontend/           # React frontend (if applicable)
├── docs/               # Documentation
└── scripts/            # Utility scripts
```

---

## 2. Core Files

### CLAUDE.md (Project Instructions)

The main file Claude reads for project context. Include:

```markdown
# Project Name

## What Problem We Solve
[One paragraph explaining the core problem]

## Tech Stack
[Table of technologies and why]

## What We BUILD (Unique Value)
[Checklist of features we're building]

## What We DON'T Build (Use Libraries)
[Libraries to use instead of building from scratch]

## Architecture Layers
[High-level system design]

## Current Phase
[What we're working on now]

## Commands
[How to run tests, start servers, etc.]

## Context for Claude Code
[Specific instructions for AI behavior]
```

### ROADMAP.md (Milestones)

Track progress with verification criteria:

```markdown
## Week N: Feature Name

**Status:** IN PROGRESS | COMPLETE
**Dates:** Start to End

### Milestones
- [ ] Task 1
- [ ] Task 2

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

### Verification Criteria (MUST PASS)
```
VERIFY-N.1: Test Name
  [ ] Run: command to run
  [ ] Expected: what should happen
  [ ] Manual: manual verification step
```

### Files to Create
| File | Purpose | Status |
|------|---------|--------|
```

### STATE.md (Session Continuity)

Quick context restoration between sessions:

```markdown
## Current Position
| Field | Value |
|-------|-------|
| **Week** | N - Feature |
| **Status** | IN PROGRESS |
| **Next** | What's next |
| **Tests** | X passing |
| **Last Commit** | hash |

## Session Log
### Date Session N (Latest)
**Completed:** List of completed items
**Key Decisions:** Important decisions made
**Blockers:** Any blockers encountered
```

### ISSUES.md (Tech Debt)

Track deferred work:

```markdown
## Priority Levels
| Level | Meaning |
|-------|---------|
| P0 | Blocking |
| P1 | High |
| P2 | Medium |
| P3 | Low |

## Open Issues
### P2 - Medium Priority
#### ISSUE-001: Description
**Created:** Date
**Component:** file/service
**Impact:** What's affected
**Suggested Fix:** How to fix
```

---

## 3. Workflow Procedures

### Pre-Commit Persona Review

Before every commit, review from multiple perspectives:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRE-COMMIT REVIEW                        │
├─────────────────────────────────────────────────────────────┤
│ [0] CODE REVIEWER                                           │
│     [ ] Security issues (injection, XSS, secrets)           │
│     [ ] Error handling complete                             │
│     [ ] Edge cases covered                                  │
│     [ ] No hardcoded values                                 │
│                                                             │
│ [1] QA ENGINEER                                             │
│     [ ] Tests exist for new code                            │
│     [ ] Tests pass (run pytest)                             │
│     [ ] Edge case tests included                            │
│     [ ] No skipped/commented tests                          │
│                                                             │
│ [2] ARCHITECT                                               │
│     [ ] Follows existing patterns                           │
│     [ ] No unnecessary coupling                             │
│     [ ] Files in correct locations                          │
│     [ ] No circular imports                                 │
│                                                             │
│ [3] DOCUMENTATION                                           │
│     [ ] ROADMAP.md updated                                  │
│     [ ] STATE.md updated                                    │
│     [ ] New issues in ISSUES.md                             │
└─────────────────────────────────────────────────────────────┘
```

### Feature Branch Workflow

For complex features (like Week 4 Aggregation), use feature branches:

```bash
# 1. Create feature branch
git checkout -b feature/week4-aggregation

# 2. Develop with regular commits
git add . && git commit -m "Add netting service"

# 3. Run full test suite
python -m pytest backend/tests -v

# 4. Complete persona review (all checks pass)

# 5. Push feature branch
git push -u origin feature/week4-aggregation

# 6. Create PR for review (if team) or merge locally
git checkout develop
git merge feature/week4-aggregation

# 7. Delete feature branch
git branch -d feature/week4-aggregation
```

### When to Use Feature Branches

| Scenario | Use Feature Branch? |
|----------|---------------------|
| Simple bug fix | No - commit to develop |
| Single file change | No - commit to develop |
| New API endpoint | No - commit to develop |
| Complex multi-file feature | **Yes** |
| Core architecture changes | **Yes** |
| Risky refactoring | **Yes** |
| Week 4 Aggregation Engine | **Yes** |

---

## 4. Testing Strategy

### Test Pyramid

```
         ╱╲
        ╱  ╲     E2E Tests (few)
       ╱────╲    - Full workflow tests
      ╱      ╲   - API integration tests
     ╱────────╲
    ╱          ╲ Integration Tests (some)
   ╱────────────╲ - Service layer tests
  ╱              ╲ - Database tests
 ╱────────────────╲
╱                  ╲ Unit Tests (many)
────────────────────  - Pure function tests
                      - Model validation tests
```

### Test Organization

```
backend/tests/
├── conftest.py          # Fixtures
├── test_positions.py    # Position API tests
├── test_trades.py       # Trade API tests
├── test_risk.py         # Risk calculation tests
└── test_aggregation.py  # Aggregation tests (Week 4)
```

### Test Naming Convention

```python
class TestFeatureName:
    """Tests for feature description."""

    def test_action_scenario_expected(self):
        """Test that action in scenario produces expected result."""
        pass

    # Examples:
    def test_create_position_valid_data_returns_201(self): ...
    def test_create_position_missing_field_returns_422(self): ...
    def test_var_normal_distribution_matches_expected(self): ...
```

---

## 5. Commit Message Format

```
<type>: <short description>

<detailed description if needed>

<verification notes>

Co-Authored-By: Claude <model>
```

### Types

| Type | Use For |
|------|---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `refactor:` | Code restructuring |
| `test:` | Adding tests |
| `docs:` | Documentation |
| `chore:` | Maintenance tasks |

### Example

```
feat: Add VaR calculation with three methods

Implements Value at Risk using:
- Historical simulation
- Parametric (variance-covariance)
- Monte Carlo simulation

Verified:
- All 31 risk tests passing
- ATM delta ~0.5 as expected
- Put-call parity holds

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## 6. Session Handoff Protocol

### Starting a Session

1. Read STATE.md for current position
2. Read recent session log entries
3. Check ISSUES.md for blockers
4. Run tests to verify baseline
5. Continue from "Next" in STATE.md

### Ending a Session

1. Complete current task or reach safe stopping point
2. Update STATE.md:
   - Session log entry
   - Current position
   - Next steps
3. Update ROADMAP.md checkboxes
4. Add any new issues to ISSUES.md
5. Commit with descriptive message
6. Push to remote

### Context Recovery (After Compaction)

If conversation is summarized/compacted:
1. Read CLAUDE.md for project context
2. Read STATE.md for session state
3. Read ROADMAP.md for current week
4. Continue from last documented position

---

## 7. Quality Gates

### Before Marking Week Complete

```
QUALITY GATE CHECKLIST

[ ] All milestones checked in ROADMAP.md
[ ] All acceptance criteria met
[ ] All verification criteria passed
[ ] All tests passing
[ ] STATE.md updated with completion
[ ] No P0/P1 issues in ISSUES.md
[ ] Commit pushed to remote
```

### Battle Testing (Before Week Completion)

1. **Run full test suite** - All tests must pass
2. **Manual API testing** - Verify endpoints work
3. **Edge case verification** - Test empty data, invalid input
4. **Schema validation** - Queries work against actual DB
5. **Documentation review** - ROADMAP updated, verification done

---

## 8. Common Patterns

### API Endpoint Pattern

```python
@router.get("/resource/{id}", response_model=ResourceResponse)
def get_resource(
    id: UUID,
    tenant_id: UUID = Query(..., description="Tenant ID"),
):
    """
    Get resource by ID.

    - **id**: Resource UUID
    - **tenant_id**: Tenant for multi-tenant isolation
    """
    with get_db_connection() as conn:
        service = ResourceService(conn)
        result = service.get_by_id(id, tenant_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resource {id} not found"
            )

        return ResourceResponse(**result)
```

### Service Pattern

```python
class ResourceService:
    """Service for resource operations."""

    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[Dict]:
        """Get resource by ID with tenant isolation."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM resources
                WHERE id = %s AND tenant_id = %s
            """, (str(id), str(tenant_id)))
            return cur.fetchone()
```

### Test Pattern

```python
class TestResourceAPI:
    """Tests for Resource API endpoints."""

    def test_get_resource_not_found(self, client):
        """Test getting non-existent resource returns 404."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/resources/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()
```

---

## 9. Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Import errors in tests | Run from project root: `python -m pytest backend/tests -v` |
| Database column not found | Check `supabase/migrations/*.sql` for actual schema |
| Tests pass locally but fail in CI | Check Python version, dependencies |
| Context lost after compaction | Read STATE.md + ROADMAP.md |

### Debug Commands

```bash
# Check test imports
python -c "from backend.services.risk_engine import RiskEngine; print('OK')"

# Run single test with output
python -m pytest backend/tests/test_risk.py::TestVaR -v -s

# Check database schema
grep -r "CREATE TABLE" supabase/migrations/*.sql

# View recent git changes
git log --oneline -10
git diff HEAD~1
```

---

## 10. Subagent Strategy

Use Claude Code's built-in subagents strategically:

| Subagent | When to Use |
|----------|-------------|
| **Explore** | Finding files, understanding codebase patterns |
| **Plan** | Complex architecture decisions (Week 4 aggregation) |
| **Bash** | Git operations, running commands |
| **general-purpose** | Multi-step research tasks |

### When to Use Plan Agent

Before implementing complex features:
- Cross-PM netting algorithm
- Overlap detection logic
- Firm-level rollup
- Any feature touching 5+ files

---

*Template version: 1.0*
*Based on RISKCORE development experience*
*Last updated: 2026-01-12*
