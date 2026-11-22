# Architecture and status record

This document describes how the code is built today, traces one real workflow through it, and lists where the [PRD](PRD.md) and the code disagree. The PRD stays the source for what the product should be; this file is the source for what exists.

Written during repository preparation on 2026-11-22 against commit `81dc815` (the only commit on `main`). Line numbers refer to that commit. When you change the code, update the affected section in the same pull request.

Status words used below:

- **Implemented**: the code exists and a check that exercises it was run on 2026-11-22 and passed (one test passed in two of three runs; section 5, item 12).
- **Implemented, read only**: the code exists and was read, but no check that exercises it was run.
- **Planned**: described in the PRD, nothing in the code.
- **Needs verification**: a claim that nobody has checked yet, or that was checked only on one platform.

## 1. Traced workflow: edit a case study, save it, reopen it after a restart

1. **Start.** `python -m case_study_builder --data-dir D --port P` runs `main()` (`case_study_builder/__main__.py:25`). It calls `create_server` (`__main__.py:32`), which creates the data directory, opens `Storage(D/"case_studies.sqlite3")` and binds `_Server(("127.0.0.1", port))` (`server.py:207-214`). `Storage.__init__` reads `PRAGMA user_version`: a newer version raises `SchemaTooNew`, an older one creates the tables inside `BEGIN IMMEDIATE` and sets the version, and in every accepted case WAL mode is switched on (`storage.py:51-76`). `main()` prints `Serving on http://127.0.0.1:<port>/` and calls `serve_forever()` (`__main__.py:51-53`).
2. **Page load.** `GET /` is answered from the `STATIC_FILES` whitelist (`server.py:21-25`, `server.py:141-142`, `_static` at `server.py:168-174`). `init()` (`static/app.js:467`) calls `GET /api/v1/projects`, picks the project named in `location.hash` or else the first of the list, which the server orders by `updated_at` descending (`storage.py:113-123`), and opens it with `openProject` (`app.js:281`).
3. **Edit.** `input` events copy the field value into `state.project`, call `markDirty()` and re-render the preview (`app.js:397-412`). `renderPreview()` (`app.js:82-103`) builds an `h2` for the title, an `h3` for each non-empty section heading and one `p` per chunk of the body split on blank lines, all with `textContent`.
4. **Save.** Ctrl+S or Cmd+S (`app.js:445-450`) or submitting the form (`app.js:435`) calls `save()` (`app.js:322`). It sends `PUT /api/v1/projects/{id}` with `{title, base_revision, sections:[{id?, heading, body}]}`.
5. **Request handling.** `_handle` (`server.py:87`) calls `_route` (`server.py:112`): Host check (`_check_host`, `server.py:105-110`), route and method match (`server.py:117-133`), same-origin `Origin` check for `POST` and `PUT` (`server.py:135-138`). `_read_json` (`server.py:176-196`) enforces `application/json`, a numeric `Content-Length`, no chunked bodies and the 262144-byte cap (`MAX_BODY_BYTES`, `server.py:13`). `validate_project_payload(..., require_revision=True)` (`validation.py:90-123`) checks keys, types and limits and assigns ids to sections that have none (`validation.py:79-86`).
6. **Storage.** `Storage.update_project` (`storage.py:157-179`) runs one `BEGIN IMMEDIATE` transaction: read the current revision; raise `NotFound` or `RevisionConflict` if it is missing or differs from `base_revision`; update the project row with `revision+1`; `_write_sections` deletes all sections of the project and inserts the new list at positions `0..n-1` (`storage.py:129-136`); reload; commit. Any exception rolls back (`storage.py:176-178`).
7. **Response.** 200 with the stored project (`server.py:166`). A conflict becomes 409 `revision_conflict` with `current_revision` (`server.py:162-165`). The client then sets `state.conflict`, shows the alert, disables Save and focuses "Reload latest" (`app.js:362-375`, `updateControls` at `app.js:75-79`).
8. **Restart.** The server keeps no state besides the SQLite file. Starting it again with the same `--data-dir` reopens the same file. `tests/test_restart.py` covers this in process (`test_b04_data_survives_server_restart`) and through the real command line (`test_b04_cli_restart_reopens_saved_project`).

## 2. Actual architecture

**Pattern.** A layered monolith without a framework: a hand-written JSON API on `http.server.ThreadingHTTPServer`, SQLite for persistence, and a single static page in plain JavaScript (one IIFE, one `state` object, 485 lines).

**Layers and what each owns.**

