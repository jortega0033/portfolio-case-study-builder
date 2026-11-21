# Project Portfolio Case Study Builder — PRD and Technical Specification

M1 is implemented. See the [baseline verification](../README.md#baseline-verification) for observed results. CS-B01–CS-B16 define its full exit criteria. Milestones M2–M6 are planned.
Labels used throughout: **[Decision]** fixed choice, **[Default]** proposed default that can be changed, **[Open]** unresolved, **[Calculated]** derived by arithmetic from stated inputs, **[Planned]** demonstration not yet run, **[Observed]** result actually seen. The README records the completed checks.

All names, projects and numbers in examples and fixtures are fictional.

---

## 1. Product definition

### 1.1 Problem
A designer or engineer who wants to present past work as a portfolio piece usually writes in a general-purpose document editor or a web page builder. The result is hard to keep consistent: headings drift, a heading is stranded at the bottom of a page, a figure is split from its caption, and exporting to PDF changes the layout that was reviewed on screen. There is no small, private, offline tool that treats a case study as structured content (a title plus ordered sections) and later lays it out reliably for print.

### 1.2 User
One author working on their own machine. They write several case studies, return to them over days, and eventually print or export them. They do not need accounts, sharing, or collaboration. [Decision]

### 1.3 One end-to-end outcome
The author opens the tool locally, writes a case study as a title and ordered sections, saves it, closes the program, starts it again later and finds the same document intact. (Baseline M1.) Later the author gets a paginated, print-ready version whose on-screen layout matches the printed one. (Epic E1.)

### 1.4 Scope
In scope for the baseline (M1):
- Project browser listing saved case studies.
- Title, ordered sections each with a heading and a body block.
- Add section, move up, move down, delete section, with button and keyboard alternatives.
- Structured reading preview that updates as the author types.
- Save to SQLite with revision checks; reopen after the server process restarts.
- Loopback-only HTTP server with Host and Origin validation, body size cap, safe text rendering.

Out of scope for the baseline, planned in epic E1: typed content blocks beyond a plain body, revision history, placeholder artwork, pagination, overflow diagnostics, print/PDF, full offline and keyboard QA.

Out of scope for the product: accounts, sync, sharing, remote hosting, rich text pasted from other tools, real personal data, analytics, any network request at runtime. [Decision]

### 1.5 Workflow states
Document (client view): `clean` → `dirty` (any edit) → `saving` → `clean` (200) | `dirty` with error (network error, validation error) | `conflict` (409). `conflict` leaves local edits visible and unsaved until the author chooses "Reload latest", which discards them and returns to `clean`.
Server view: a project exists at revision `n ≥ 1`; a successful save moves it to `n+1`.

### 1.6 Accessibility goals
- Every control has a programmatic label; section controls name their section number ("Move section 2 up").
- Visible focus on every interactive element (≥ 3 px outline, meets 3:1 contrast against both backgrounds).
- Save, move, add and delete outcomes are announced via a polite live region; errors via an alert region.
- Everything doable with the pointer is doable with the keyboard (Tab order follows reading order; Alt+Up/Alt+Down moves a section; Ctrl/Cmd+S saves).
- Text contrast meets WCAG AA. Preview body text ≥ 18 px, line height ≈ 1.6, measure ≈ 65 characters.
- Usable at 800×600 without horizontal page scroll; respects `prefers-reduced-motion`.

### 1.7 Why it matters
The stated goal is a dependable, private way to turn project notes into a polished case study.

### 1.8 Design direction
Editorial editor: plum accent on a neutral editing surface, warm paper preview, generous serif typography with no web fonts. Editor controls take priority over decoration: buttons are plain, labelled and large enough to hit; decoration is limited to the preview "paper".

---

## 2. Epic and stories (future work)

### Epic E1 — "Print-ready case studies"
Outcome: an author can compose a case study from typed blocks (paragraph, figure with caption), see a paginated preview that obeys documented fitting rules, receive diagnostics where content cannot fit, and print or save a PDF locally whose layout matches the preview, all offline and fully keyboard-operable.

| ID | Story | Depends on | Observable checks |
|---|---|---|---|
| E1-S1 | Revision-safe typed content blocks | M1 baseline | CS-T01–CS-T05 |
| E1-S2 | Original placeholder artwork and figure blocks | E1-S1 | CS-A01–CS-A04 |
| E1-S3 | Measured pagination with keep-with-next | E1-S1, E1-S2 | CS-P01–CS-P06 |
| E1-S4 | Intentional overflow diagnostics | E1-S3 | CS-D01–CS-D04 |
| E1-S5 | Local print/PDF with CSS/print parity | E1-S3, E1-S4 | CS-R01–CS-R04 |
| E1-S6 | Offline and keyboard QA and release gate | E1-S1–S5 | CS-Q01–CS-Q05 |

Ordering: S1 → S2 → S3 → S4 → S5 → S6 (S2 and S1 may overlap once the block schema is frozen).

### Story outlines
**E1-S1 Typed blocks and revisions.** Replace the single `body` with an ordered list of typed blocks (`paragraph`, `figure`, later `callout`). Store each saved revision as an immutable snapshot so a prior revision can be viewed and restored as a new revision. Migrate schema v1 → v2 without data loss.
**E1-S2 Placeholder artwork.** Provide original, bundled SVG placeholder artwork (geometric, generated by the project) and a figure block with source image dimensions, alt text and a required caption. No third-party images.
**E1-S3 Pagination.** Measure rendered blocks in a hidden container using the print stylesheet width and assign blocks to pages using the rules in §6.
**E1-S4 Overflow diagnostics.** When a rule cannot be satisfied (for example an unbreakable unit taller than a page), the preview marks the block and lists the reason; it never silently clips.
**E1-S5 Print/PDF.** Emit one wrapper per computed page with explicit page breaks, a fixed `@page` size and margins, so Chrome "Save as PDF" reproduces the on-screen pages.
**E1-S6 QA gate.** Offline verification (network blocked), keyboard-only walkthrough, regression run of all baseline checks.

---

## 3. Milestones

| Milestone | Content | Entry | Exit gate |
|---|---|---|---|
| **M1 Baseline (implemented)** | Title, ordered sections, editor controls, preview, SQLite save/reopen, security basics | — | CS-B01–CS-B16 |
| M2 | E1-S1 typed blocks + revisions, schema v2 migration | M1 | CS-T*, all CS-B* still pass |
| M3 | E1-S2 placeholder artwork and figure block | M2 | CS-A* |
| M4 | E1-S3 pagination | M3 | CS-P* |
| M5 | E1-S4 diagnostics, E1-S5 print/PDF | M4 | CS-D*, CS-R* |
| M6 | E1-S6 release integration gate | M5 | CS-Q*, full regression |

Integration gates: at the end of each milestone the whole unit suite and the browser flow in §10 run clean. M4 must freeze the fitting rules before M5 starts, because print parity depends on them.

Open decisions: [Open] whether revisions retain all history or a bounded number (default: keep all, 200 per project cap). [Open] page size (default: US Letter portrait with 0.75 in margins; A4 selectable later). [Open] whether callout blocks belong in E1 or after.

---

## 4. Architecture and offline entry points

```
Browser (Chrome) ── HTTP, loopback only ──> Python http.server (ThreadingHTTPServer, 127.0.0.1)
  static/index.html, app.css, app.js            ├─ validation.py   input rules
                                                ├─ storage.py      SQLite, transactions
                                                └─ server.py       routing, Host/Origin checks, headers
```
- Runtime: Python 3.12+ standard library, `sqlite3`, hand-written HTML/CSS/JS. No npm, no pip packages, no CDN, no web fonts, no network calls. [Decision]
- Entry point: `python -m case_study_builder --data-dir <directory> --port <port>`. Binds only to `127.0.0.1`. `--port 0` picks a free port and prints it. The data directory is created if absent and holds `case_studies.sqlite3` (plus WAL side files).
- Test entry: `python -m unittest discover -s tests -v`. Tests start the real server on an ephemeral loopback port with a temporary data directory.
- Package layout: `case_study_builder/` (code and `static/`), `tests/`, `docs/`.
- Prerequisites needing a host check: Python ≥ 3.12 with `sqlite3` (WAL support); Chrome on Linux for the browser flow. Windows/macOS are not claimed. [Assumption]

## 5. Data schema and API

### 5.1 Schema (v1, `PRAGMA user_version = 1`)
```
projects(id TEXT PK, title TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>=1), created_at TEXT, updated_at TEXT)
sections(project_id TEXT REFERENCES projects ON DELETE CASCADE, position INTEGER, section_id TEXT, heading TEXT, body TEXT,
         PRIMARY KEY(project_id, position), UNIQUE(project_id, section_id))
```
Pragmas: `foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout=5000`. A database with a newer `user_version` is refused at startup (exit code 2).

### 5.2 API (`/api/v1`)
| Method | Path | Result |
|---|---|---|
| GET | `/health` | `200 {"status":"ok","schema_version":1}` |
| GET | `/projects` | `200 {"projects":[{id,title,revision,updated_at,section_count}]}` newest first |
| POST | `/projects` | `201` project; default title "Untitled case study" and one empty section |
| GET | `/projects/{id}` | `200` project with ordered `sections` |
| PUT | `/projects/{id}` | `200` project; body `{title, base_revision, sections:[{id?, heading, body}]}` |

Errors use `{"error":{"code","message","details"}}`: 400 `invalid_json`/`invalid_field`, 403 `forbidden_host`/`forbidden_origin`, 404 `not_found`, 405 `method_not_allowed`, 409 `revision_conflict` (with `current_revision`), 411 `length_required`, 413 `payload_too_large`, 415 `unsupported_media_type`, 500 `internal_error` without stack traces. The exact semantics are the project's API contract; limits: title 1–120 chars, heading ≤ 160, body ≤ 20 000, ≤ 50 sections, request body ≤ 256 KiB.

### 5.3 Security rules
- `Host` must be `127.0.0.1:<port>` or `localhost:<port>` (blocks DNS rebinding).
- `POST`/`PUT` require an `Origin` equal to `http://<Host>`; missing or foreign Origin is rejected.
- Strict CSP (`default-src 'none'; script-src 'self'; style-src 'self'; …`), `nosniff`, `no-referrer`, API `no-store`.
- The server never interprets text as HTML. The client renders with `textContent`/`value` only.

## 6. Main algorithm and invariants

### 6.1 Baseline: revision-checked atomic replace
Save = one `BEGIN IMMEDIATE` transaction: read current revision; if it differs from `base_revision`, roll back and return 409; otherwise update the project row, delete its sections, insert the new ones with positions `0..n-1`, set revision `+1`, commit.
Invariants:
- I1 `revision` increases by exactly 1 per successful save and never otherwise changes.
- I2 Section positions are contiguous `0..n-1` and equal array order of the last successful save.
- I3 A failed or rejected save leaves the stored project byte-for-byte unchanged.
- I4 Section ids are unique within a project; ids supplied by the client are preserved on save.
- I5 Stored text equals submitted text (except `\r\n`→`\n` and trimming of title/heading).

### 6.2 Future: measured pagination (E1-S3) — documented fitting rules [Default]
Inputs: page usable height `H` (fixture: 960 px), column width `W` (fixture: 720 px), measured block heights from the same stylesheet used for print, body line height 24 px.
1. Blocks are placed in order into the current page while they fit in the remaining height `R`.
2. **Keep-with-next:** a heading is never the last item on a page. A heading and the first block after it are placed as a unit; if the unit does not fit in `R`, the whole unit moves to the next page.
3. **Short-block rule:** a paragraph of ≤ 4 lines (≤ 96 px) is unbreakable.
4. **Long-block rule:** a paragraph of more than 4 lines may split between lines, leaving at least 2 lines at the bottom of a page (orphans) and 2 at the top of the next (widows). If neither split point is legal it moves whole.
5. **Figure unit:** a figure and its caption are one unbreakable unit. The figure scales down to the column width, preserving aspect ratio, and never scales up. If the unit is taller than `H`, the figure is further scaled to fit `H` minus caption height, and a diagnostic is raised if the scale falls below 50 %.
6. **Overflow:** if a unit still cannot fit in an empty page, it is placed alone, marked overflow, and reported (E1-S4); nothing is clipped silently.
7. Termination: each block is placed exactly once; a block moved to a fresh page is always placed (rule 6), so the algorithm is linear in block count.

Print parity: the paginator measures in a hidden element that uses the exact print stylesheet (same fonts, widths, line heights). The print output uses one wrapper per computed page with `break-after: page`, fixed `@page` size and margins, and `break-inside: avoid` on units. Parity check compares block-to-page assignment from the screen paginator with the assignment extracted from Chrome's print layout.

### 6.3 Future fixture calculations [Calculated]
- Keep-with-next fixture: page height 960 px, 100 px remaining. Heading 40 px + first paragraph 72 px (3 lines × 24 px, ≤ 4 lines so unbreakable) = 112 px > 100 px, so both move to the next page together; the previous page keeps 100 px blank. Remaining on the new page = 960 − 112 = 848 px.
- Figure fixture: source 1200×800 px in a 720 px column, scale = 720 / 1200 = 0.6, giving 720×480 px (aspect 3:2 preserved). With a caption of up to two 24 px lines plus 8 px gap (56 px), the unit is 536 px ≤ 960 px, so no further scaling and no diagnostic. The caption always stays on the same page as its figure.

## 7. Errors, retry, restart, multi-tab

- **Validation error (400):** the editor shows the message in the alert region; edits stay; the author fixes and saves again.
- **Network failure or 5xx:** the editor stays `dirty`, shows an alert, and Save is re-enabled for manual retry. Retries are safe because saves are idempotent in effect under revision checks: a retry after a lost response either succeeds (revision unchanged from the client's view) or conflicts (409) if the first attempt actually committed; on 409 the author reloads and sees the already-saved content.
- **Conflict (409):** another tab or session saved first. Local edits are kept visible, saving is blocked until "Reload latest".
- **Cancel:** closing a tab discards unsaved edits; `beforeunload` warns when dirty; switching projects while dirty asks for confirmation.
- **Restart:** the server holds no state besides SQLite; after restart the same data directory reopens all projects. The browser reopens the project in `location.hash`.
- **Crash during save:** the transaction either committed or did not (SQLite WAL); there is no partial save (I3).
- **Multi-tab:** last-writer-wins is prevented by revision checks; two tabs editing the same project yield one success and one 409.
- **Locked database:** `busy_timeout` of 5 s; on timeout the server returns 500 `internal_error`, client may retry.
- **Port in use / unwritable data dir:** the CLI prints a clear message and exits non-zero.

## 8. Deterministic fixtures

Fixtures are synthetic and checked into `tests/`.
- **F1 "Lantern Library case study"** (fictional): title `Lantern Library: A Reading Lamp Redesign`; sections: 1 `Overview` / `A small team reworked a fictional desk lamp for night reading.`, 2 `Constraints` / `Budget, materials, and a two-week schedule.`, 3 `Outcome` / `Prototype tested with ten invented readers.`
- **F2 markup-like text:** heading `<script>alert(1)</script>`, body `<img src=x onerror=alert(1)> & "quotes"` to prove verbatim storage and inert rendering.
- **F3 limits:** title of 121 characters, heading of 161, body of 20 001, 51 sections.
- **F4 reorder:** sections A, B, C moved to C, A, B; ids preserved.
- **F5 layout fixture [future]:** page 960 px, remaining 100 px, heading 40 px, paragraph 72 px; figure 1200×800 in a 720 px column with caption.

## 9. Acceptance checks

Status key: **U** automated unit/integration test, **B** browser flow, **P** planned (future). No result is claimed as observed in this document.

### Baseline (M1)
| ID | Check | Expected | Type |
|---|---|---|---|
| CS-B01 | `GET /api/v1/health` | 200, `status` `ok`, `schema_version` 1 | U |
| CS-B02 | `POST /projects` with no body fields | 201, revision 1, title "Untitled case study", one section | U |
| CS-B03 | Save F1 then `GET` | Same title, 3 sections in order, revision 2 | U |
| CS-B04 | Stop server, start new server on same data dir | F1 identical, revision preserved | U (+B) |
| CS-B05 | Two saves with same `base_revision` | First 200, second 409 `revision_conflict` with `current_revision` 2; stored data equals first | U |
| CS-B06 | Invalid payloads (empty title, long title/heading/body, 51 sections, wrong types, unknown keys, control chars, duplicate section ids, bad revision) | 400 with `invalid_field`/`invalid_json`, stored data unchanged | U |
| CS-B07 | Body > 256 KiB; missing Content-Length; wrong content type | 413 / 411 / 415 | U |
| CS-B08 | Request with foreign `Host` | 403 `forbidden_host` | U |
| CS-B09 | `PUT`/`POST` with missing or foreign `Origin` | 403 `forbidden_origin`; same-origin accepted | U |
| CS-B10 | F2 round trip and preview | Stored verbatim; displayed as literal text; no element created | U (API) + B (display) |
| CS-B11 | Browser flow in §10 | All steps succeed | B |
| CS-B12 | Static assets contain no external URLs; server socket is 127.0.0.1 | Scan finds none; address is loopback | U |
| CS-B13 | Atomicity: rejected save after a good save | Stored project unchanged (I3) | U |
| CS-B14 | Accessible names and keyboard actions present | Labels named in §1.6 ("Section N heading", "Move section N up", …) exist in HTML/JS; Alt+Arrow and Ctrl+S are wired | U (static) + B |
| CS-B15 | Viewport 800×600 | No horizontal page scroll; editor and preview both reachable; focus visible | B |
| CS-B16 | Unknown routes, wrong methods, malformed ids | 404 / 405 with `Allow` / 404, JSON error envelope | U |

### Future (planned, not built)
| ID | Story | Check |
|---|---|---|
| CS-T01 | E1-S1 | Migration v1→v2 preserves every F1 section as a paragraph block, in order |
| CS-T02 | E1-S1 | Saving creates an immutable snapshot; list of revisions is ordered |
| CS-T03 | E1-S1 | Restoring revision 2 creates revision N+1 with revision 2's content |
| CS-T04 | E1-S1 | Block ids stable across reorder |
| CS-T05 | E1-S1 | Conflict behaviour of baseline still holds with blocks |
| CS-A01 | E1-S2 | Bundled placeholder SVGs load with the network blocked |
| CS-A02 | E1-S2 | Figure block requires alt text and caption; missing either is a 400 |
| CS-A03 | E1-S2 | Source dimensions stored; no third-party assets in the repository |
| CS-A04 | E1-S2 | Figure renders at 720×480 for 1200×800 in a 720 px column |
| CS-P01 | E1-S3 | F5: heading+paragraph (112 px) move together when 100 px remains |
| CS-P02 | E1-S3 | Paragraph ≤ 4 lines is never split |
| CS-P03 | E1-S3 | Paragraph > 4 lines splits with ≥ 2 lines on each side |
| CS-P04 | E1-S3 | Figure and caption are always on the same page |
| CS-P05 | E1-S3 | No heading is last on any page for random generated documents (seeded) |
| CS-P06 | E1-S3 | Pagination is deterministic: same input → same assignment |
| CS-D01 | E1-S4 | Unit taller than page is placed alone and marked overflow |
| CS-D02 | E1-S4 | Diagnostics list each overflow with block id and reason |
| CS-D03 | E1-S4 | Figure scale < 50 % raises a diagnostic |
| CS-D04 | E1-S4 | Diagnostics are exposed to assistive technology |
| CS-R01 | E1-S5 | Print stylesheet emits one wrapper per page with fixed `@page` size |
| CS-R02 | E1-S5 | Block-to-page assignment in Chrome print layout equals the screen paginator |
| CS-R03 | E1-S5 | Saved PDF page count equals computed page count |
| CS-R04 | E1-S5 | Print works with network blocked |
| CS-Q01 | E1-S6 | Full keyboard walkthrough without a pointer |
| CS-Q02 | E1-S6 | All checks pass with outbound network blocked |
| CS-Q03 | E1-S6 | All CS-B* checks still pass |
| CS-Q04 | E1-S6 | No console errors in the browser flow |
| CS-Q05 | E1-S6 | Contrast and focus checks on editor, preview and diagnostics |

## 10. Demo flow (for baseline verification)

1. `python -m case_study_builder --data-dir ./demo-data --port 8765`
2. Open `http://127.0.0.1:8765/` in Chrome. Expect the empty state and "New case study".
3. Click "New case study"; enter title `Lantern Library: A Reading Lamp Redesign`.
4. Fill section 1 heading `Overview` and body (F1). Click "Add section" twice and fill sections 2 and 3.
5. Move section 3 up with its button; move it back with Alt+ArrowDown in its heading field.
6. Delete section 2; check status announces "Section deleted (unsaved)"; add it back by "Add section".
7. Observe the preview: `h1` title, `h2` headings, paragraphs.
8. Press Ctrl+S. Expect "Saved (revision 2)".
9. Stop the server (Ctrl+C), start it again with the same command, reload the page. Expect identical content.
10. Open a second tab on the same project; save a change in tab 1; edit and save in tab 2. Expect the conflict alert and "Reload latest".
11. Resize to 800×600: no horizontal scroll, all controls reachable.

## 11. Explicit assumptions
- A1 Single local author, single machine; no authentication is needed because the server binds to loopback only and checks Host/Origin.
- A2 Python 3.12+ with SQLite WAL support is available.
- A3 Chrome on Linux is the browser target; other browsers are untested.
- A4 System serif fonts are acceptable; exact glyph metrics differ across machines, which is why future pagination measures in-browser rather than precomputing.
- A5 Full-replace saves are adequate for documents of ≤ 50 sections × 20 000 characters.
- A6 Identical-content saves still bump the revision.
- A7 No project deletion in the baseline.
- A8 Windows and macOS compatibility are not claimed.

## 12. Baseline versus work ahead

| Implemented in M1 | Not built yet |
|---|---|
| Title, ordered sections, heading and body | Typed blocks, revision history |
| Add, move up/down, delete with labelled buttons and shortcuts | Figures and original placeholder artwork |
| Live reading preview | Measured pagination, keep-with-next, long-block splitting |
| SQLite save, reopen after restart, revision conflicts | Overflow diagnostics |
| Loopback binding, Host/Origin checks, body cap, CSP | Print stylesheet, PDF export, parity checks |
| Unit/integration tests on loopback | Full offline and keyboard QA gate |
