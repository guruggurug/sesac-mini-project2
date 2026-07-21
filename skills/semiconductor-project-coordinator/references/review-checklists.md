# Review Checklists

## Table of Contents

1. Repository and ownership
2. Progress update
3. Schema and sample data
4. Backend
5. Frontend
6. Modeling
7. Pull request

## 1. Repository and Ownership

- The task has one owner.
- Changed files belong to the task or are explicitly approved shared files.
- Another role's progress file was not edited.
- Root `PROGRESS.md` and `ROADMAP.md` were edited only by Team Lead.
- Generated, secret, and local environment files are not committed.

## 2. Progress Update

A role log includes:

- date
- task ID
- status
- changed outputs
- validation result
- blockers
- next action

Do not delete prior logs. Append a new entry.

## 3. Schema and Sample Data

- Required fields exist.
- Enum values match `data-enums.yaml`.
- CSV headers match the schema-required fields.
- Example request and response JSON validate against API schemas.
- Dates, company codes, units, and missing-value rules are unambiguous.
- Data A can collect the fields.
- Data B can calculate with the fields.
- Backend can validate and serve the fields.
- Frontend can render the fields.

## 4. Backend

- API contract matches schemas.
- Validation failures return understandable errors.
- Sample mode works without unfinished real data.
- Real-data and model integrations can replace mocks without changing the frontend contract.
- Contract tests cover request and response examples.

## 5. Frontend

- UI uses the approved API response shape.
- Loading, error, empty, and sample states exist.
- Core comparison and portfolio recommendation are visible.
- Mobile layout is usable.
- Stitch exports are reviewed before being treated as approved source.

## 6. Modeling

- Historical return and loss conventions are documented.
- VaR and CVaR confidence levels are explicit.
- Portfolio weights obey constraints.
- Optimization failure has a deterministic fallback.
- Sensitivity or sanity checks are recorded.
- Results are not presented as guaranteed investment outcomes.

## 7. Pull Request

- PR title includes the task ID or clear scope.
- Description lists outputs and validation.
- Shared-file changes have affected-role reviewers.
- No unrelated formatting rewrite is included.
- Merge conflict resolution preserves both contributors' valid work.