| Layer | File | Owns |
|---|---|---|
| Command line | `case_study_builder/__main__.py` (62 lines) | Arguments, exit codes (2 for a newer schema, 1 for database or socket errors), SIGINT, SIGTERM and SIGBREAK handling |
| HTTP | `case_study_builder/server.py` (214 lines) | Routing, Host and Origin checks, body limits, security headers, error envelope, static whitelist |
| Validation | `case_study_builder/validation.py` (123 lines) | Payload shape and limits. Pure: no I/O, no imports from the other layers |
| Storage | `case_study_builder/storage.py` (179 lines) | Schema, the version check, transactions. One connection per operation (`_connect`, `storage.py:78-82`) |
| Client | `case_study_builder/static/index.html`, `app.css`, `app.js` | Editor, project list, live preview, dirty and conflict states |
| Tests | `tests/helpers.py`, `test_api.py`, `test_restart.py`, `test_static.py` | 38 tests. Each server test starts a real server on an ephemeral port with a temporary database |

**Data ownership.** The server and SQLite are authoritative. The client keeps a working copy and the `revision` it loaded. It gives each section a local `key` (`app.js:26`) that is never sent. The server assigns a section id (`s` plus 8 hex characters) when the client sends none (`validation.py:79-86`) and a project id (`uuid4().hex`, `storage.py:139`).

**Invariants in code.**

| Invariant | Where |
|---|---|
| Revision rises by exactly 1 per successful save (PRD I1) | `storage.py:167-172` |
| Section positions are `0..n-1` in array order (I2) | `storage.py:129-136`, primary key `(project_id, position)` at `storage.py:26` |
| A rejected save changes nothing (I3) | Rollback at `storage.py:176-178`; validation runs before storage is called (`server.py:156`) |
| Section ids are unique within a project; client ids are kept (I4) | `validation.py:67-73`, `UNIQUE(project_id, section_id)` at `storage.py:27` |
| Stored text equals submitted text except `\r\n` to `\n` and trimmed title and heading (I5) | `validation.py:31-47`, `validation.py:76-77`, `validation.py:115` |
| Limits: title 1 to 120, heading up to 160, body up to 20000 characters, up to 50 sections | `validation.py:8-11` |
| Loopback bind | `server.py:212` |
| Host must be `127.0.0.1:<port>` or `localhost:<port>` | `server.py:105-110` |
| `POST` and `PUT` need `Origin` equal to `http://<Host>` | `server.py:135-138` |
| CSP, `nosniff`, `no-referrer`, `no-store` on every response | `server.py:18-19`, `server.py:65-68` |
| A database with a newer `user_version` is refused, exit code 2 | `storage.py:56-60`, `__main__.py:33-35` |

**Schema.** Version 1 only (`SCHEMA_VERSION`, `storage.py:10`; tables at `storage.py:12-29`). There is no migration framework: `Storage.__init__` knows "older than current, create everything" and "newer than current, refuse".

## 3. PRD capabilities and their status

| PRD capability | Status | Evidence |
|---|---|---|
| Project browser (section 1.4) | Implemented | `list_projects` (`storage.py:113`), `renderList` (`app.js:106`); `test_list_ordering_and_counts` |
| Title and ordered sections with heading and body | Implemented | `validation.py`, `storage.py`; `test_b03_save_and_reload_preserves_order` |
| Add, move, delete section; Alt+Arrow; Ctrl+S | Implemented, read only | `app.js:220-262`, `app.js:423-430`, `app.js:445-450`. `test_b14_labels_and_controls_present` only checks that the strings exist in the source. Not driven in a browser on 2026-11-22. |
| Live reading preview | Implemented | `app.js:82-103`. A headless Chrome 157 run on 2026-11-22 showed the saved fixture rendered in the preview (section 4). Typing was not exercised. |
| Save with revision checks | Implemented | `storage.py:157-179`; `test_b05_revision_conflict`, `test_b13_rejected_save_after_good_save_leaves_state` |
| Reopen after restart | Implemented | `tests/test_restart.py`; repeated by hand on 2026-11-22 (section 4) |
| Host, Origin, body size, CSP | Implemented; early rejections need verification on Windows | `server.py`; `test_b07_*`, `test_b08_*`, `test_b09_*`, `test_no_cors_headers_and_security_headers`. See section 5, item 12. |
| Markup-like text is stored verbatim and shown as text (CS-B10) | Implemented | `test_b10_markup_like_text_round_trips_verbatim`; the headless Chrome run showed the text escaped in the DOM and no `img` element created |
| Conflict flow in the editor, `beforeunload` warning, confirm on project switch (section 7) | Implemented, read only | `app.js:362-375`, `app.js:452-457`, `app.js:298-301`, `app.js:437-443` |
| Accessibility goals (section 1.6) | Needs verification | Labels and live regions exist in the source (`index.html:34-35`, `app.js:157`, `app.js:174`, `app.js:187-189`). Contrast, visible focus, tab order and the 800 by 600 layout (CS-B15) were not checked in a browser on 2026-11-22. |
| Browser flow of section 10 (CS-B11) | Needs verification | The README records one manual run on Windows Chrome 157. It was not repeated in full on 2026-11-22. |
| Port in use, unwritable data directory (section 7) | Needs verification, one part fails on Windows | See section 5, item 4 |
| Typed blocks and revision history (E1-S1) | Planned | No block or snapshot tables, no revision routes |
| Placeholder artwork and figure blocks (E1-S2) | Planned | No SVG files, no figure model |
| Measured pagination (E1-S3) | Planned | Nothing in the code |
| Overflow diagnostics (E1-S4) | Planned | Nothing in the code |
| Print and PDF with parity (E1-S5) | Planned | `app.css` has no `@media print` and no `@page` rule |
| Offline and keyboard release gate (E1-S6) | Planned | No gate, no browser test harness |

