# Design tokens

The interface uses the Pipenzo "Flow look" tokens: a black page in dark mode, Flow-style alpha layers kept as opaque solids, one accent (Pipenzo yellow `#FECE02`) and red only for danger.

## Source and resync

- File: `case_study_builder/static/tokens.css`, served at `/static/tokens.css` (listed in `STATIC_FILES`).
- Source: `jortega0033/clip-to-reel-studio`, `extension/sidepanel/tokens.css`, commit `a13378ce73e5b27213c9a200fc960ec93afef054` (2026-11-21).
- Resync: copy the file over `tokens.css`. Nothing else. Never edit the copy; the header comment of the file states the contrast rules.

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
- Yellow only on the primary action and the current-step marker. Red only for danger.

## Light and dark

`tokens.css` defines the light theme in `:root` and overrides it in a `prefers-color-scheme: dark` block. The operating system colour scheme chooses; there is no switch in the page. Dark is the primary design.
