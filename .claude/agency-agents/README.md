# Agency Agents roles used in this repository

The Markdown files in `.claude/agents/` whose names start with `engineering-` or `testing-` are copies of role definitions from Agency Agents. They are project-local Claude Code subagents. The file `loop-verifier.md` in the same folder is not from Agency Agents; it belongs to the Loop Engineering setup described in [`LOOP.md`](../../LOOP.md).

## Source and licence

- Upstream: https://github.com/msitarzewski/agency-agents
- Pinned revision: `8ae6164602c95ca78828b148b9052460ee426885` (upstream `main`, 2026-11-09)
- Licence: MIT, "Copyright (c) 2025 AgentLand Contributors". The upstream licence text at the pinned revision is kept unchanged in [`LICENSE`](LICENSE) next to this file (SHA-256 `9a45258434d5cedf0af73c9ad4771373701225038d246c49219026c33677f66f`). It covers only the copied role files, not the rest of this repository.
- Fetched with `gh api "repos/msitarzewski/agency-agents/contents/<path>?ref=<revision>" -H "Accept: application/vnd.github.raw"`.

## Installed roles

"Upstream SHA-256" is the hash of the file as fetched at the pinned revision. Reviewer roles have one added frontmatter line, `tools: Read, Grep, Glob`, directly after `description:`, so they cannot edit files or run commands. Nothing else in any file was changed.

| File in `.claude/agents/` | `name:` | Upstream path | Upstream SHA-256 | Local change |
|---|---|---|---|---|
| `engineering-software-architect.md` | Software Architect | `engineering/engineering-software-architect.md` | `b85121691776147bacde26673e68fbbacd6a7f0816d1ca8e203c264d25ce1d30` | added `tools: Read, Grep, Glob` |
| `engineering-code-reviewer.md` | Code Reviewer | `engineering/engineering-code-reviewer.md` | `7509fcc3ea1dda46511b2801996305bf3d4a125576f9655ff0b63df25602f446` | added `tools: Read, Grep, Glob` |
| `engineering-codebase-onboarding-engineer.md` | Codebase Onboarding Engineer | `engineering/engineering-codebase-onboarding-engineer.md` | `07aa548b45887c3ad768efad5fdbf6e57bea639df4f1b74c7e383142f454e2a1` | added `tools: Read, Grep, Glob` |
| `engineering-pdf-engine-architect.md` | PDF Engine Architect | `engineering/engineering-pdf-engine-architect.md` | `367dd859aeda52d2a3de6ffd33b8c38eac625e884a2f71574a73d38350f8f457` | added `tools: Read, Grep, Glob` |
| `testing-accessibility-auditor.md` | Accessibility Auditor | `testing/testing-accessibility-auditor.md` | `362935907af23839775b9c6162f38c0c5a740542ab4350cb5c5b5a0d9f9a4268` | added `tools: Read, Grep, Glob` |
| `testing-reality-checker.md` | Reality Checker | `testing/testing-reality-checker.md` | `6d32fcdb114233e13902ec6372d50293b120e85d490b5e81d372c29808f988a1` | added `tools: Read, Grep, Glob` |
| `engineering-backend-architect.md` | Backend Architect | `engineering/engineering-backend-architect.md` | `ac717bde4848d7663fff8a3c7edc711fd119256de6a7ce38c036619372f42c99` | none |
| `engineering-frontend-developer.md` | Frontend Developer | `engineering/engineering-frontend-developer.md` | `1ae4cc10b2e0163bd3ed921ad54080b865cd02e591becd8919b64b73fab06dad` | none |
| `testing-test-automation-engineer.md` | Test Automation Engineer | `testing/testing-test-automation-engineer.md` | `4299d038e88387546d645ccbe767b1dfdb7de10da55eba1ab103149972cd2b9b` | none |

To compare a reviewer copy with upstream, remove its `tools:` line and hash the result; it must equal the hash in the table.

## Why these roles

