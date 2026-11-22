---
name: next-ticket
description: Owner-started driver that takes one ticket of epic #1 from the queue to a ready pull request. Starting it is the owner's go signal. Never merges.
argument-hint: "[issue number]"
disable-model-invocation: true
---

# Next ticket

Only the owner starts this skill (`/next-ticket` or `/next-ticket <issue number>`). Starting it is the go signal: this repository is used to train AI models, so no ticket work runs without it. One ticket per run. This skill never merges and never starts another run. The only issue it closes is a parent whose sub-issues are all closed (step 1).

The epic is [issue #1](https://github.com/jortega0033/portfolio-case-study-builder/issues/1). Its body lists the child issues in dependency order. `CLAUDE.md` holds the commands, boundaries, Git workflow and evidence rules; the playbook is [`implement-ticket`](../implement-ticket/SKILL.md).

## Labels

`status:ready`, `status:blocked`, `status:in-progress`, `needs-decision`, and `tracking` for a container ticket.

## Which ticket is work

Big tickets are split into sub-issues of 1 to 4 hours, one pull request each. A ticket labelled `tracking` or `epic`, or one with open sub-issues, is a container: this skill never picks it. List sub-issues with `gh api repos/jortega0033/portfolio-case-study-builder/issues/<n>/sub_issues`. Work is a **leaf** ticket: no open sub-issues and not `tracking`. Leaf order is the order of the parents in the epic's table, then the order of the sub-issues inside each parent.

## Steps

1. **Refresh the queue.** `gh issue list --state open --limit 100` with labels, the epic body for the order, and the sub-issues of every open container. A `status:blocked` ticket whose blockers are all closed becomes `status:ready` (`gh issue edit <n> --add-label status:ready --remove-label status:blocked`). A parent whose sub-issues are all closed is closed with a comment that names them (`gh issue close <n> --comment ...`).
2. **Pick.** If an issue number was given and it is a container, refuse it and list its open sub-issues; stop. Otherwise use it, but stop and say so if it is `status:in-progress`, `needs-decision` or has an open blocker. With no number, take the first `status:ready` leaf ticket in the order above that is not `status:in-progress` and not `needs-decision`. If none qualifies, report that and stop.
3. **Claim.** `gh issue edit <n> --add-label status:in-progress`.
4. **Branch in a fresh worktree**, as the Git workflow in `CLAUDE.md` says: `git fetch origin`, then `git worktree add ../portfolio-case-study-builder-<n> -b feature/<n>-<short-slug> origin/main`. Work only inside that worktree. Never work on `main`.
5. **Run the `implement-ticket` playbook** for the ticket, start to finish, including both gates, the `docs/ui-quality.md` check and the `unslop` pass. A step that needs a person ("by hand in a normal browser", "manual, recorded") is done as far as an agent can (a scripted or headless run, with the evidence); the rest goes under "Owner checks" in the pull request.
6. **Write the review files, then run the gates.** Code Reviewer and Reality Checker have no shell. After the local checks, write `git diff --stat origin/main...HEAD`, `git diff origin/main...HEAD` and the check outputs to `.claude/state/review/` in the worktree (ignored by Git), and name those files in each request.
7. **Open the pull request** only after local checks passed and both gates ran on the full diff. Open it as a draft with the template in `.github/pull_request_template.md`, and `git push` only the feature branch. The description says `Closes #<n>`; if this is the last open sub-issue of a parent, it also says `Closes #<parent>`, so the owner's merge closes both.
8. **Wait for CI without polling.** Bind the pull request to the session if the app offers it (the desktop app's pull request tools), then end the turn with the line "Draft pull request #N is waiting for CI". Do not loop, sleep or watch. When the session is woken (a CI event from the app, or the owner says "continue"), read `gh pr checks <pr>` once: green, go to step 9; red, fix it, re-run the local checks and both gates, push, and end the turn with the same line; still running, end the turn with the same line. A failure that is the known intermittent Windows test (issue #9) is reported, not worked around.
9. **When CI is green on every job** (both gates already ran before step 7), mark the pull request ready (`gh pr ready`) and comment on the issue with the pull request link, the CI run link, the evidence summary and the roles run. The review gate hook blocks `gh pr create` and `gh pr ready` until the gate roles ran after the last code edit.
10. **Stop.** Leave `status:in-progress` in place. The owner reviews and merges. If you hit a blocker or an open owner decision with no stated default, stop, comment on the issue, add `needs-decision` and say so.
