# Runnability

## Windows

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
.\scripts\smoke.ps1
```

## Live Local Brief

The live brief expects these sibling repos to exist:

- `..\calendar-glance`
- `..\mail-triage`
- `..\todo`

It also expects Microsoft Graph auth to be warmed through `mtg-auth login`.

```powershell
.\invoke.ps1 brief --timeblocks
```
