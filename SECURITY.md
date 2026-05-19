# Security Policy

## Reporting

Report security concerns privately to Midtown Technology Group maintainers. Do not open public issues for secrets, tenant data, customer data, or exploitable findings.

## Scope

`day-brief` is a read-only local operator tool. It shells out to existing Midtown toys and summarizes calendar, mail, and task metadata. It must not mutate calendar events, mail, tasks, tickets, or external systems.

## Data Handling

- Do not commit tokens, exported mailbox data, calendar payloads, or task dumps.
- Keep generated reports local unless they have been reviewed for customer-sensitive content.
- Prefer source tool links and compact metadata over copying long message bodies.
