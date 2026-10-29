from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from .models import CalendarItem, DayBrief, InboxItem, TaskItem, TimeBlock


def build_brief(
    *,
    timezone_name: str,
    calendar: list[CalendarItem],
    inbox: list[InboxItem],
    tasks: list[TaskItem],
    errors,
    include_timeblocks: bool,
) -> DayBrief:
    tz = ZoneInfo(timezone_name)
    now = datetime.now(tz)
    calendar = sorted(
        [
            item.model_copy(
                update={
                    "start_at": item.start_at.astimezone(tz),
                    "end_at": item.end_at.astimezone(tz),
                }
            )
            for item in calendar
            if item.start_at.astimezone(tz).date() == now.date()
        ],
        key=lambda item: item.start_at,
    )
    priorities = suggest_priorities(calendar, inbox, tasks)
    timeblocks = suggest_timeblocks(now, calendar, inbox, tasks) if include_timeblocks else []
    return DayBrief(
        timezone=timezone_name,
        generated_at=now,
        calendar=calendar,
        inbox=inbox,
        tasks=tasks,
        source_errors=errors,
        priorities=priorities,
        timeblocks=timeblocks,
    )


def suggest_priorities(
    calendar: list[CalendarItem], inbox: list[InboxItem], tasks: list[TaskItem]
) -> list[str]:
    priorities: list[str] = []
    if calendar:
        priorities.append(f"Protect the fixed schedule: {len(calendar)} calendar item(s) today.")
    unread = [item for item in inbox if not item.is_read]
    high = [item for item in inbox if item.importance.lower() == "high"]
    if high:
        priorities.append(f"Review {len(high)} high-importance inbox item(s).")
    elif unread:
        priorities.append(f"Triage {min(len(unread), 10)} unread/recent inbox item(s).")
    important_tasks = [item for item in tasks if item.is_important]
    if important_tasks:
        priorities.append(f"Advance important task: {important_tasks[0].subject}.")
    elif tasks:
        priorities.append(f"Pick one open task to move forward: {tasks[0].subject}.")
    return priorities[:4]


def suggest_timeblocks(
    now: datetime,
    calendar: list[CalendarItem],
    inbox: list[InboxItem],
    tasks: list[TaskItem],
) -> list[TimeBlock]:
    day_start = datetime.combine(now.date(), time(8, 30), tzinfo=now.tzinfo)
    day_end = datetime.combine(now.date(), time(17, 0), tzinfo=now.tzinfo)
    cursor = max(now.replace(second=0, microsecond=0), day_start)
    blocks: list[TimeBlock] = []
    fixed = [
        item
        for item in sorted(calendar, key=lambda event: event.start_at)
        if item.end_at > cursor and item.start_at.date() == now.date()
    ]
    for event in fixed:
        if event.start_at - cursor >= timedelta(minutes=45):
            blocks.extend(_blocks_for_gap(cursor, event.start_at, inbox, tasks))
        cursor = max(cursor, event.end_at + timedelta(minutes=15))
    if day_end - cursor >= timedelta(minutes=45):
        blocks.extend(_blocks_for_gap(cursor, day_end, inbox, tasks))
    return blocks[:4]


def _blocks_for_gap(
    start: datetime,
    end: datetime,
    inbox: list[InboxItem],
    tasks: list[TaskItem],
) -> list[TimeBlock]:
    duration = end - start
    if duration < timedelta(minutes=45):
        return []
    if inbox:
        mail_end = min(start + timedelta(minutes=30), end)
        return [
            TimeBlock(
                start_at=start,
                end_at=mail_end,
                label="Inbox triage",
                rationale=(
                    f"Clear the top {min(len(inbox), 10)} unread/recent messages "
                    "before deeper work."
                ),
            )
        ]
    label = "Focused work"
    rationale = "Use this open block for the highest-priority task."
    if tasks:
        label = "Task focus"
        rationale = tasks[0].subject
    return [TimeBlock(start_at=start, end_at=end, label=label, rationale=rationale)]