| Role | Use in this repository |
|---|---|
| Software Architect (read-only) | Review a ticket's design against the layering in [`docs/architecture.md`](../../docs/architecture.md) before code is written: the schema v2 migration, the split of the browser client into modules, the paginator's pure core. |
| Code Reviewer (read-only) | Review a diff for correctness, missed edge cases and broken invariants (I1 to I5 in the PRD). |
| Codebase Onboarding Engineer (read-only) | Trace a code path and report facts with file and line citations. |
| PDF Engine Architect (read-only) | Review the pagination rules, the print stylesheet and the screen/print parity check of epic E1 (issues on pagination and print/PDF). |
| Accessibility Auditor (read-only) | Review keyboard operation, focus handling, accessible names and live-region announcements, which PRD section 1.6 and the CS-D04 and CS-Q checks treat as acceptance criteria. |
| Reality Checker (read-only) | Check claimed evidence against what was actually run before a ticket or the release gate is called done. |
| Backend Architect | Implement work in `case_study_builder/*.py` (HTTP layer, storage, validation). |
| Frontend Developer | Implement work in `case_study_builder/static/`. |
| Test Automation Engineer | Build the JavaScript unit tests and the browser run for print parity and the release gate. |

Several roles are written for larger stacks than this one. Backend Architect talks about cloud services and microservices, Frontend Developer about React, Vue and Angular, Test Automation Engineer about Playwright and Cypress, and PDF Engine Architect about Playwright browser pools and tagged PDF. In this repository the rules in [`CLAUDE.md`](../../CLAUDE.md) win: Python standard library only, native HTML, CSS and JavaScript, no pip or npm dependencies in the product, no external requests, and print goes through the browser's own print dialog. Use the roles for their review habits, not for their stack advice.

## Name collision with user-level agents

A developer who has installed Agency Agents in `~/.claude/agents/` already has agents with the same `name:` values. Claude Code gives the project-level definition precedence, so inside this repository the copies here are used, including the read-only tool limits. The upstream names were kept on purpose so that the roles stay recognisable and can be compared with upstream.

A Claude Code session that was already running when these files were added keeps the definitions it loaded at start. Start a new session to pick up the project copies.

## Check that the roles load

From the repository root, in a new session:

```text
claude -p "List the project-level subagents defined in .claude/agents with the tools each one may use. Then run the Reality Checker subagent and ask it which tools it has."
```

The six reviewer roles and `loop-verifier` must report exactly `Read, Grep, Glob`.

### What was observed, and what was not

Observed on 2026-11-22 with Claude Code 2.1.323, headless (`claude -p --model haiku --strict-mcp-config --mcp-config <empty>`, prompt on standard input), from the repository root, before the files were committed:

- The listing showed Software Architect, Code Reviewer, Codebase Onboarding Engineer, PDF Engine Architect, Accessibility Auditor, Reality Checker and `loop-verifier` with `Read, Grep, Glob`, and Backend Architect, Frontend Developer and Test Automation Engineer with all tools.
- A launched PDF Engine Architect and a launched Reality Checker each reported exactly `Read`, `Grep`, `Glob`. The user-level copies of these roles on that machine have no `tools:` line, so this shows that the project copies were the ones loaded.
- **Not shown:** that Backend Architect, Frontend Developer and Test Automation Engineer are loaded from the project copies. These three files are unchanged from upstream and have no `tools:` line, exactly like a user-level install, and the listing shows names and tools only, not where a definition comes from. Project precedence for these three is assumed from how Claude Code resolves names, not observed. On a machine without a user-level install, check that the three names are listed at all.
- The other four reviewer roles were listed with the restricted tools but not launched.

## Updating

Fetch the same paths at a newer revision, re-apply the `tools:` line to the six reviewer roles, and update the revision and hashes in this file in the same commit.

## Local change: automatic delegation (2026-11-22)

One sentence beginning "Use proactively" was appended to the `description:` line of every Agency Agents role in `.claude/agents/` (not to `loop-verifier`). Claude Code uses that field to decide when to delegate, so the roles now run during ticket work without being named. Nothing else in the role files changed.

This supersedes any statement above that a role file is unmodified or that the `tools:` line is the only local change. To compare a role with the pinned upstream file, remove that sentence (and the `tools:` line where one was added) first.

The steps at which each role runs are in `.claude/skills/implement-ticket/SKILL.md`.
