from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from typer.testing import CliRunner

from day_brief.cli import app
from day_brief.models import CalendarItem, InboxItem, TaskItem
from day_brief.planner import build_brief
from day_brief.render import render_markdown


class FakeCollector:
    def collect(self, *, days: int, mail_limit: int, task_limit: int):
        tz = ZoneInfo("America/Indianapolis")
        today = datetime.now(tz).replace(hour=9, minute=0, second=0, microsecond=0)
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
    tz = "America/Indianapolis"
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


def test_cli_renders_json_from_collector(monkeypatch):
    monkeypatch.setattr("day_brief.cli.SourceCollector", lambda: FakeCollector())
    monkeypatch.setattr("day_brief.cli.get_localzone_name", lambda: "America/Indianapolis")
    runner = CliRunner()

    result = runner.invoke(app, ["brief", "--output", "json", "--timeblocks"])

    assert result.exit_code == 0
    assert '"timezone": "America/Indianapolis"' in result.stdout
    assert '"title": "Standup"' in result.stdout
    assert '"subject": "Needs review"' in result.stdout


def test_cli_keeps_brief_subcommand(monkeypatch):
    monkeypatch.setattr("day_brief.cli.SourceCollector", lambda: FakeCollector())
    monkeypatch.setattr("day_brief.cli.get_localzone_name", lambda: "America/Indianapolis")
    runner = CliRunner()

    result = runner.invoke(app, ["brief", "--output", "markdown"])

    assert result.exit_code == 0
    assert "Here's Your Day" in result.stdout


def test_brief_filters_calendar_to_local_today():
    tz = ZoneInfo("America/Indianapolis")
    brief = build_brief(
        timezone_name="America/Indianapolis",
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
