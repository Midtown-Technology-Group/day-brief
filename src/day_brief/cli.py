from __future__ import annotations

import os

import typer
from tzlocal import get_localzone_name

from .planner import build_brief
from .render import render_json, render_markdown
from .sources import SourceCollector

app = typer.Typer(help="Read-only day brief and timeblock suggestions.")


def default_timezone() -> str:
    return os.environ.get("DAY_BRIEF_TIMEZONE") or get_localzone_name() or "UTC"


@app.callback()
def root() -> None:
    """Read-only day brief and timeblock suggestions."""


@app.command("brief")
def brief(
    output: str = typer.Option("markdown", "--output", "-o", help="markdown or json"),
    days: int = typer.Option(1, "--days", min=1, max=3),
    mail_limit: int = typer.Option(40, "--mail-limit", min=0, max=200),
    task_limit: int = typer.Option(20, "--task-limit", min=0, max=100),
    timeblocks: bool = typer.Option(False, "--timeblocks", help="Suggest advisory timeblocks."),
    timezone_name: str | None = typer.Option(
        None,
        "--timezone",
        "-z",
        help="IANA timezone for rendered times. Defaults to this machine's timezone.",
    ),
) -> None:
    collector = SourceCollector()
    calendar, inbox, tasks, errors = collector.collect(
        days=days,
        mail_limit=mail_limit,
        task_limit=task_limit,
    )
    report = build_brief(
        timezone_name=timezone_name or default_timezone(),
        calendar=calendar,
        inbox=inbox,
        tasks=tasks,
        errors=errors,
        include_timeblocks=timeblocks,
    )
    if output == "json":
        typer.echo(render_json(report))
        return
    if output != "markdown":
        raise typer.BadParameter("--output must be markdown or json")
    typer.echo(render_markdown(report))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
