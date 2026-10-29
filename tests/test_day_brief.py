from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from typer.testing import CliRunner

from day_brief import planner
from day_brief.cli import app
from day_brief.models import CalendarItem, InboxItem, TaskItem
from day_brief.planner import _blocks_for_gap, build_brief, suggest_timeblocks
from day_brief.render import render_markdown

FROZEN_NOW = datetime(2026, 10, 13, 12, 0, tzinfo=ZoneInfo("America/Indiana/Indianapolis"))


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return FROZEN_NOW.astimezone(tz)


@pytest.fixture
def frozen_clock(monkeypatch):
    monkeypatch.setattr(planner, "datetime", FrozenDatetime)


class FakeCollector:
    def collect(self, *, days: int, mail_limit: int, task_limit: int):
        today = FROZEN_NOW.replace(hour=9, minute=0)
        return (
            [
                CalendarItem(
                    title="Standup",
                    start_at=today,
                    end_at=today + timedelta(minutes=30),
                )
            ],
            [InboxItem(subject="Needs review", sender="Alex", is_read=False)],
            [TaskItem(subject="Ship the daily brief")],
            [],
        )


def test_markdown_includes_schedule_watchlist_and_timeblocks():
    tz = "America/Indiana/Indianapolis"
    brief = build_brief(
        timezone_name=tz,
        calendar=[],
        inbox=[InboxItem(subject="Needs review", sender="Alex", is_read=False)],
        tasks=[TaskItem(subject="Ship the daily brief")],
        errors=[],
        include_timeblocks=True,
    )

    output = render_markdown(brief)

    assert "Here's Your Day" in output
    assert "Inbox triage" in output
    assert "Needs review" in output
    assert "Ship the daily brief" in output


def test_cli_renders_json_from_collector(monkeypatch, frozen_clock):
    monkeypatch.setattr("day_brief.cli.SourceCollector", lambda: FakeCollector())
    monkeypatch.setattr("day_brief.cli.get_localzone_name", lambda: "America/Indiana/Indianapolis")
    runner = CliRunner()

    result = runner.invoke(app, ["brief", "--output", "json", "--timeblocks"])

    assert result.exit_code == 0
    assert '"timezone": "America/Indiana/Indianapolis"' in result.stdout
    assert '"title": "Standup"' in result.stdout
    assert '"subject": "Needs review"' in result.stdout


def test_cli_keeps_brief_subcommand(monkeypatch, frozen_clock):
    monkeypatch.setattr("day_brief.cli.SourceCollector", lambda: FakeCollector())
    monkeypatch.setattr("day_brief.cli.get_localzone_name", lambda: "America/Indiana/Indianapolis")
    runner = CliRunner()

    result = runner.invoke(app, ["brief", "--output", "markdown"])

    assert result.exit_code == 0
    assert "Here's Your Day" in result.stdout


def test_brief_filters_calendar_to_local_today():
    tz = ZoneInfo("America/Indiana/Indianapolis")
    brief = build_brief(
        timezone_name="America/Indiana/Indianapolis",
        calendar=[
            CalendarItem(
                title="Today",
                start_at=datetime.now(tz).replace(hour=12, minute=0, second=0, microsecond=0),
                end_at=datetime.now(tz).replace(hour=13, minute=0, second=0, microsecond=0),
            ),
            CalendarItem(
                title="Tomorrow",
                start_at=datetime.now(tz).replace(hour=10, minute=0, second=0, microsecond=0)
                + timedelta(days=1),
                end_at=datetime.now(tz).replace(hour=11, minute=0, second=0, microsecond=0)
                + timedelta(days=1),
            ),
        ],
        inbox=[],
        tasks=[],
        errors=[],
        include_timeblocks=False,
    )

    assert [item.title for item in brief.calendar] == ["Today"]


@pytest.mark.parametrize(
    "source_start",
    ["2026-10-13T18:00:00+00:00", "2026-10-14T08:00:00+14:00"],
)
def test_brief_normalizes_calendar_to_requested_timezone(frozen_clock, source_start):
    start = datetime.fromisoformat(source_start)
    event = CalendarItem(
        title="Afternoon meeting", start_at=start, end_at=start + timedelta(minutes=30)
    )
    brief = build_brief(
        timezone_name="America/Indiana/Indianapolis",
        calendar=[event],
        inbox=[],
        tasks=[],
        errors=[],
        include_timeblocks=True,
    )

    assert "- 2:00 PM - 2:30 PM: Afternoon meeting" in render_markdown(brief)
    assert brief.calendar[0].start_at.isoformat() == "2026-10-13T14:00:00-04:00"
    assert [(block.start_at.hour, block.end_at.hour) for block in brief.timeblocks] == [
        (12, 14), (14, 17)
    ]
    assert brief.timeblocks[1].start_at.minute == 45
    assert event.start_at == start
    assert event.start_at.utcoffset() == start.utcoffset()


