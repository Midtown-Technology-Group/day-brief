from __future__ import annotations

import json

from .models import DayBrief


def render_json(brief: DayBrief) -> str:
    return json.dumps(brief.model_dump(mode="json"), indent=2)


def render_markdown(brief: DayBrief) -> str:
    lines: list[str] = []
    date_label = (
        f"{brief.generated_at.strftime('%A, %B')} "
        f"{brief.generated_at.day}, {brief.generated_at.year}"
    )
    lines.append(f"# Here's Your Day ({date_label})")
    lines.append("")
    lines.append(f"_Timezone: {brief.timezone}_")
    lines.append("")
    if brief.source_errors:
        lines.append("## Needs Evidence")
        for error in brief.source_errors:
            lines.append(f"- {error.source}: {error.message.splitlines()[0]}")
        lines.append("")
    lines.append("## Fixed Schedule")
    if brief.calendar:
        for item in brief.calendar:
            lines.append(
                f"- {_time(item.start_at)} - {_time(item.end_at)}: {item.title}"
            )
    else:
        lines.append("- No calendar items found.")
    lines.append("")
    lines.append("## Watchlist")
    if brief.priorities:
        for priority in brief.priorities:
            lines.append(f"- {priority}")
    else:
        lines.append("- Nothing urgent surfaced from the enabled sources.")
    lines.append("")
    lines.append("## Inbox Signals")
    if brief.inbox:
        for item in brief.inbox[:8]:
            lines.append(f"- {item.sender}: {item.subject}")
    else:
        lines.append("- No unread/high-signal inbox items returned.")
    lines.append("")
    lines.append("## Open Tasks")
    if brief.tasks:
        for item in brief.tasks[:8]:
            prefix = "!" if item.is_important else "-"
            lines.append(f"{prefix} {item.subject}")
    else:
        lines.append("- No open tasks returned.")
    if brief.timeblocks:
        lines.append("")
        lines.append("## Suggested Timeblocks")
        for block in brief.timeblocks:
            lines.append(
                f"- {_time(block.start_at)} - {_time(block.end_at)}: "
                f"{block.label} ({block.rationale})"
            )
    return "\n".join(lines)


def _time(value) -> str:
    return value.strftime("%I:%M %p").lstrip("0")