## 4. Runnable baseline: what was run on 2026-11-22

A runnable end-to-end baseline exists. Environment: Windows 11, Python 3.13.14, Chrome 157, from a clean checkout of `81dc815`.

| Check | Command or method | Result |
|---|---|---|
| Unit and integration suite | `python -m unittest discover -s tests -v` | Run three times, each a full run of 38 tests. First run: `Ran 38 tests in 18.618s`, `OK`. Second run: `FAILED (errors=1)`, `test_b07_content_type_and_length` raised `ConnectionAbortedError: [WinError 10053]` while reading the response. Third run: `OK`. No file under `case_study_builder/` or `tests/` differed from `81dc815` in any run. See section 5, item 12. |
| Launch, save, restart | `python -m case_study_builder --data-dir <temp> --port 0`, then `GET /api/v1/health`, `GET /`, `POST /api/v1/projects`, `PUT /api/v1/projects/{id}`, stop, start again with the same directory, `GET /api/v1/projects/{id}` | `Serving on http://127.0.0.1:<port>/`; health `{"status": "ok", "schema_version": 1}`; create 201 at revision 1 with one section; save 200 at revision 2; the data directory held `case_studies.sqlite3`; after the restart the project was returned identical at revision 2 |
| Page renders a saved project with other hosts unreachable | Headless Chrome with `--host-resolver-rules="MAP * ~NOTFOUND, EXCLUDE 127.0.0.1"`, `--virtual-time-budget=4000`, `--dump-dom` on `/#<project id>` | Exit 0. Status region `Loaded revision 1`. Preview contained the title as `h2`, three `h3` headings and three paragraphs. The heading `<script>alert(1)</script>` and the body `<img src=x onerror=alert(1)> & "quotes"` appeared as escaped text; the DOM had one `script` element (the app's own) and no `img` element. |
| Chrome can print the page to a PDF | Same Chrome flags with `--print-to-pdf` | Exit 0, a PDF of 2 pages (the unpaginated page as it is today). The page count could be read from the file with a regular expression (`/Type /Page` objects and `/Count 2`). |
| Chrome's command-line PDF output uses the stylesheet's page box | Same Chrome flags plus `--no-pdf-header-footer`, on `file://` test pages with `@page { size: 8.5in 11in; margin: 0.75in }` and 38 empty blocks of 24 pixels (912 pixels), then with one more pixel | Chrome 157.0.8103.79. 912 pixels: 1 page. 913 pixels: 2 pages. `MediaBox` 612 by 792 points (US Letter). Without the `@page` rule the same 913 pixels fit on 1 page. So the page size and margins come from the stylesheet and the content is not scaled. Checked for fixed-height blocks only, not for text, not for the app's own page. |
| Second server on a port that is in use | Start one server, start a second with the same `--port` | The second server started as well and kept running. See section 5, item 4. |
| What the socket option does on Windows | In-process sockets and bare `http.server` classes on `127.0.0.1`, no change to the app | `http.server.HTTPServer.allow_reuse_address` is `1`. A `ThreadingHTTPServer` subclass with `allow_reuse_address = False` refused a second server on the same port with `WinError 10048`. See section 5, item 4. |
| Data directory that cannot be created | `--data-dir` below an existing file | Exit 1, `error: cannot start server: ...`, no traceback |

Not run on 2026-11-22: the manual browser flow of PRD section 10 (typing, moving and deleting sections, the two-tab conflict, the 800 by 600 viewport), any check on Linux or macOS, any check with a screen reader.

The headless Chrome results matter for the planned work: they show that a browser check can be driven from the standard library alone (start the server, run Chrome as a subprocess, read the DOM or count PDF pages), without npm packages, and that a PDF page count can stand for the printed layout because the command-line print path follows the `@page` rule.

## 5. Where the PRD, the README and the code disagree

1. **Heading levels in the preview.** PRD section 10, step 7, expects "`h1` title, `h2` headings". The code renders the title as `h2` and section headings as `h3` (`app.js:87-93`), because the page's only `h1` is the application name (`index.html:12`). Observed in the DOM on 2026-11-22. The code gives a correct heading outline; the PRD step is out of date. The print layout of epic E1 has to decide which levels a printed case study uses.
2. **Platform claims.** The PRD names Chrome on Linux as the target and says Windows and macOS are not claimed (section 4, assumptions A3 and A8). The README records the unit suite on Windows with Python 3.13 and a manual browser run on Windows Chrome 157. The 2026-11-22 run was also on Windows. No Linux result was observed during preparation.
3. **"Observed" wording.** The PRD header points to the README for observed results, while PRD section 9 says that no result is claimed as observed in that document. Both are true as written, but the PRD carries no dated evidence itself. Section 4 above is the dated record.
4. **Port in use on Windows.** PRD section 7 says the command line prints a clear message and exits non-zero when the port is in use. On Windows it does not: `_Server.allow_reuse_address = True` (`server.py:201`) sets `SO_REUSEADDR`, which on Windows lets a second process bind the same port. Observed on 2026-11-22: two servers with different data directories listened on the same port at the same time. A browser tab can then reach either one. On Linux the option does not allow this; that was not verified. No test covers the port-in-use case. Line 201 only restates a default: `http.server.HTTPServer` sets `allow_reuse_address = 1` itself, so deleting the line would change nothing. A fix has to turn the option off on Windows explicitly or set `SO_EXCLUSIVEADDRUSE` before the bind. Observed on 2026-11-22 with sockets only (section 4): with the option off, a second server on the same port is refused with `WinError 10048`, an `OSError`, which `__main__.py:39-41` already turns into the message and exit code 1.
5. **The API contract document.** PRD section 5.2 says "the exact semantics are the project's API contract". No such document is tracked in the repository. The tests are the only executable statement of the contract.
6. **Fixtures.** PRD section 8 says fixtures are checked into `tests/`. F1 is a named constant (`LANTERN` in `tests/helpers.py`). F2, F3 and F4 exist only as inline values inside `tests/test_api.py`. F5 (layout) does not exist yet, as the PRD says.
7. **`Cache-Control`.** PRD section 5.3 lists `no-store` for the API. The code sends it on every response, static files included (`server.py:68`); the `api` parameter of `_send` is unused (`server.py:59`). Harmless offline, but each page load re-fetches the script and stylesheet.
8. **Page geometry for the planned pagination.** PRD section 3 proposes US Letter portrait with 0.75 inch margins as the default page. At 96 CSS pixels per inch that is a content box of 672 by 912 pixels (816 minus 144, 1056 minus 144). The fixtures of PRD section 6.2 and 6.3 use a column of 720 pixels and a usable height of 960 pixels, which is US Letter with 0.5 inch margins (816 minus 96, 1056 minus 96). The two do not match. The fixture numbers are test inputs for the fitting rules; the real page box must be decided before the fitting rules are frozen (PRD section 3, "M4 must freeze the fitting rules").
9. **Line height for the planned pagination.** PRD section 6.2 assumes a body line height of 24 pixels. The current preview uses 1.15 rem at 1.6, about 29.4 pixels (`app.css:99-100`). The planned page stylesheet needs its own type scale; the current preview values cannot be reused unchanged.
10. **Keep-with-next and long paragraphs.** PRD section 6.2, rule 2, makes a heading and the whole first block one unit. Read literally, a heading followed by a paragraph longer than a page would be an overflow, although rule 4 allows that paragraph to split. The pagination ticket has to state the intended reading (heading plus the first legal fragment of a splittable paragraph).
11. **"All baseline checks still pass" after schema 2.** PRD section 3 requires all `CS-B*` checks to keep passing after milestone M2, and CS-Q03 says "unchanged". CS-B01 expects `schema_version` 1, `test_schema_metadata` expects `user_version` 1, and `test_newer_schema_is_refused_with_exit_code_2` builds a version 2 database as the "newer" one. These three encode the version number and must change with schema 2. `/api/v1/health` also returns a literal `1` (`server.py:144`) instead of `storage.SCHEMA_VERSION`.
12. **One test fails now and then on Windows.** `test_b07_content_type_and_length` (`tests/test_api.py:175`) failed in one of three runs on 2026-11-22 with `ConnectionAbortedError: [WinError 10053]`; the stages that inventoried and traced the repository earlier the same day saw it pass. The test posts a small body with the wrong content type. The server answers 415 without reading the body and marks the connection for closing (`server.py:60-61`, `server.py:69-70`). Likely cause, not confirmed: closing a socket that still holds unread request bytes makes Windows reset the connection, and the reset can reach the client before it has read the response. Every `POST` or `PUT` that is rejected before `_read_json` reads the body takes the same path (403, 404, 405, 411, 413, 415). PRD section 5.2 promises a JSON error for these cases; a browser could see a failed request instead. Until this is fixed, a single failure of this kind on Windows is a known defect, not a regression: rerun once and report both results.
13. **Keep-with-next and a figure scaled to the page.** PRD section 6.2, rule 5, scales a figure that is too tall "to fit `H` minus caption height", which fills a whole page. Rule 2 makes a heading and the first block after it one unit. Read together, a heading followed by such a figure is a unit taller than a page (for example 40 + 856 + 8 + 48 = 952 pixels on a 912 pixel page), and rule 6 reports it as an overflow. A section that starts with a tall figure would then always overflow. The PRD also does not say whether the 50 percent diagnostic counts scaling to the column width (a 1600 pixel wide figure in a 672 pixel column is at 0.42). Calculated from the rules, nothing is implemented. The pagination ticket has to state the intended reading: scale the figure to the space the heading leaves, and say which scale the diagnostic counts.

## 6. Risks for whoever implements epic E1

1. **No migration path exists.** `Storage.__init__` must learn to upgrade version 1 in place, inside one transaction, and still refuse a newer version (`storage.py:51-76`).
2. **Saves replace all sections.** `_write_sections` deletes and reinserts (`storage.py:129-136`). Stable block ids and immutable revision snapshots have to survive that pattern.
3. **The payload shape will change.** Almost every test in `tests/test_api.py` sends `body`. Moving to typed blocks touches those tests; item 11 in section 5 applies.
4. **One JavaScript file.** `app.js` is a single IIFE. Pagination, diagnostics and print will not fit into it sensibly. Every new file must be added to `STATIC_FILES` (`server.py:21-25`) and to the scans in `tests/test_static.py`. Today the external-URL scan lists three file names explicitly (`test_static.py:21`), and the scan for HTML injection and the check of labels and controls read only `app.js` (`test_static.py:36`, `test_static.py:42`). A new script is therefore served without being scanned until those tests walk the directory; that change has to land before, or together with, the first new static file.
5. **Content-Security-Policy.** `style-src 'self'` forbids inline styles and `style=` attributes; `img-src 'self' data:` allows bundled images (`server.py:18-19`). Figure sizes have to come from `width` and `height` attributes, classes or the CSS object model, not from `style` attributes.
6. **No browser test harness.** Nothing in the repository drives a browser or runs JavaScript tests. Pagination, diagnostics, print parity and the release gate all need one. Section 4 shows a dependency-free way.
7. **Print parity is unproven.** Whether Chrome's print layout breaks lines exactly as the screen measurement does is not known. The design should make a mismatch visible (never clip a page wrapper) so that a page count check catches it. A page count check is only evidence where the command-line PDF output follows the stylesheet's `@page` size and margins without scaling. That was observed on one host for fixed-height blocks (section 4) and should be kept as a permanent test in the browser harness.
8. **Tests start real servers.** About 20 seconds for 38 tests. Do not run them in a watch loop. One of them is intermittent on Windows (section 5, item 12), which weakens "the suite passed" as evidence until it is fixed.
9. **No project deletion and no list paging** (assumption A7). `GET /api/v1/projects` returns everything (`storage.py:113-123`).
10. **The body read has no time limit.** `_read_json` calls `rfile.read(length)` (`server.py:188`) and `Handler` sets no `timeout` (`server.py:49`; the default of `socketserver.StreamRequestHandler` is `None`). A `POST` or `PUT` that passes the early checks, declares a length and never sends its body holds one daemon thread until the client disconnects. Read from the source, not exercised. On a loopback-only, single-user server this is a known limit and not a defect to fix in passing; a fix for the early rejections (section 5, item 12) must not add an unbounded wait of its own.
