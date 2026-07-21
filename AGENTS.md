# AGENTS.md

## 1. Purpose

This file defines the mandatory rules for all human contributors and AI coding agents working on the **Chip Buddy MVP**.

The project goal is to build a four-day MVP that compares Samsung Electronics and SK hynix using:

- ESG management risk
- Historical downside risk
- Historical CVaR
- Portfolio weight optimization
- Historical event analysis
- A mobile-first dashboard

All agents must follow this document before creating, modifying, or deleting project files.

---

## 2. Project Scope

### In Scope

- Samsung Electronics and SK hynix only
- ESG indicator and event datasets
- Historical CVaR-based downside risk
- 20% to 80% portfolio weight constraints
- 1% grid-search optimization
- Current versus recommended weight comparison
- Historical event return analysis
- Sample, validated, and fallback data states
- FastAPI backend
- Mobile-first frontend
- Google Stitch UI drafts
- Google Antigravity-assisted implementation

### Out of Scope

- Stock price prediction
- Expected return prediction
- Automated trading
- Additional stocks
- Real-time investment recommendations
- Automatic scoring of unverified news
- Advanced machine learning
- Black-Litterman optimization
- PCA-based ESG scoring
- Multi-asset portfolio optimization
- Authentication and user accounts
- Production-grade financial advisory services

Agents must not add out-of-scope features unless the team lead explicitly updates `ROADMAP.md`.

---

## 3. Mandatory Project Files

The following files must exist in the repository root:

- `README.md`
- `AGENTS.md`
- `ROADMAP.md`
- `PROGRESS.md`
- `.gitignore`
- `.env.example`

If `ROADMAP.md` or `PROGRESS.md` does not exist, the agent must create it before implementation work begins.

The agent must not begin feature implementation until both files have been read.

---

## 4. Source of Truth Priority

When instructions conflict, use the following order:

1. Explicit instructions from the team lead
2. `AGENTS.md`
3. `ROADMAP.md`
4. Data, API, and UI schema files
5. `PROGRESS.md`
6. PRD and project documentation
7. Existing implementation
8. Agent assumptions

Agents must not silently resolve conflicts.

When a conflict is found:

1. Stop the affected task.
2. Record the conflict in `PROGRESS.md`.
3. Mark the task as `blocked`.
4. Notify the task owner or team lead.

---

## 5. Team Roles

### Data A

Responsible for:

- ESG indicator definitions
- Official report collection
- ESG value verification
- Event candidate normalization and automated verification rules
- Official source confirmation
- `esg_indicators.csv`
- `events.csv`
- `sources.csv`

Data A does not:

- Calculate CVaR
- Optimize portfolio weights
- Modify model formulas
- Implement frontend or backend business logic

### Data B

Responsible for:

- Price validation
- Daily return calculation
- Historical CVaR
- Maximum drawdown
- Downside deviation
- ESG risk aggregation
- Turnover penalty
- 1% grid-search optimization
- Historical event return analysis

Data B does not:

- Change automated ESG source-verification rules independently
- Select model-eligible events without official-source verification
- Implement frontend layouts
- Change API contracts independently

### Backend

Responsible for:

- FastAPI project structure
- Data loaders
- Data validation
- API schemas
- Repositories and services
- Model function integration
- Error and fallback handling
- OpenAPI documentation

Backend does not:

- Change ESG methodology
- Bypass event verification rules
- Modify model weights without agreement
- Present sample output as validated output

### Frontend

Responsible for:

- Google Stitch UI drafts
- Frontend pages and components
- Mobile user flow
- API integration
- Loading, error, empty, sample, and fallback states
- Accessibility and responsive layout

Frontend does not:

- Calculate ESG scores
- Modify optimization results
- Select events
- Hard-code final recommendation values

---

## 6. `ROADMAP.md` Rules

`ROADMAP.md` defines the approved four-day project plan.

### Required Sections

`ROADMAP.md` must include:

- Project goal
- MVP completion criteria
- Team roles
- Day 1 through Day 4 tasks
- Integration checkpoints
- Must / Should / Drop First priorities
- Current blockers
- Final demo flow

### Read Rules

Before starting any task, every agent must:

1. Read `ROADMAP.md`.
2. Identify the current project phase.
3. Identify the task ID.
4. Confirm the task owner.
5. Confirm dependencies.
6. Confirm required outputs.
7. Confirm completion criteria.

