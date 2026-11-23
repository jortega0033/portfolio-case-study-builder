# Owner decisions

A dated record of the decisions the owner made for this repository, so the rules do not depend on anyone's memory of a conversation. Changing any entry needs the owner. An agent that finds a decision blocking a ticket stops and says so.

| # | Date | Decision | Implemented in |
|---|---|---|---|
| 1 | 2026-11-22 | The instructions, tooling and playbook live on the default branch (`main`). | The `.claude/` tree, `CLAUDE.md`, `.github/` |
| 2 | 2026-11-22 | Persona agents run automatically during ticket work and carry instructions tailored to this project. | `.claude/agents/` ("In this repository" sections and "Use proactively" descriptions), [`.claude/skills/implement-ticket/SKILL.md`](../.claude/skills/implement-ticket/SKILL.md) |
| 3 | 2026-11-22 | Every open ticket is about app implementation; tooling is installed, not ticketed. | Epic #1 children; this tooling set |
| 4 | 2026-11-22 | Agents may take a ticket up to a ready pull request. Only the owner merges and releases. | [`CLAUDE.md`](../CLAUDE.md) "Git workflow" and "Delivery workflow", [`.claude/skills/next-ticket/SKILL.md`](../.claude/skills/next-ticket/SKILL.md), [`RELEASING.md`](RELEASING.md), `.github/CODEOWNERS` |
| 5 | 2026-11-22 | No scheduler. Ticket work starts only on the owner's go signal (`/next-ticket`), because the repository is used to train AI models. | [`.claude/skills/next-ticket/SKILL.md`](../.claude/skills/next-ticket/SKILL.md) (`disable-model-invocation: true`), [`LOOP.md`](../LOOP.md) |
| 6 | 2026-11-22 | A review gate hook blocks opening or readying a pull request until the gate roles have run after the last code edit. | [`.claude/hooks/role_gate.py`](../.claude/hooks/role_gate.py), [`.claude/settings.json`](../.claude/settings.json) |
| 7 | 2026-11-22 | Loop Engineering stays at L1, report-only and unscheduled. | [`LOOP.md`](../LOOP.md), [`loop-constraints.md`](../loop-constraints.md) |
| 8 | 2026-11-22 | Continuous integration runs on Linux and Windows; the default branch requires a pull request and green checks. | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml); branch protection is set on GitHub after the merge |
| 9 | 2026-11-22 | Permission rules: documented commands are allowed; force pushes, pushes to the default branch, merges, releases and reads of secrets are denied; edits to CI, agent configuration and Loop files ask first. | [`.claude/settings.json`](../.claude/settings.json) |
| 10 | 2026-11-22 | Open decisions on tickets are settled with the ticket's stated default (list below). | Epic [#1](https://github.com/jortega0033/portfolio-case-study-builder/issues/1) and the issues named below |
| 11 | 2026-11-22 | Rust is verified in CI only. Not applicable here: this repository has no Rust. | None |
| 12 | 2026-11-22 | The ten UI rules in `docs/ui-quality.md` are binding, and the `ui-ux-pro-max` and `unslop` skills are installed in the repository and used for UI work and for copy. | [`ui-quality.md`](ui-quality.md), `.claude/skills/ui-ux-pro-max/`, `.claude/skills/unslop/` |
| 13 | 2026-11-23 | Visual system: Pipenzo Flow look tokens ([`design-tokens.md`](design-tokens.md)). SDLC kit version: jortega0033/sdlc-kit v1.0.0. | [`design-tokens.md`](design-tokens.md), `case_study_builder/static/tokens.css`, `case_study_builder/static/app.css` |
| 14 | 2026-11-23 | Token rules, five parts. D1, current selection: the yellow accent is used for the primary action, the current-step marker and the current selection (UI rule 8). Decided by the owner on 2026-11-23. How (recommended by the orchestrator, adopted under the owner's delegation of the same day): a selection uses a solid --primary fill with --on-primary text (not only a yellow border, which has about 1.5:1 against white on light), plus a second sign that is not colour (weight, icon or text) and the existing aria attribute. Never a tint with a same-hue border and never a thick one-sided border. D2, focus ring: --focus is a focus indicator, exempt from the accent limit, including where it is yellow in dark. A ticket that says the focus style stays unchanged means the rule on main after the token pull request. Recommended by the orchestrator, adopted under the owner's delegation of 2026-11-23. D3, themes: contrast and no-colour-alone checks cover both the light and the dark block of tokens.css. Recommended by the orchestrator, adopted under the owner's delegation of 2026-11-23. D4, linking: a ticket that creates a page or its static allowlist links tokens.css before any other stylesheet and serves it (allowlist and its test). Recommended by the orchestrator, adopted under the owner's delegation of 2026-11-23. D5, release-dependency-planner: while a plan is open only one yellow primary button shows; "New plan" (#new-plan) becomes neutral, in ticket #11. Recommended by the orchestrator, adopted under the owner's delegation of 2026-11-23. | [`design-tokens.md`](design-tokens.md) "Rules" |

## Entry 10: open decisions settled by the ticket default (2026-11-22)

| Issue | Decision | Default applied |
|---|---|---|
| #1, #4, #11 | Page box | US Letter with 0.75 inch margins (672 by 912 CSS pixels); the 720 by 960 of the PRD fixtures stays a test input |
| #2 | `body` on write after schema 2 | Rejected; a section carries `blocks` |
| #2 | Migration of a version 1 body | Split at blank lines into paragraph blocks |
| #2 | Revision history retention | Newest 200 snapshots per project are kept |
| #10 | Where JavaScript and layout tests run | Headless Chrome started from Python, not Node |
| #10 | Module convention for new browser code | ES modules, each added to `STATIC_FILES` |
| #7 | Release gate host | The available host (Windows 11 with installed Chrome); the PRD platform assumptions are updated to match |
| #11 | Figure scale diagnostic | Counts the final scale, whether column width or page height caused it |
| #1 | Callout blocks | Not part of this epic |
| #10 | Fallback DevTools Protocol client if the page-box check fails (the ticket says to stop and ask the owner and states no default) | Conservative option: do not build it; stop and report. Flag in issue |
