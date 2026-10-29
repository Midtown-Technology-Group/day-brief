from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
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
        key=lambda item: item.start_at.timestamp(),
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
    # Keep local workday boundaries, but compare and add elapsed durations in UTC.
    # Same-ZoneInfo datetime arithmetic ignores fold during a repeated hour.
    day_start = datetime.combine(now.date(), time(8, 30), tzinfo=now.tzinfo).astimezone(
        timezone.utc
    )
    day_end = datetime.combine(now.date(), time(17, 0), tzinfo=now.tzinfo).astimezone(timezone.utc)
    cursor = max(now.replace(second=0, microsecond=0).astimezone(timezone.utc), day_start)
    blocks: list[TimeBlock] = []
    fixed = [
        item
        for item in sorted(calendar, key=lambda event: event.start_at.timestamp())
        if item.end_at.astimezone(timezone.utc) > cursor
        and item.start_at.astimezone(timezone.utc) < day_end
        and item.start_at.astimezone(now.tzinfo).date() == now.date()
    ]
    for event in fixed:
        event_start = event.start_at.astimezone(timezone.utc)
        event_end = event.end_at.astimezone(timezone.utc)
        if event_start - cursor >= timedelta(minutes=45):
            blocks.extend(_blocks_for_gap(cursor, event_start, inbox, tasks))
        cursor = max(cursor, event_end + timedelta(minutes=15))
    if day_end - cursor >= timedelta(minutes=45):
        blocks.extend(_blocks_for_gap(cursor, day_end, inbox, tasks))
    return [
        block.model_copy(
            update={
                "start_at": block.start_at.astimezone(now.tzinfo),
                "end_at": block.end_at.astimezone(now.tzinfo),
            }
        )
        for block in blocks[:4]
    ]


def _blocks_for_gap(
    start: datetime,
    end: datetime,
    inbox: list[InboxItem],
    tasks: list[TaskItem],
) -> list[TimeBlock]:
    utc_start = start.astimezone(timezone.utc)
    utc_end = end.astimezone(timezone.utc)
    duration = utc_end - utc_start
    if duration < timedelta(minutes=45):
        return []
    if inbox:
        mail_end = min(utc_start + timedelta(minutes=30), utc_end).astimezone(start.tzinfo)
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
