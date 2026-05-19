# Architecture

`day-brief` is an orchestration CLI. It does not call Microsoft Graph directly.

## Flow

1. `day_brief.sources.SourceCollector` shells out to local read-only toys with `--output json`.
2. Child tool JSON is normalized into Pydantic models.
3. `day_brief.planner` filters the local-day calendar, chooses watchlist priorities, and optionally suggests advisory timeblocks.
4. `day_brief.render` emits Markdown or JSON.

## Read-Only Boundary

The default command path only reads:

- `calendar-glance agenda`
- `mail-triage inbox`
- `todo list`

Timeblocks are suggestions only. They are not written to a calendar.

## Failure Model

Each source is isolated. If one child tool fails, the brief still renders and lists the failed source under `Needs Evidence`.
