# Trading Research System 0.3.0 Smoke

This runbook verifies the smallest useful product path. It is not a private
runtime rehearsal and it never performs broker or order actions.

## Automated Check

```bash
bash scripts/verify-skill.sh
```

The default gate checks only syntax, portable Skill distribution, canonical
Broker-Live product knowledge, Private Runtime preparation/health, the stable
`ResearchResult -> DeliveryPacket` contract, retained ArtifactPacket behavior,
and Skill structure. It does not launch a browser or export an artifact.

## Human Acceptance

1. Generate one representative Macro, Instrument, Portfolio, or Price Action
   `ResearchResult` delivery.
2. Render the returned inline fragment in the actual Codex chat surface.
3. Confirm the first viewport shows decision-relevant numbers and a usable
   interactive chart when quantitative evidence exists.
4. Confirm gaps, source time, privacy, and the no-order boundary remain visible.
5. Record the user's acceptance or feedback before public cutover.

Do not run screenshot matrices, pixel diffs, broad browser combinations, or
legacy runtime fixture suites by default. Add a focused test only when a
specific regression or safety risk requires it.

## Safety Boundary

- public fixtures only;
- no private runtime or account database deletion;
- no live broker reads;
- no network call from an opened artifact;
- no order creation, modification, cancellation, or implied approval.
