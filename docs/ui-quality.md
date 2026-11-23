# UI quality rules

Binding since 2026-11-22 (owner decision, see [`owner-decisions.md`](owner-decisions.md)). Rules 1 and 2 were stated by the owner; rules 3 to 10 were proposed and approved the same day and have the same standing. They keep the interface from showing the usual marks of generated UIs.

1. No thick accent border on one side of a card, callout, alert, list item or quote (for example `border-left: 4px solid <accent>`). Use spacing, type weight, an icon or a full hairline border instead.
2. No soft tinted background with a thin border of the same hue as the default way to mark a status, tag, callout or card. One neutral surface and one clear signal (text, icon or a solid chip) is enough.
3. No gradient text, and no purple-to-blue gradient as a default accent.
4. No blur or glass panels, and no drop shadow plus large radius on every card.
5. No emoji used as icons or bullets, and no sparkle marks.
6. No pill or badge on things that are not states. No all-caps, letter-spaced micro labels as section decoration.
7. No centred hero with a slogan in an application screen. Screens open on the user's task.
8. One accent colour, used for the primary action and the current selection. Status colours only for status.
9. Dense, aligned layouts on a consistent spacing scale. No card grid where a table or a list is the right form.
10. User-facing copy is plain and specific: no filler, no exclamation marks, and the same word for the same thing everywhere.

## How the rules are applied

- A UI ticket starts with the `ui-ux-pro-max` skill (design-system search for the product type, `python .claude/skills/ui-ux-pro-max/scripts/search.py "<query>" --design-system`) and ends with a check of every changed screen against this file. Both steps are in [`implement-ticket`](../.claude/skills/implement-ticket/SKILL.md).
- User-facing copy, documentation and pull request text go through the `unslop` skill before the pull request is opened.
- The Frontend Developer, Accessibility Auditor and Code Reviewer roles name this file in their checklists. The Code Reviewer runs on every ticket and treats a breach as a blocker.
- Enforcement is by that review gate, not by a script. Rule 1 can be linted with a search for one-sided `border-left`, `border-right`, `border-inline-start` or `border-inline-end` widths above 2px; rule 2 cannot be detected reliably from CSS.
- The hard constraints in `CLAUDE.md` still apply: no external fonts, images or icons, no inline `style=`.
- Colours come from the design tokens in [`design-tokens.md`](design-tokens.md); new UI adds no colour literals.
- Rule 8 is read with the Rules section of [`design-tokens.md`](design-tokens.md) and decision 14 in [`owner-decisions.md`](owner-decisions.md): the accent also marks the current step, and `--focus` is a focus indicator, exempt from the accent limit.
