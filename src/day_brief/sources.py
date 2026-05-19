from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .models import BriefSourceError, CalendarItem, InboxItem, TaskItem

ROOT = Path(r"C:\Users\ThomasBray\src\Midtown-Technology-Group")


class SourceCollector:
    def __init__(
        self,
        calendar_cmd: Path | None = None,
        mail_cmd: Path | None = None,
        todo_cmd: Path | None = None,
    ) -> None:
        self.calendar_cmd = calendar_cmd or Path(
            os.environ.get("DAY_BRIEF_CALENDAR", ROOT / "calendar-glance" / "invoke.ps1")
        )
        self.mail_cmd = mail_cmd or Path(
            os.environ.get("DAY_BRIEF_MAIL", ROOT / "mail-triage" / "invoke.ps1")
        )
        self.todo_cmd = todo_cmd or Path(
            os.environ.get("DAY_BRIEF_TODO", ROOT / "todo" / "invoke.ps1")
        )

    def collect(
        self,
        *,
        days: int,
        mail_limit: int,
        task_limit: int,
    ) -> tuple[list[CalendarItem], list[InboxItem], list[TaskItem], list[BriefSourceError]]:
        errors: list[BriefSourceError] = []
        calendar = self._safe("calendar", lambda: self.calendar(days))
        inbox = self._safe("inbox", lambda: self.inbox(mail_limit))
        tasks = self._safe("tasks", lambda: self.tasks(task_limit))
        for _source, value in [calendar, inbox, tasks]:
            if isinstance(value, BriefSourceError):
                errors.append(value)
        return (
            calendar[1] if not isinstance(calendar[1], BriefSourceError) else [],
            inbox[1] if not isinstance(inbox[1], BriefSourceError) else [],
            tasks[1] if not isinstance(tasks[1], BriefSourceError) else [],
            errors,
        )

    def _safe(self, source: str, func):
        try:
            return source, func()
        except Exception as exc:
            return source, BriefSourceError(source=source, message=str(exc))

    def calendar(self, days: int) -> list[CalendarItem]:
        rows = self._run_json(
            self.calendar_cmd,
            ["--output", "json", "agenda", "--days", str(days)],
        )
        return [
            CalendarItem(
                title=row.get("subject") or "(no subject)",
                start_at=row["start_at"],
                end_at=row["end_at"],
                location=row.get("location"),
                organizer=row.get("organizer"),
            )
            for row in rows
        ]

    def inbox(self, limit: int) -> list[InboxItem]:
        rows = self._run_json(self.mail_cmd, ["--output", "json", "inbox", "--limit", str(limit)])
        interesting = []
        for row in rows:
            if row.get("is_read") and str(row.get("importance", "normal")).lower() != "high":
                continue
            interesting.append(
                InboxItem(
                    subject=row.get("subject") or "(no subject)",
                    sender=row.get("sender") or row.get("sender_address") or "(unknown)",
                    received_at=row.get("received_at"),
                    is_read=bool(row.get("is_read")),
                    importance=row.get("importance") or "normal",
                )
            )
        return interesting[:limit]

    def tasks(self, limit: int) -> list[TaskItem]:
        rows = self._run_json(self.todo_cmd, ["--output", "json", "list", "--all"])
        open_items = []
        for row in rows:
            if row.get("is_completed"):
                continue
            open_items.append(
                TaskItem(
                    subject=row.get("subject") or "(no subject)",
                    created_at=row.get("created"),
                    status=row.get("status") or "notStarted",
                    is_important=bool(row.get("is_important")),
                )
            )
        return open_items[:limit]

    def _run_json(self, command: Path, args: list[str]) -> list[dict[str, Any]]:
        if not command.exists():
            raise FileNotFoundError(f"{command} not found")
        result = subprocess.run(
            self._command_line(command, args),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(detail or f"{command.name} exited {result.returncode}")
        payload = json.loads(result.stdout or "[]")
        if not isinstance(payload, list):
            raise RuntimeError(f"{command.name} returned non-list JSON")
        return payload

    def _command_line(self, command: Path, args: list[str]) -> list[str]:
        if platform.system() == "Windows" and command.suffix.lower() == ".ps1":
            pwsh = shutil.which("pwsh") or shutil.which("powershell")
            if not pwsh:
                raise RuntimeError("PowerShell not found")
            return [pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(command), *args]
        return [str(command), *args]
