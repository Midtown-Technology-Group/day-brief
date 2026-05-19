# Day Brief

Read-only daily brief and timeblock suggestions for Midtown operators.

## Usage

```powershell
.\invoke.ps1 brief
.\invoke.ps1 brief --timeblocks
.\invoke.ps1 brief --output json
```

The CLI reads existing local toys by default:

- `calendar-glance` for the fixed schedule
- `mail-triage` for recent inbox signals
- `todo` for open tasks

It does not mutate mail, tasks, tickets, or calendars.

## Health Checks

```powershell
.\scripts\smoke.ps1
```

The smoke script runs lint, tests, and a no-mail/no-task JSON brief check.

## Configuration

Override tool paths when needed:

```powershell
$env:DAY_BRIEF_CALENDAR='C:\Users\ThomasBray\src\Midtown-Technology-Group\calendar-glance\invoke.ps1'
$env:DAY_BRIEF_MAIL='C:\Users\ThomasBray\src\Midtown-Technology-Group\mail-triage\invoke.ps1'
$env:DAY_BRIEF_TODO='C:\Users\ThomasBray\src\Midtown-Technology-Group\todo\invoke.ps1'
```

Times render in the machine-local timezone unless `--timezone` is provided.
