# Design tokens

The interface uses the Pipenzo "Flow look" tokens: a black page in dark mode, Flow-style alpha layers kept as opaque solids, one accent (Pipenzo yellow `#FECE02`) and red only for danger. The rules below say where the accent may appear.

## Source and resync

- File: `case_study_builder/static/tokens.css`, served at `/static/tokens.css` (listed in `STATIC_FILES`).
- Source: `jortega0033/clip-to-reel-studio`, `extension/sidepanel/tokens.css`, commit `a13378ce73e5b27213c9a200fc960ec93afef054` (2026-11-21).
- Resync: write the file from git, not from a working tree (a checkout with `core.autocrlf=true` turns LF into CRLF): `git -C <clip-to-reel-studio> show <commit>:extension/sidepanel/tokens.css > case_study_builder/static/tokens.css`. Then check that `git hash-object case_study_builder/static/tokens.css` prints the blob hash of the pinned source (`41d6d6dbb17ea1055db9c4bc2ea8fb0b557ef108` for `a13378c`) and that `git ls-files --eol` shows `i/lf`. `.gitattributes` (`*.css text eol=lf`) keeps CRLF out. Never edit the copy. The header comment of `tokens.css` states the contrast rules, and those stay in force. Its Yellow rule does not list the current selection, and the comment on `--state-selected` calls it the selected-row fill. These comments cannot be changed here because the copy must stay identical to the source. For where yellow may be used and how a current selection is marked, the Rules section below takes precedence.

## Token groups

- Surfaces: `--bg`, `--bg-raised`, `--surface`, `--bg-sunken`.
- Text and lines: `--fg`, `--muted`, `--faint`, `--border`, `--hairline`, `--control-border`, `--input-border`.
- Accent: `--primary`, `--primary-press`, `--on-primary`, `--primary-edge`, `--focus`.
- Status: `--danger`, `--danger-bg`, `--success`, `--ok`, `--ok-bg`, `--warn-fg`, `--warn-bg`, `--info`.
- Dark blocks: `--ink`, `--on-ink`, `--on-ink-muted`, `--ink-border`, `--hero-*`.
- Alpha layers: `--state-hover`, `--state-selected`, `--btn-secondary*`, `--glass*`, `--scrim`. Text never sits on a bare alpha layer. `docs/ui-quality.md` rule 4 still forbids glass panels.
- Type, space, shape, motion: `--font`, `--mono`, `--space-1` to `--space-7`, `--radius-*`, `--dur-*`, `--ease-*`, `--shadow-*`.

`app.css` keeps only `--serif` and `--sans` of its own (the preview and the application font stacks).

## Rules

- New UI uses these tokens. No new colour literals in CSS or JavaScript. A script that needs a colour reads it with `getComputedStyle(document.documentElement).getPropertyValue('--token')`.
- Yellow (`--primary`) is used for the primary action, the current-step marker and the current selection (UI rule 8). Decided by the owner on 2026-11-23 (decision 14, D1, in [`owner-decisions.md`](owner-decisions.md)). Red only for danger.
- Current selection (how part of D1): a solid `--primary` fill with `--on-primary` text, plus a second sign that is not colour (weight, an icon or text) and the existing aria attribute (`aria-current`, `aria-selected` or `aria-pressed`). A yellow border alone is not enough: it has about 1.5:1 contrast against white in the light theme. Never a tint with a border of the same hue, and never a thick border on one side (UI rules 1 and 2).
- Focus ring (D2): `--focus` is a focus indicator and is exempt from the one-accent limit, including where it is yellow in dark. A ticket that says the focus style stays unchanged means the rule on `main` after the token pull request.
- Both themes (D3): checks for contrast and for "not colour alone" cover the light block (`:root`) and the dark block (`prefers-color-scheme: dark`) of `tokens.css`.
- Linking (D4): a ticket that creates a page, or its static allowlist, links `tokens.css` before any other stylesheet and serves it (an entry in `STATIC_FILES` and a test for it).
- The four rules after the yellow rule were recommended by the orchestrator and adopted under the owner's delegation of 2026-11-23 (decision 14: how part of D1, D2, D3, D4).
- Current state: the project list marks the current project with the solid `--primary` fill, `--on-primary` text and `aria-current="true"`. It has no second sign that is visible and not colour yet (weight, an icon or text); that follows in ticket work.

## Light and dark

`tokens.css` defines the light theme in `:root` and overrides it in a `prefers-color-scheme: dark` block. The operating system colour scheme chooses; there is no switch in the page. Dark is the primary design.
