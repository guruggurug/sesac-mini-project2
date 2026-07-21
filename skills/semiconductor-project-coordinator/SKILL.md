---
name: semiconductor-project-coordinator
description: Coordinate the four-day, four-person Chip Buddy project through its connected GitHub repository or uploaded repository files. Use when the user asks to inspect project status, select the next task for Data A, Data B, Backend, Frontend, or Integration, review ROADMAP.md or PROGRESS.md, update role progress files, check file ownership, prepare Git branches and commits, review schemas and sample data, reduce merge conflicts, or determine whether parallel work can start.
---

# Chip Buddy Coordinator

## Goal

Coordinate the repository without overwriting another role's work. Base every recommendation on the latest repository state and preserve the project's four-day MVP scope.

## Repository Sources

Use sources in this order:

1. Use the connected GitHub repository when a GitHub connector is available.
2. Otherwise inspect repository files uploaded in the conversation.
3. Otherwise inspect a local repository path supplied by the user.
4. If none are accessible, state which files are required and provide a non-destructive template only.

Never claim that a GitHub file or branch was changed unless the connected tool confirms the change.

## Required Context

Read these files before coordinating work when they exist:

```text
README.md
AGENTS.md
ROADMAP.md
PROGRESS.md
progress/DATA-A.md
progress/DATA-B.md
progress/BACKEND.md
progress/FRONTEND.md
progress/INTEGRATION.md
```

For data or API work, also inspect:

```text
schemas/data/
schemas/api/
data/sample/
```

Treat `AGENTS.md` as the repository operating policy. Treat `ROADMAP.md` as the task plan and root `PROGRESS.md` as the team-lead summary.

## Role Ownership

Apply these ownership rules unless the repository explicitly defines newer rules:

- Data A edits `progress/DATA-A.md` and Data A outputs.
- Data B edits `progress/DATA-B.md` and modeling outputs.
- Backend edits `progress/BACKEND.md` and backend outputs.
- Frontend edits `progress/FRONTEND.md` and frontend outputs.
- Team Lead or Integration edits `progress/INTEGRATION.md`.
- Only Team Lead edits root `PROGRESS.md` and project-wide `ROADMAP.md` status.

Do not instruct a role to edit another role's progress file.

## Coordination Workflow

### 1. Establish Current State

- Read the latest default branch state.
- Identify the current checkpoint and statuses: `todo`, `in_progress`, `blocked`, `review`, `done`.
- Check dependencies before recommending work.
- Identify active blockers and files currently owned by another role.

### 2. Select Work

Choose one task that:

- belongs to the requested role
- is not already owned by another active branch or assignee
- has satisfied dependencies
- contributes directly to the MVP
- can produce a verifiable repository output

If dependencies are incomplete, recommend the smallest useful preparatory task rather than pretending the main task is ready.

### 3. Define Execution

Return:

1. current state
2. selected task ID and purpose
3. files allowed to change
4. ordered implementation steps
5. completion conditions
6. validation commands or checks
7. suggested branch name
8. suggested commit message
9. progress entry to append

Keep instructions executable by a non-major beginner. Explain unfamiliar commands briefly.

### 4. Review Changes

When reviewing work:

- compare changed files with task ownership
- verify schema and sample consistency
- verify that required tests or validation were run
- identify scope creep beyond the four-day MVP
- flag destructive rewrites of shared files
- distinguish blockers from optional improvements

Use `references/review-checklists.md` for detailed checks.

### 5. Update Progress Safely

For a normal team member:

- update only the role-specific progress file
- append a dated work log
- include task ID, status, outputs, validation, blockers, and next action
- request Team Lead review for root status changes

For Team Lead:

- update root `PROGRESS.md` after merge, checkpoint review, blocker changes, or end-of-day review
- update `ROADMAP.md` only when ownership, priority, dependency, or completion status changes
- summarize rather than copying full role logs

## GitHub Workflow

Prefer one branch per task:

```text
feature/data-a-<topic>
feature/data-b-<topic>
feature/backend-<topic>
feature/frontend-<topic>
chore/integration-<topic>
```

Before work:

```bash
git switch main
git pull origin main
git switch -c <branch-name>
```

Before commit:

```bash
git status
git diff
git add <owned-files>
git commit -m "<type>: <task summary>"
git push -u origin <branch-name>
```

Do not recommend `git add .` when unrelated changes may exist. Do not use force push unless the user explicitly requests it and understands the impact.

## Parallel Start Gate

Treat initial parallel work as ready only when:

- COMMON-02 shared schemas are approved
- COMMON-03 sample data is approved
- role-specific progress files exist
- each active task has one owner
- each role can begin without waiting for another role's unfinished real output

The expected first parallel tasks are normally:

```text
DATA-A-01
DATA-B-01
BE-01
FE-01
```

Confirm against the latest `ROADMAP.md` before using them.

## Output Style

Use concise Korean by default for this project. Use exact file paths and task IDs. Separate confirmed repository facts from recommendations. Never report an unverified GitHub change as completed.
