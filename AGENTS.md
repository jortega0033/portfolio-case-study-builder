# AGENTS.md

The working rules for any coding agent in this repository are in [`CLAUDE.md`](CLAUDE.md). This file repeats only the commands and the loop rules, and points to the ticket workflow, so that tools which read `AGENTS.md` find them.

## Ticket workflow

To implement a GitHub issue, follow the playbook [`.claude/skills/implement-ticket/SKILL.md`](.claude/skills/implement-ticket/SKILL.md) and the section "Project agents and ticket workflow" in `CLAUDE.md`. The roles are in `.claude/agents/`; each file starts with a section "In this repository". Pick leaf tickets only, never a container (`tracking`, `epic` or open sub-issues). A tool that cannot delegate to them uses that section as the checklist for the step and says so in the pull request.

## Test commands

```text
python -m unittest discover -s tests -v
```

There is no lint command, no build step and no package manager. Python 3.12 or newer, standard library only. See `CLAUDE.md` for the run command and for the checks that are planned but do not exist yet.

## Loop conventions

- The loop is at L1: report-only, started by hand, no scheduler, no automated fixes, no auto-merge.
- See [`LOOP.md`](LOOP.md) for the manual triage command and the human gates.