### Update Rules

Agents may update only:

- The checkbox of a task they own
- The status of a task they performed
- A blocker directly related to their task
- A verified completion note

Only the team lead may change:

- Project goal
- MVP scope
- Priorities
- Deadlines
- Role ownership
- Integration checkpoints
- Drop First items

Agents must not:

- Rewrite the entire roadmap
- Delete completed task history
- Mark a task complete without validation
- Add new features without team lead approval
- Change another member's task status

### Completion Rules

A roadmap task may be marked complete only when:

- Required output files exist
- Required tests or validation commands were run
- Results meet the documented completion criteria
- Sample output is clearly labeled as sample
- No unresolved blocking error remains
- `PROGRESS.md` has been updated

---

## 7. `PROGRESS.md` Rules

The root `PROGRESS.md` records the project-wide execution summary and may be modified only by the team lead.

Detailed role work logs must be recorded in:

```text
progress/DATA-A.md
progress/DATA-B.md
progress/BACKEND.md
progress/FRONTEND.md
progress/INTEGRATION.md
```

### Required Sections

`PROGRESS.md` must include:

- Current project phase
- Overall status
- Last updated timestamp
- Current integration checkpoint
- Task status table
- Active blockers
- Work log
- Next integration actions

### Allowed Status Values

Only these values may be used:

- `todo`
- `in_progress`
- `blocked`
- `review`
- `done`

### Before Starting Work

The agent must:

1. Pull or inspect the latest branch state.
2. Read `ROADMAP.md`.
3. Read the root `PROGRESS.md`.
4. Read its own role progress file.
5. Select one incomplete task assigned to its role.
6. Confirm no other agent owns the same active task.
7. Mark the task as `in_progress` in its own role progress file.
8. Add a work log entry to its own role progress file.

### During Work

The agent must record:

- Important assumptions
- Schema changes
- Blockers
- External dependencies
- Unexpected errors
- Scope risks

The agent must not wait silently when blocked.

A blocked task must be recorded as:

```text
status: blocked
reason: specific blocking issue
required_action: action needed to continue
owner: responsible person
```

### After Work

The agent must update only its own role progress file with:

- Date and time
- Role
- Task ID
- Status
- Work completed
- Files created
- Files modified
- Validation commands
- Validation results
- Remaining issues
- Blockers
- Next recommended task

### Completion Restrictions

The agent must not mark a task `done` when:

- Tests were not run
- Required output files do not exist
- Required schema checks failed
- Sample data is shown as validated data
- Unverified events are included in scoring
- Data scope is ambiguous
- Hard-coded demo values remain in production paths
- Errors are hidden or ignored
- Another team member's approval is required

Use `review` when work is implemented but requires another role's approval.

---

## 8. Concurrent Agent Rules

Multiple team members may use Google Antigravity at the same time.

To reduce Git conflicts, progress tracking is split by role.

### Required Progress Files

```text
PROGRESS.md
progress/
├── DATA-A.md
├── DATA-B.md
├── BACKEND.md
├── FRONTEND.md
└── INTEGRATION.md
```

Ownership rules:

- `progress/DATA-A.md`: Data A only
- `progress/DATA-B.md`: Data B only
- `progress/BACKEND.md`: Backend only
- `progress/FRONTEND.md`: Frontend only
- `progress/INTEGRATION.md`: Team lead or integration owner only
- Root `PROGRESS.md`: Team lead only

### Team Member Rules

Each team member or agent must:

1. Read the latest root `PROGRESS.md`.
2. Read its own role progress file.
3. Update only its own role progress file.
4. Append work logs instead of replacing previous logs.
5. Record task status, outputs, validation, blockers, and next work.
6. Never edit another role's progress file.
7. Never directly edit the root `PROGRESS.md`.

### Team Lead Rules

The team lead must update the root `PROGRESS.md` only:

- after a pull request is merged
- after an integration checkpoint
- when a project-wide blocker appears
- at the end of a work session or project day
- when `ROADMAP.md` priorities or ownership change

The root `PROGRESS.md` must remain a concise project summary. Detailed logs belong in the role-specific files.

### Git and Merge Rules

