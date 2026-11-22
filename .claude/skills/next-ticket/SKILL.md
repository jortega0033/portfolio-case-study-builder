---
name: next-ticket
description: Owner-started driver that takes one ticket of epic #1 from the queue to a ready pull request. Starting it is the owner's go signal. Never merges.
argument-hint: "[issue number]"
disable-model-invocation: true
---

# Next ticket

Only the owner starts this skill (`/next-ticket` or `/next-ticket <issue number>`). Starting it is the go signal: this repository is used to train AI models, so no ticket work runs without it. One ticket per run. This skill never merges, never closes an issue and never starts another run.

The epic is [issue #1](https://github.com/jortega0033/portfolio-case-study-builder/issues/1). Its body lists the child issues in dependency order. `CLAUDE.md` holds the commands, boundaries, Git workflow and evidence rules; the playbook is [`implement-ticket`](../implement-ticket/SKILL.md).

## Labels

`status:ready`, `status:blocked`, `status:in-progress`, `needs-decision`.

## Steps

1. **Refresh the queue.** `gh issue list --state open --limit 100` with labels, and the epic body for the dependency order. A `status:blocked` ticket whose blockers are all closed becomes `status:ready` (`gh issue edit <n> --add-label status:ready --remove-label status:blocked`).
2. **Pick.** If an issue number was given, use it, but stop and say so if it is `status:in-progress`, `needs-decision` or has an open blocker. Otherwise take the first `status:ready` ticket in the epic's dependency order that is not `status:in-progress` and not `needs-decision`. If none qualifies, report that and stop.
3. **Claim.** `gh issue edit <n> --add-label status:in-progress`.
4. **Branch in a fresh worktree**, as the Git workflow in `CLAUDE.md` says: `git fetch origin`, then `git worktree add ../portfolio-case-study-builder-<n> -b feature/<n>-<short-slug> origin/main`. Work only inside that worktree. Never work on `main`.
5. **Run the `implement-ticket` playbook** for the ticket, start to finish, including both gates, the `docs/ui-quality.md` check and the `unslop` pass.
6. **Open the pull request** only after local checks passed and both gates ran on the full diff. Open it as a draft with the template in `.github/pull_request_template.md`. Push only the feature branch.
7. **Wait for CI** on the draft. `gh pr checks <pr>` until every job has finished. If a job fails, fix it, re-run the local checks and both gates, and push again. A failure that is the known intermittent Windows test (issue #9) is reported, not worked around.
8. **When CI is green on every job** (both gates already ran before step 6), mark the pull request ready (`gh pr ready`) and comment on the issue with the pull request link, the CI run link, the evidence summary and the roles run. The review gate hook blocks `gh pr create` and `gh pr ready` until the gate roles ran after the last code edit.
9. **Stop.** Leave `status:in-progress` in place. The owner reviews and merges. If you hit a blocker or an open owner decision with no stated default, stop, comment on the issue, add `needs-decision` and say so.
