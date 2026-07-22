# Canonical Board Human Review Gate

Human review is mandatory after the automated visual acceptance gate passes.
It cannot waive, downgrade, or override an automated failure.

## Preconditions

- The acceptance report records `automated_status: pass` for the 60 complete,
  90 degraded, 48 dark, and 12 Gallery cases. Its `release_status` remains
  `pending_human_review` until the real Codex inline evidence is validated.
- The reviewed HTML files are exact-byte copies of the three complete staged
  Gallery artifacts. Record their SHA-256 values before opening them.
- No public README or legacy SVG path has been changed. Public cutover remains
  a separate Issue 57 action.

## Browser Review

- Review every staged Gallery PNG at its recorded dimensions.
- Confirm Board identity, selected view, evidence state, source/as-of labels,
  decision posture, gaps, and synthetic-fixture disclosure are legible.
- Confirm narrow and dark captures have no overlap, clipping, hidden critical
  content, unreadable labels, or accidental horizontal scrolling.
- Confirm charts are nonblank and support the Board decision rather than replace
  its evidence model.

## Standalone Board Smoke

For each complete Board artifact:

1. Open the exact `research-brief.html` bytes directly over localhost.
2. Confirm Overview is the default view.
3. Switch every view with pointer and keyboard input.
4. Confirm selected state, visible focus, narrow reflow, no page error, and no
   external request.
5. Record the direct-open result and the sibling snapshot/manifest hashes. An
   iframe, host-styled fragment, or separately authored wrapper is not evidence.

The evidence file is local release evidence. Do not commit user identifiers,
session URLs, private paths, account data, or broker/runtime output.

## Sign-off

- Reviewer name or stable public handle is present.
- Review timestamp is UTC RFC 3339.
- Each recorded HTML hash matches the staged Gallery manifest.
- Any visual concern becomes a failing issue or code-review finding. Do not mark
  the release gate passed until it is fixed and the affected checks are rerun.
