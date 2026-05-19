# Agent Notes

This repo contains a read-only daily brief CLI for local Midtown operator workflows.

- Preserve read-only behavior unless the user explicitly asks for mutation.
- Do not add calendar, mail, To Do, PSA, or ticket mutations to the default brief path.
- Keep child tool calls explicit and JSON-based.
- Avoid storing live report output, customer data, access tokens, or local cache files in the repo.
- Run `.\scripts\smoke.ps1` before claiming the repo is healthy.
