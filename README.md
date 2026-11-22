# Portfolio Case Study Builder

A small, private, offline editor for portfolio case studies. A case study is a title plus ordered sections, each with a heading and body text. Data is stored in a local SQLite file. The app uses only the Python 3.12+ standard library and native HTML, CSS and JavaScript; there is nothing to install.

All example content is fictional.

## Run

```
python -m case_study_builder --data-dir ./demo-data --port 8765
```

Then open <http://127.0.0.1:8765/> in a browser. The server binds only to `127.0.0.1`. Use `--port 0` to pick a free port; the chosen address is printed on start. Press Ctrl+C to stop. Starting again with the same `--data-dir` reopens your saved case studies.

## Use

- **New case study** creates a draft; the project list on the left reopens saved ones.
- Edit the title and each section's heading and body. Use **Add section**, and the per-section **Move up**, **Move down** and **Delete** buttons. Keyboard: `Alt+ArrowUp` / `Alt+ArrowDown` in a section field moves the section; `Ctrl+S` (or `Cmd+S`) saves.
- The reading preview on the right updates as you type.
- If the same case study was saved from another tab, Save reports a conflict; choose **Reload latest**.

## Test

```
python -m unittest discover -s tests -v
```

Tests start the real server on an ephemeral loopback port with a temporary database.

## Documentation

`docs/PRD.md` holds the product definition, technical specification, acceptance checks and the plan for future work (typed blocks, placeholder artwork, pagination, print/PDF).

`docs/architecture.md` records how the code is built today, one traced workflow with line citations, what is implemented, planned or still unverified, and where the PRD and the code disagree.

`CLAUDE.md` holds the working rules for coding agents and contributors: commands, constraints, Git workflow and the evidence a finished ticket needs.

## Current limitations

Implemented: title, ordered sections, save/reopen, conflict detection. Not yet implemented: typed blocks, images, pagination, print/PDF, project deletion. See the baseline verification below for the tested platforms.

## Baseline verification

- The unit suite passed on Windows with Python 3.13 and on Ubuntu 24.04 in WSL2 with Python 3.12 (38 tests on Ubuntu). On Linux, use `python3` in the launch and test commands if `python` is unavailable.
- Windows Chrome 157 ran the workflow with external browser requests blocked. Created a case study with two sections, checked the reading preview, then saved and reopened the case study after a server restart. The browser reported no uncaught page errors.
