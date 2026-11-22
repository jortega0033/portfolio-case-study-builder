# Loop Configuration — Minimal Triage (Claude Code)

Scaffolded with Loop Engineering (`@cobusgreyling/loop@0.2.0`, MIT, https://github.com/cobusgreyling/loop-engineering) using `init . --pattern daily-triage --tool claude`. The generated files were then adapted to this repository: project name, real test command, manual start instead of a schedule, and tighter constraints.

## Active Loops

| Pattern | Cadence | Status | Command |
|---------|---------|--------|---------|
| Daily Triage (`daily-triage`) | Manual, at most once a day. No scheduler. | L1 report-only | See "Next manual triage run" |

Nothing runs on its own. The generated starter suggested `/loop 1d $loop-triage`; that schedule is deliberately not used.

## Next manual triage run

A run rewrites two tracked files, `STATE.md` and `loop-run-log.md`, and leaves them modified in the working tree. So that this never lands on `main` or in a feature branch by accident, the person who starts the run prepares a branch first (the loop itself creates no branch and no commit):

```text
git fetch origin
git switch -C loop/triage origin/main
```

Start only from a clean working tree. Never run the loop on `main` or on a `feature/...` branch. After the run, read `STATE.md`, then either keep the report (commit only `STATE.md` and `loop-run-log.md` on `loop/triage` and open a pull request, as [`CLAUDE.md`](CLAUDE.md) describes) or drop it with `git restore STATE.md loop-run-log.md`. Both steps are done by a person.

From the repository root, on that branch, in an interactive Claude Code session, paste:

```text
Run the loop-constraints skill, then the loop-budget skill, then the loop-triage skill once, in report-only mode.
Inputs: `gh issue list --state open`, `gh pr list --state open`, `git log --since="48 hours ago" origin/main`,
and one run of `python -m unittest discover -s tests`. There is no CI to read.
Do not edit any file except STATE.md and loop-run-log.md. Do not commit, push, comment, label or open anything.
Update STATE.md and append one entry to loop-run-log.md.
```

## Human Gates

- The loop stays at L1 until the owner decides otherwise. No automated source fixes, no auto-merge, no scheduled runs.
- The binding rules are in [`loop-constraints.md`](loop-constraints.md). Budget and the kill switch are in [`loop-budget.md`](loop-budget.md).
- Every change to the product goes through an issue, a branch and a reviewed pull request as described in [`CLAUDE.md`](CLAUDE.md).

## Worktrees

- Not used at L1; a report-only run changes no source files.
- If the owner later moves to L2: one worktree per fix attempt, discarded after a `loop-verifier` REJECT.

## Connectors (MCP)

- None needed. The run uses the `gh` CLI and local `git` read commands.

## Budget

- Max sub-agent spawns per run: 0 (L1)
- Review `STATE.md` after each run

## Files

| File | Purpose |
|---|---|
| `STATE.md` | What the last run found. Rewritten by each run. |
| `loop-run-log.md` | One JSON entry per run. |
| `loop-budget.md` | Daily caps and the kill switch. |
| `loop-constraints.md` | Binding rules, read first on every run. |
| `.claude/skills/loop-triage/`, `loop-budget/`, `loop-constraints/` | The three skills a run uses, as generated, with one change: the `loop-constraints` skill stops when `loop-constraints.md` is missing (the generated text fell back to a `docs/safety.md` that this repository does not have). |
| `.claude/agents/loop-verifier.md` | Checker for a later L2 setup. Not used at L1. Limited to `Read, Grep, Glob`, like the other reviewer roles, so nothing in the L1 setup can run commands or edit. Its instructions tell it to run the tests itself; without `Bash` it answers `ESCALATE_HUMAN` instead. Moving to L2 means the owner adds `Bash` back to its `tools:` line in the same change that updates `loop-constraints.md` and this file. |

## What the generator produced and what was changed

`init` wrote `AGENTS.md`, `LOOP.md`, `STATE.md`, `loop-budget.md`, `loop-constraints.md`, `loop-run-log.md`, `.claude/agents/loop-verifier.md` and three skills under `.claude/skills/`. For this pattern it wrote no `.grok/` or `.codex/` directory and no `.github/` workflow, so there was nothing scheduled to remove.

- `AGENTS.md`: the generated test commands were `npm test` and `npm run lint`. This repository has no npm; they were replaced with the real command.
- `LOOP.md`: rewritten for a manual run. The generated links pointed at `../../patterns/` and `docs/safety.md`, which do not exist here.
- `loop-budget.md`, `loop-run-log.md`, `STATE.md`: project name filled in; the L2 columns and the `fix-proposed` outcome were removed.
- `loop-constraints.md`: rewritten for L1 (no commits, no pushes, no sub-agents, no scheduler, private data directories off limits).
- `loop-verifier.md`: `tools: Read, Grep, Glob` added.
- `loop-constraints` skill: stops instead of falling back to missing default rules.
- `loop-triage` and `loop-budget` skills: unchanged. They mention CI, Linear and Slack; this repository has none of them, and the prompt above names the real inputs.

## Recorded health check

Run on 2026-11-22 from the repository root, after the adaptations above and before the files were committed:

| Command | Result |
|---|---|
| `npx --yes @cobusgreyling/loop@0.2.0 doctor .` | exit 0, `Status: HEALTHY`, `Ready: 100/100 L2`, `state=STATE.md LOOP.md=yes budget=yes run-log=yes gate=no` |
| `npx --yes @cobusgreyling/loop@0.2.0 status .` | exit 0, `Pattern: daily-triage`, `Ready: 100/100 L2`, `State: STATE.md · never`, `constraints=yes`, no recent runs |

Run again on 2026-11-22 after the files were committed:

| Command | Result |
|---|---|
| `npx --yes @cobusgreyling/loop@0.2.0 doctor .` | exit 0, `Status: HEALTHY`, `Ready: 100/100 L3`, `state=STATE.md LOOP.md=yes budget=yes run-log=yes gate=no` |
| `npx --yes @cobusgreyling/loop@0.2.0 status .` | exit 0, `Pattern: daily-triage`, `Ready: 100/100 L3`, `State: STATE.md · never`, `constraints=yes`, no recent runs |

The label moved from L2 to L3 between the two runs although no loop run took place; the only change was that the files were committed. The likely reason, taken from the same observation in a sibling repository and not checked in the tool's source here, is that the tool counts a recent commit touching `STATE.md` or `loop-run-log.md` as loop activity.

"Ready: 100/100 L2" or "L3" is the tool's score for which files exist and how recently they changed. It is not the operating level. The operating level is L1 report-only. Doctor's suggested next actions (a `docs/safety.md`, issue and pull request templates, workflows, a pattern registry) were not followed: this repository has no CI, and the denylist lives in `loop-constraints.md`. `gate=no` means no CI gate workflow exists, which is intended.

## Links

- Pattern: [daily-triage](https://github.com/cobusgreyling/loop-engineering/blob/959fad23efa52456d3b478bd78eca1b1b4d9e88a/patterns/daily-triage.md)
- Checklist: [loop-design-checklist](https://github.com/cobusgreyling/loop-engineering/blob/959fad23efa52456d3b478bd78eca1b1b4d9e88a/docs/loop-design-checklist.md)
