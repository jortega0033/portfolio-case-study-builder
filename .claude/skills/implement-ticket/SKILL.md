---
name: implement-ticket
description: Playbook for implementing a GitHub issue in this repository from start to pull request, with the project subagents run at fixed steps. Use whenever asked to implement, start, continue or finish a ticket, an issue or an epic child, for example "implement #12" or "work on the next ticket".
argument-hint: "[issue number]"
---

# Implement a ticket

Use this playbook for every implementation ticket in this repository. `CLAUDE.md` holds the commands, the architecture boundaries, the Git workflow and the evidence rules; where this playbook and `CLAUDE.md` differ, `CLAUDE.md` wins.

The project subagents in `.claude/agents/` are part of the work. Delegate to them at the steps below without waiting to be asked. If a step names a role that is not installed, do that step yourself and say so in the pull request.

## Steps

1. **Read the ticket.** `gh issue view <number>` and the epic it belongs to. A ticket that is `tracking`, `epic` or has open sub-issues is a container: do not implement it and do not pick a sub-issue for it. Refuse it, list its open sub-issues (`gh api repos/jortega0033/portfolio-case-study-builder/issues/<n>/sub_issues`) and stop; the owner starts `/next-ticket`, which picks a leaf ticket with its own checks (not `status:in-progress`, not `needs-decision`, `status:ready`). Check that every prerequisite issue is closed and that no owner decision named in the ticket is still open. If the ticket is blocked, stop and say what blocks it.
2. **Read the rules.** `CLAUDE.md`, then the architecture notes it links to.
3. **UI tickets: start with design guidance.** If the ticket changes anything the user sees, run the `ui-ux-pro-max` skill first (`python .claude/skills/ui-ux-pro-max/scripts/search.py "<product type>" --design-system`) and read [`docs/ui-quality.md`](../../../docs/ui-quality.md).
4. **Orient and check the approach.** Delegate as the table "Before coding" says. Settle open design questions before writing code.
5. **Branch** as the Git workflow in `CLAUDE.md` says. Never work on the default branch.
6. **Implement** inside the ticket's stated scope. Do not change agent configuration (`.claude/agents`, `.claude/skills`, `.claude/hooks`, `.claude/settings.json`) in a ticket. Delegate the work to the implementing role that matches the files being changed (table "While coding"). Do not widen scope; note anything else you find as a follow-up.
7. **Test.** Add or change tests for every acceptance criterion and material edge case, then run the checks listed in `CLAUDE.md`. Record each command and its result. A criterion that needs a person ("by hand in a normal browser", "manual, recorded") is done as far as an agent can, with the evidence, and the rest is listed under "Owner checks" in the pull request; Reality Checker accepts that only when the ticket marks the step as manual.
8. **Specialist review.** Run every role in the table "After coding" whose trigger matches the change.
9. **UI check.** For a UI ticket, check every changed screen against [`docs/ui-quality.md`](../../../docs/ui-quality.md) and note the result.
10. **Writing pass.** Run the `unslop` skill over user-facing copy, documentation and the pull request text now, so the gates judge the final diff.
11. **Changelog.** Add one line for the ticket under Unreleased in `CHANGELOG.md`, before the gates.
12. **Review gate, always.** Write the diff (`git diff --stat origin/main...HEAD`, `git diff origin/main...HEAD`) and the recorded check outputs to `.claude/state/review/` in the worktree, name those files in the request, and run Code Reviewer on the full diff. Fix every material finding, re-run the checks, and have the reviewer look again until no material finding is left.
13. **Acceptance gate, always.** Run Reality Checker with the ticket's acceptance criteria and the recorded local evidence. It checks that the documented checks ran locally and passed and that CI is configured to run them; it does not judge a CI result, which does not exist yet. Do not open the pull request unless it passes.
14. **Hand off.** Capture the evidence `CLAUDE.md` asks for and open a draft pull request from `.github/pull_request_template.md` that names the issue (the pull request of a parent's last open sub-issue also says `Closes #<parent>`), only after local checks passed and both gates ran. Then bind the pull request to the session if the app offers it and end the turn with "Draft pull request #N is waiting for CI"; do not poll. When woken, read `gh pr checks <n>` once. If a job fails, fix it, re-run the local checks and both gates, and push. When every job is green, mark the pull request ready (`gh pr ready`) and comment on the issue with the CI run link. Green CI is checked by you, not by Reality Checker. The review gate hook blocks `gh pr create` and `gh pr ready` until the gate roles ran after the last code edit. Only the owner merges; never merge.

## Roles

### Before coding

| Role | Access | Delegate to it |
|---|---|---|
| Codebase Onboarding Engineer | read-only reviewer | At the start of a ticket in an unfamiliar area, to trace the relevant code paths before anything is changed |
| Software Architect | read-only reviewer | Before implementing a ticket that adds or changes a module boundary, data model, storage schema, public API or dependency, to check the approach against the architecture notes |

### While coding

| Role | Access | Delegate to it |
|---|---|---|
| Backend Architect | can edit | When a ticket changes server-side code, HTTP routes, validation, persistence or data migrations |
| Frontend Developer | can edit | When a ticket changes browser-side code such as pages, components, client state, styling or keyboard interaction |
| PDF Engine Architect | read-only reviewer | When a ticket touches pagination, print CSS or PDF output |
| Test Automation Engineer | can edit | When a ticket adds or changes tests, fixtures or a browser test harness, or when acceptance criteria need new automated checks |

### After coding

| Role | Access | Delegate to it |
|---|---|---|
| Accessibility Auditor | read-only reviewer | After a ticket changes user-facing UI, keyboard handling, focus order or markup |

### Gates that run on every ticket

| Role | Access | Delegate to it |
|---|---|---|
| Code Reviewer | read-only reviewer | After implementing or changing code for a ticket, before the work is called done and before a pull request is opened |
| Reality Checker | read-only reviewer | As the acceptance gate of every ticket, after Code Reviewer and before the draft pull request is opened, to check each acceptance criterion against evidence that was actually produced locally, before the pull request is opened |

## Rules

- The session or role that wrote a change does not count as its reviewer.
- Read-only reviewers cannot run commands. Give them the diff, the acceptance criteria and the recorded command output.
- Where a role's general advice (frameworks, dependencies, cloud services) conflicts with `CLAUDE.md`, `CLAUDE.md` wins.
- In the pull request description, add a section "Agent roles run" listing each role that ran, what it was asked and its verdict, and any step you did yourself because a role was missing.
