# Agent Notes

This repo contains a read-only daily brief CLI for local Midtown operator workflows.

- Preserve read-only behavior unless the user explicitly asks for mutation.
- Do not add calendar, mail, To Do, PSA, or ticket mutations to the default brief path.
- Keep child tool calls explicit and JSON-based.
- Avoid storing live report output, customer data, access tokens, or local cache files in the repo.
- Run `.\scripts\smoke.ps1` before claiming the repo is healthy.

## Secret gate before publication

Before publishing the current PR branch, commit the complete candidate and run
`python3 scripts/secret_gate.py --base origin/main` (native Windows: `python`). Require exit 0;
missing tooling/authentication, scan errors and skipped scans block publication.
Then run the existing repository gates. Repeat after changing outgoing commits.
Push exactly the scanned HEAD. This PR scan covers the current branch against its
fetched intended base; other refs, multi-ref pushes and rewritten history require
`--pre-push` with Git's complete ref-update stream. Stop if any pushed ref is
uncovered. See [secret scanning](SECRET-SCANNING.md) for base selection, new branches,
pre-push input and prerequisites. Preserve GitGuardian App, CI and Gitleaks checks.

For a non-default PR target, fetch its destination and pass that exact ref to
`--base`; the remote default is not a substitute for a release/maintenance base.

The secret gate requires Python 3.11+ and approved ggshield >=1.56.1,<2.