- Each task must have a unique task ID.
- Each active task must have one owner.
- Before work, fetch or pull the latest branch state.
- Before committing, re-check the latest target branch.
- Do not rewrite the full contents of shared files.
- Shared schema changes require review from all affected roles.
- Project-wide `ROADMAP.md` changes require team lead approval.
- Merge conflicts must not be resolved by deleting another member's work.
- If a conflict affects another role's progress log, stop and ask that role or the team lead to resolve it.

## 9. Data Rules

### Data States

Allowed data states:

- `sample`
- `validated`
- `fallback`

Every API response and UI result must identify the data state when relevant.

### Data Pipeline

Use this order:

```text
raw
→ candidate
→ automated schema and official-source verification
→ processed
→ API
→ UI
```

Models must not read directly from `data/raw/`.
Human review is not part of the runtime pipeline. Candidate records that fail automated verification remain non-scoring warnings or are rejected.

### Missing Values

- Do not replace missing values with zero.
- Do not replace missing values with peer averages.
- Use `unavailable`.
- Lower data confidence when needed.
- Show data shortage in the UI.
- `availability = unavailable` requires `raw_value = null`; zero is not a missing-value marker.
- Parser, source, or schema validation failures must remain rejected candidates and must not be converted into `availability = unavailable`.

### Samsung Scope

Use this priority:

1. Samsung Electronics DS or semiconductor data
2. Korean semiconductor site data
3. Samsung Electronics consolidated data

When consolidated data is used:

```text
scope_mismatch = true
```

### Event Status

Allowed event statuses:

- `reported`
- `confirmed`
- `resolved`

`sanctioned` is an enforcement outcome, not an event status. Store it in `enforcement_action`.

Only `confirmed` and `resolved` events that pass automated schema and official-source verification may affect model scores.

`rumor` records remain in raw collection only and must not be normalized into event data. `reported` events may be shown as warnings but must not affect ESG risk scores.

### Source Rules

Each validated ESG value must include:

- Company
- Indicator
- Raw value
- Unit
- Period
- Business scope
- Geography
- Source title
- Source page
- Source URL
- Data confidence

Each model-eligible event must include:

- Company
- Event category
- Event date
- Event date type
- Detection source type (`dart_disclosure` or `news`)
- Status
- Enforcement action
- Official confirmation
- Official source

---

## 10. Modeling Rules

The model must:

- Use Historical CVaR as the primary downside-risk metric
- Use deterministic calculations
- Use a 20% to 80% weight constraint
- Use 1% grid-search steps
- Ensure total recommended weights equal 100%
- Keep ESG risk separate from external semiconductor business risk
- Keep model parameters in configuration files
- Generate rule-based explanations
- Record the data period and assumptions

The model must not:

- Predict future stock prices
- Claim expected return
- Use unverified events
- Hide missing data
- Hard-code company risk scores in model code
- Introduce advanced ML without roadmap approval

Required checks:

- Same input produces same output
- Weight sum equals 1.0
- Each weight remains within constraints
- CVaR calculation handles insufficient data
- Removing ESG penalty produces an explainable change
- Sensitivity checks do not produce unexplained instability

---

## 11. Backend Rules

The backend must:

- Expose `GET /health`
- Validate all input schemas
- Return clear errors
- Support sample-data mode
- Support validated-data mode
- Support fallback mode
- Keep API response examples synchronized
- Use automatically validated processed data for model calculations
- Filter unverified events
- Preserve source metadata

The backend must not:

- Return sample results without a sample label
- Silently convert malformed values
- Ignore missing required columns
- Overwrite the last valid processed snapshot with invalid refresh output
- Put API keys in source code

External refresh must write to raw or candidate storage first. Automated verification may atomically publish a new processed snapshot only after schema, official-source, status, and deduplication checks pass.

---

## 12. Frontend and Stitch Rules

Google Stitch output is a draft, not final production code.

Stitch output must be stored first under:

```text
stitch-export/raw/
```

Before moving Stitch code into the frontend:

- Remove hard-coded recommendation values
- Replace fixed values with props, mock data, or API data
- Extract reusable components
- Check Korean text wrapping
- Check a 390px mobile viewport
- Add loading state
- Add error state
- Add empty state
- Add sample-data state
- Add fallback state
- Add source links
- Add investment disclaimer
- Verify navigation
- Verify accessibility

Do not overwrite the frontend project with an entire Stitch export.

The UI must not rely only on color.

Risk displays must include text labels such as:

- Low
- Medium
- High
- Data unavailable
- Sample data

