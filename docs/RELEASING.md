# Releasing

Only the owner releases. Agents never tag, publish or create a release.

## What a release is here

This is a small private tool run from a checkout. There is no package, installer or deployment. A release is a Git tag on a commit of `main` plus the matching `CHANGELOG.md` section.

## Before tagging

1. Every pull request for the release is merged and CI is green on `main` (Linux and Windows jobs).
2. On the release commit, run `python -m unittest discover -s tests -v` and note the `Ran N tests` line and `OK`. If `test_b07_content_type_and_length` fails with `ConnectionAbortedError` on Windows, that is the known intermittent defect (issue #9): rerun once and record both results.
3. Run `python -m case_study_builder --data-dir ./demo-data --port 0`, open the printed address, save a case study, stop the server (Ctrl+C) and start it again to check the case study returns unchanged. Delete `./demo-data` afterwards; it is ignored by Git and must never be committed.
4. Move the `Unreleased` entries in `CHANGELOG.md` under a new version heading with the date, and commit that change through a pull request.

## Tagging

From an up-to-date `main`: `git tag -a vX.Y.Z -m "vX.Y.Z"` and `git push origin vX.Y.Z`. Create the GitHub release from the tag with the changelog section as its notes.