@pytest.mark.parametrize("hour", [16, 17, 18])
@pytest.mark.parametrize("has_inbox", [False, True])
def test_evening_meetings_do_not_extend_suggested_workday(hour, has_inbox):
    now = FROZEN_NOW.replace(hour=hour)
    evening = CalendarItem(
        title="Evening meeting",
        start_at=now.replace(hour=20),
        end_at=now.replace(hour=21),
    )

    blocks = suggest_timeblocks(
        now,
        [evening],
        [InboxItem(subject="Review", sender="Alex")] if has_inbox else [],
        [],
    )

    if hour >= 17:
        assert blocks == []
    else:
        assert len(blocks) == 1
        assert blocks[0].start_at == now
        expected_end = now.replace(hour=16, minute=30) if has_inbox else now.replace(hour=17)
        assert blocks[0].end_at == expected_end


def test_brief_sorts_repeated_hour_by_instant(monkeypatch, frozen_clock):
    tz = ZoneInfo("America/Indiana/Indianapolis")
    monkeypatch.setattr(__name__ + ".FROZEN_NOW", datetime(2026, 11, 1, 12, tzinfo=tz))
    first = CalendarItem(
        title="First hour",
        start_at="2026-11-01T01:45:00-04:00",
        end_at="2026-11-01T01:50:00-04:00",
    )
    second = CalendarItem(
        title="Second hour",
        start_at="2026-11-01T01:15:00-05:00",
        end_at="2026-11-01T01:20:00-05:00",
    )
    brief = build_brief(
        timezone_name=tz.key, calendar=[second, first], inbox=[], tasks=[],
        errors=[], include_timeblocks=True,
    )
    assert [item.title for item in brief.calendar] == ["First hour", "Second hour"]
    assert [item.start_at.fold for item in brief.calendar] == [0, 1]


@pytest.mark.parametrize("has_inbox", [False, True])
def test_gap_uses_elapsed_time_across_repeated_hour(has_inbox):
    tz = ZoneInfo("America/Indiana/Indianapolis")
    start = datetime(2026, 11, 1, 1, 45, tzinfo=tz, fold=0)
    end = datetime(2026, 11, 1, 1, 30, tzinfo=tz, fold=1)
    blocks = _blocks_for_gap(
        start, end, [InboxItem(subject="Review", sender="Alex")] if has_inbox else [], []
    )
    assert len(blocks) == 1
    assert blocks[0].start_at.timestamp() == start.timestamp()
    assert blocks[0].end_at.timestamp() == start.timestamp() + (1800 if has_inbox else 2700)
    assert blocks[0].end_at.fold == 1


@pytest.mark.parametrize("minute,fold", [(50, 0), (5, 1)])
def test_timeblocks_preserve_elapsed_buffers_during_repeated_hour(monkeypatch, minute, fold):
    tz = ZoneInfo("America/Indiana/Indianapolis")
    # Move the work window over the real DST transition to exercise planner arithmetic.
    monkeypatch.setattr(planner, "time", lambda hour, minute: time(0, 30) if hour == 8 else time(3))
    now = datetime(2026, 11, 1, 1, minute, tzinfo=tz, fold=fold)
    events = [
        CalendarItem(
            title="Second hour", start_at=datetime(2026, 11, 1, 1, 15, tzinfo=tz, fold=1),
            end_at=datetime(2026, 11, 1, 1, 20, tzinfo=tz, fold=1),
        ),
        CalendarItem(
            title="First hour", start_at=datetime(2026, 11, 1, 1, 45, tzinfo=tz),
            end_at=datetime(2026, 11, 1, 1, 55, tzinfo=tz),
        ),
    ]
    blocks = suggest_timeblocks(now, events, [], [])
    assert len(blocks) == 1
    expected = datetime(2026, 11, 1, 1, 35, tzinfo=tz, fold=1)
    assert blocks[0].start_at.timestamp() == expected.timestamp()
    assert blocks[0].end_at.timestamp() == datetime(2026, 11, 1, 3, tzinfo=tz).timestamp()