---

## 13. Antigravity Task Rules

Every Antigravity task prompt should define:

- Task ID
- Goal
- Allowed files
- Files that must not be modified
- Inputs
- Expected outputs
- Validation commands
- Completion criteria

Example:

```text
Task ID: DB-03
Goal: Implement Historical CVaR 95%
Allowed files:
- src/modeling/downside.py
- tests/unit/test_downside.py

Do not modify:
- data/processed/
- src/frontend/
- schemas/

Validation:
- pytest tests/unit/test_downside.py
```

Antigravity agents must not:

- Use destructive shell commands
- Run `git push --force`
- Modify `.env`
- Print secrets
- Delete processed data
- Rewrite unrelated files
- Change project scope
- Mark unverified work as complete
- Present mock output as real analysis

---

## 14. Safe File Operation Rules

Agents must not perform:

- `rm -rf`
- Project-root deletion
- User-home deletion
- Force push
- Secret exposure
- Bulk overwrite of processed data
- Bulk overwrite of Stitch-integrated frontend code
- Deletion of prior progress logs

Before deleting or replacing a file:

1. Confirm it is generated or temporary.
2. Confirm it is not a source-of-truth file.
3. Record the action in `PROGRESS.md`.
4. Preserve recoverability through Git.

---

## 15. Schema Change Rules

A schema change includes:

- CSV column changes
- JSON field changes
- Enum changes
- API request changes
- API response changes
- Model function signature changes

Before changing a schema:

1. Record the proposal in `PROGRESS.md`.
2. Identify affected roles.
3. Update schema files first.
4. Update sample data.
5. Update tests.
6. Update producers.
7. Update consumers.
8. Run contract tests.
9. Request review.

No agent may independently change shared schemas without recording the impact.

---

## 16. Validation Requirements

Before marking any task complete, run the relevant checks.

### Data

- Required columns
- Data types
- Duplicate rows
- Allowed enum values
- Date formats
- Scope values
- Source presence
- Automated verification result

### Modeling

- Unit tests
- Deterministic output
- Weight constraints
- Weight sum
- Missing-data handling
- Event-status filtering

### Backend

- API unit tests
- Schema validation
- OpenAPI examples
- Error handling
- Sample, validated, and fallback states

### Frontend

- Lint
- Build
- Mobile viewport
- Navigation
- Loading and error states
- No hard-coded final values
- API field compatibility

### Integration

- Portfolio input to result flow
- Model result through API
- API result through UI
- Portfolio edit and recalculation
- Sample fallback flow
- Source and disclaimer display

---

## 17. Required End-of-Task Procedure

At the end of every task, the agent must:

1. Run required validation.
2. Update the task entry in `PROGRESS.md`.
3. Update the matching task status in `ROADMAP.md`.
4. Record created and modified files.
5. Record validation commands and results.
6. Record blockers and remaining work.
7. Recommend the next task.
8. Provide a concise summary to the task owner.

A task is not complete until documentation and progress tracking are updated.

---

## 18. Recommended `PROGRESS.md` Structure

```markdown
# Project Progress

## Current Status

- Project phase:
- Overall status:
- Last updated:
- Current integration checkpoint:

## Task Status

| Task ID | Role | Task | Status | Output | Blocker |
|---|---|---|---|---|---|

## Active Blockers

| Blocker ID | Related Task | Description | Owner | Required Action |
|---|---|---|---|---|

## Work Log

### YYYY-MM-DD HH:MM — TASK-ID

- Role:
- Owner:
- Status:
- Completed:
- Created files:
- Modified files:
- Validation commands:
- Validation results:
- Remaining:
- Blockers:
- Next task:

## Next Integration Actions

1.
2.
3.
```

---

## 19. Recommended `ROADMAP.md` Structure

```markdown
# Project Roadmap

## Project Goal

## MVP Completion Criteria

## Team Roles

## Day 1

## Day 2

## Day 3

## Day 4

## Integration Checkpoints

## Priority

### Must

### Should

### Drop First

## Current Blockers

## Final Demo Flow
```

---

## 20. Final Principle

The team must prioritize:

1. Small but verified data
2. Reproducible calculations
3. Stable interfaces
4. End-to-end demo completion
5. Clear limitations

Perfect data, advanced models, and visual polish are lower priority than a complete and explainable MVP.
