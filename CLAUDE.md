# CLAUDE.md

Working rules for Claude Code and other coding agents in this repository. Human contributors can use it the same way.

Portfolio Case Study Builder is a small, private, offline editor for portfolio case studies: a Python standard-library HTTP server on loopback, a SQLite file, and a hand-written HTML, CSS and JavaScript page. The baseline (milestone M1) is implemented. Epic E1, "Print-ready case studies", is planned and not built.

## Sources of truth

Read these before changing anything. Do not copy their content into other files; link to them.

| Question | Where the answer is |
|---|---|
| What the product is, scope, milestones, API, invariants, fitting rules, acceptance check IDs (`CS-B*`, `CS-T*`, `CS-A*`, `CS-P*`, `CS-D*`, `CS-R*`, `CS-Q*`) | [`docs/PRD.md`](docs/PRD.md) |
| How the code is actually built, one traced workflow with line citations, what is implemented, planned or still unverified, and where the PRD and the code disagree | [`docs/architecture.md`](docs/architecture.md) |
| How to run and use the app, current limitations | [`README.md`](README.md) |
| What to build next | The open GitHub issues. The epic is [issue #1](https://github.com/jortega0033/portfolio-case-study-builder/issues/1); its body lists the child issues in dependency order with estimates. Order as planned on 2026-11-22: #9, #10 and #2 can start together; then #3 and #11; then #4, #5, #6 and #7 in series. [`docs/architecture.md`](docs/architecture.md) section 7 says which issue covers which finding. |
| Exact API behaviour | The tests in [`tests/`](tests/). They are the executable contract; the PRD summarises it. |

If the PRD and the code disagree, do not pick one silently. Check [`docs/architecture.md`](docs/architecture.md) section 5 first; if the disagreement is not listed there, add it and say so in the pull request.

## Setup, run, test

There is nothing to install. Python 3.12 or newer, standard library only. No `pip`, no `npm`, no build step, no lint command, no CI.

```text
python -m unittest discover -s tests -v
python -m case_study_builder --data-dir ./demo-data --port 8765
```

- The test command starts real servers on ephemeral loopback ports and takes about 20 seconds. Run it once per change, never in a watch loop.
- The run command serves <http://127.0.0.1:8765/>. `--port 0` picks a free port and prints `Serving on http://127.0.0.1:<port>/`. Stop it with Ctrl+C. Always stop a server you started.
- `./demo-data`, `data/`, `*.sqlite*` and `*.db` are ignored by Git. Never commit a database. A test that needs an old database must build it in a temporary directory (a binary fixture cannot be committed, because `.gitignore` excludes it).
- Set `PYTHONDONTWRITEBYTECODE=1` if you do not want `__pycache__` folders (they are ignored either way).
- On Linux use `python3` if `python` is missing.

Both commands were run on 2026-11-22 during repository preparation (Windows 11, Python 3.13.14). The suite has 38 tests. It printed `OK` in two of three runs; in one run `test_b07_content_type_and_length` raised `ConnectionAbortedError: [WinError 10053]`. That is a known intermittent defect of the baseline on Windows ([`docs/architecture.md`](docs/architecture.md) section 5, item 12), not something to work around: if it happens, rerun once and report both results; never skip or loosen the test. The server started, saved a case study and returned it unchanged after a restart. Details and the checks that were not run are in [`docs/architecture.md`](docs/architecture.md) section 4.

Checks that do not exist yet: there is no JavaScript unit test runner, no automated browser test and no print or PDF check. The browser flow in PRD section 10 is manual. Do not claim a browser check passed unless you ran it and kept the evidence.

## Hard constraints

These are product decisions from the PRD, not style preferences. A change that breaks one is wrong even if the tests pass.

1. **Offline.** No request to any host other than the app's own loopback address, at run time or in a test. No CDN, no web font, no analytics, no remote image. `tests/test_static.py` scans the static files for external URLs; keep every new static file inside that scan. At the baseline the scan lists three file names and the HTML-injection scan reads only `app.js`, so a new file is not covered until those tests walk the directory ([`docs/architecture.md`](docs/architecture.md) section 6, item 4). Do not add a served file before it is scanned.
2. **No dependencies.** Python standard library only. Native HTML, CSS and JavaScript only. Do not add `requirements.txt`, `pyproject.toml` dependencies, `package.json` or vendored libraries.
3. **Loopback only.** The server binds `127.0.0.1`. Every request must pass the Host check; every `POST` and `PUT` must carry a same-origin `Origin`. New write routes get the same checks.
4. **Text is never HTML.** The server stores and returns text verbatim. The client renders with `textContent` and `value` only. `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `eval`, inline `<script>`, inline `<style>` and `style=` attributes are banned (the Content-Security-Policy forbids them and `tests/test_static.py` checks for them).
5. **Static files are a whitelist.** `STATIC_FILES` in `case_study_builder/server.py` lists every path that is served. A new script, stylesheet or SVG must be added there explicitly. Do not serve a directory.
6. **Saves are atomic and revision-checked.** Invariants I1 to I5 in PRD section 6.1 must hold after every change to `storage.py`.
7. **Fictional content only.** Fixtures, examples and screenshots use invented names and numbers. Never use a real case study, a real person or anything from a local data directory.
8. **Artwork is original.** No third-party images, icons or fonts in the repository.

## Architecture boundaries

Details and citations are in [`docs/architecture.md`](docs/architecture.md). The short version:

| File | Owns | Must not |
|---|---|---|
| `case_study_builder/validation.py` | Payload rules and limits. Pure functions. | Do I/O, import `storage` or `server`. |
| `case_study_builder/storage.py` | SQLite schema, migrations, transactions. One connection per operation. | Know about HTTP, JSON envelopes or status codes. |
| `case_study_builder/server.py` | Routing, Host and Origin checks, body limits, response headers, error mapping, the static whitelist. | Contain SQL or validation rules. |
| `case_study_builder/__main__.py` | Command-line arguments, exit codes, signal handling. | Contain request handling. |
| `case_study_builder/static/` | The browser client. The server and SQLite are authoritative; the client holds a working copy plus the revision it loaded. | Trust its own state over a server response; build HTML from text. |
| `tests/` | The executable contract. `tests/helpers.py` starts a real server per test. | Mock the server or the database. |

Keep new browser logic that has no need for the DOM (for example the pagination rules of PRD section 6.2) in its own file as pure functions, so that it can be tested without a layout engine.

## Git workflow

- `main` is the default branch. It has no branch protection on GitHub (checked 2026-11-22), so the rule is by agreement: never commit to `main` and never push to it directly.
- One issue, one branch, one pull request. Branch from the tip of `origin/main`: `git fetch origin`, then `git switch -c feature/<issue-number>-<short-slug> origin/main`.
- Small commits with a Conventional Commits subject (`feat:`, `fix:`, `docs:`, `test:`, `chore:`), as the existing history uses.
- Open the pull request as a draft. Reference the issue (`Closes #n`) and the epic (`Part of epic #1`). Paste the evidence listed below into the description.
- Agents do not merge, do not mark a draft ready, do not close issues and do not push to `main`. The owner does.
- Do not edit `LICENSE` or `.gitignore` as part of a feature.
- Do not rewrite published history.

## Evidence before a ticket is called done

A ticket is done when its acceptance criteria were observed, not when the code was written. Put this in the pull request:

1. The full output tail of `python -m unittest discover -s tests -v`: the `Ran N tests` line and `OK`. State N. It must not be lower than on `main` (38 at the baseline), and no test may be skipped, deleted or weakened without a sentence explaining why.
2. For each acceptance check ID the ticket names (for example `CS-T03`): the test name that covers it, or the manual step and what was seen.
3. For a change to the schema: a test that opens a database of the previous version built in a temporary directory, and a test that a newer `user_version` is still refused with exit code 2.
4. For a change in the browser client: what was run in a real browser, on which browser version and operating system, with external requests blocked, and whether the console showed errors. If no browser was run, say "not verified in a browser" in those words.
5. For a new static file: that it is in `STATIC_FILES`, covered by the external-URL scan and, for a script, by the HTML-injection scan (name the tests that read it), and served with the right content type.
6. `git status` is clean after the run: no database, no `__pycache__`, no generated file left behind.
7. Every server process you started was stopped.
8. The PRD statuses that changed (`[Planned]` to `[Observed]`), and the update to `README.md` limitations and to [`docs/architecture.md`](docs/architecture.md) section 3 if the ticket changed what is implemented.

Report only commands you ran and results you saw. If a check could not be run, say which and why.

## Project agents

`.claude/agents/` holds project-local subagents. Provenance, licence and the reasons for the selection are in [`.claude/agency-agents/README.md`](.claude/agency-agents/README.md).

| Agent | Tools | Use it for |
|---|---|---|
| Software Architect | Read, Grep, Glob | Reviewing a ticket's design against the boundaries above before code is written |
| Code Reviewer | Read, Grep, Glob | Reviewing a diff for correctness and broken invariants |
| Codebase Onboarding Engineer | Read, Grep, Glob | Tracing a code path with file and line citations |
| PDF Engine Architect | Read, Grep, Glob | Reviewing pagination rules, print CSS and screen/print parity |
| Accessibility Auditor | Read, Grep, Glob | Reviewing keyboard operation, labels, focus and live regions |
| Reality Checker | Read, Grep, Glob | Checking claimed evidence against what was actually run |
| Backend Architect | all | Implementing in `case_study_builder/*.py` |
| Frontend Developer | all | Implementing in `case_study_builder/static/` |
| Test Automation Engineer | all | Building browser and JavaScript checks |
| loop-verifier | Read, Grep, Glob | Part of the Loop setup; not used at L1 |

The upstream role texts recommend frameworks, cloud services, Playwright and similar tools. The hard constraints above override that advice.

These names also exist in a user-level Agency Agents install (`~/.claude/agents/`). Inside this repository the project copies take precedence. A session that was already open when the files changed keeps the old definitions; start a new session.

## Loop Engineering

The repository has a Loop Engineering setup at level L1: report-only, started by hand, no scheduler, no automated fixes, no auto-merge. [`LOOP.md`](LOOP.md) has the manual triage command; [`loop-constraints.md`](loop-constraints.md) has the binding rules. A triage run may change only `STATE.md` and `loop-run-log.md`. Do not raise the level or add a schedule; that is the owner's decision.
