import datetime
import json
from pathlib import Path
from typing import Optional
from typing_extensions import Annotated

from pyminder.pyminder import Pyminder
import typer
from rich import print


app = typer.Typer()

# Import config from ~/.config/beetimer/config.json
config_path = Path.home() / ".config" / "beetimer" / "config.json"
if not config_path.exists():
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.touch()
    CONFIG = {}
    with open(config_path, "w") as f:
        json.dump(CONFIG, f)
else:
    with open(config_path) as f:
        CONFIG = json.load(f)


@app.command()
def auth(username):
    """Ask for auth token and save it in config."""
    token = typer.prompt("API Token (will be stored in plaintext)", hide_input=True).strip()
    pyminder = Pyminder(user=username, token=token)
    try:
        pyminder.get_goals()
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)
    typer.echo("Success!")
    CONFIG["auth_token"] = token
    CONFIG["username"] = username
    with open(config_path, "w") as f:
        json.dump(CONFIG, f)


@app.command()
def config(settings: Optional[str] = typer.Argument(None)):
    """Set config settings.
    k:v paris in the form "k:v,k2:v2"
    """
    if settings:
        settings = dict([s.split(":") for s in settings.split(",")])
        for k, v in settings.items():
            CONFIG[k] = v
        with open(config_path, "w") as f:
            json.dump(CONFIG, f)

    print(CONFIG)


@app.command()
def goals():
    """List goals."""
    pyminder = Pyminder(user=CONFIG["username"], token=CONFIG["auth_token"])
    goals = pyminder.get_goals()
    for goal in goals:
        print_goal(goal)


def print_goal(goal):
    print(
        f"[bold]{goal.slug}[/bold]\n"
        f" {goal.title}\n"
        f" {goal.safesum}\n"
    )


@app.command()
def start(slug: str, time_format: Annotated[str, typer.Option("--time-format", "-F")] = ""):
    """Start a timer for a goal."""
    # Create a file in ~/.config/beetimer/<slug>.json
    goal_path = Path.home() / ".config" / "beetimer" / f"{slug}.json"
    if goal_path.exists():
        typer.echo(f"Goal {slug} already started.")
        raise typer.Exit(1)

    pyminder = Pyminder(user=CONFIG["username"], token=CONFIG["auth_token"])
    goal = pyminder.get_goal(slug)
    if goal is None:
        typer.echo(f"Goal {slug} not found.")
        raise typer.Exit(1)

    if not time_format:
        time_format = CONFIG["time"]

    with open(goal_path, "w") as f:
        json.dump(
            {
                "start": datetime.datetime.now().isoformat(),
                "time_format": time_format,
            }, f
        )

    typer.echo(f"Started timer for {slug}.")


@app.command()
def status(slug: str):
    """Show status for a goal."""
    goal = load_goal_file(slug)

    start = datetime.datetime.fromisoformat(goal["start"])
    if "stop" in goal:
        now = datetime.datetime.fromisoformat(goal["stop"])
    else:
        now = datetime.datetime.now()
    delta = now - start

    typer.echo(f"Goal: {slug}")
    typer.echo(f"Start: {start.strftime(goal['time_format'])}")
    typer.echo(f"Elapsed: {delta}")

    points = get_points(goal)

    typer.echo(f"Points: {points:.2f}")


def load_goal_file(slug):
    goal_path = Path.home() / ".config" / "beetimer" / f"{slug}.json"
    if not goal_path.exists():
        typer.echo(f"Goal {slug} not started.")
        raise typer.Exit(1)

    with open(goal_path) as f:
        goal = json.load(f)

    return goal


def get_points(goal):
    start = datetime.datetime.fromisoformat(goal["start"])
    if "stop" in goal:
        now = datetime.datetime.fromisoformat(goal["stop"])
    else:
        now = datetime.datetime.now()
    delta = now - start

    # Calculate the points earned
    if "hour" in goal["time_format"]:
        points = delta.seconds / 3600
    elif "minute" in goal["time_format"]:
        points = delta.seconds / 60

    return points


@app.command()
def stop(slug: str, force_upload: Annotated[bool, typer.Option("--force-upload", "-f")] = False):
    """Stop a timer for a goal."""
    goal = load_goal_file(slug)
    goal_path = Path.home() / ".config" / "beetimer" / f"{slug}.json"

    start = datetime.datetime.fromisoformat(goal["start"])
    if "stop" in goal:
        typer.echo(f"Goal {slug} already stopped.")
        raise typer.Exit(1)
    now = datetime.datetime.now()
    delta = now - start

    points = get_points(goal)

    goal["stop"] = now.isoformat()

    print(f"Goal: {slug}")
    print(f"Start: {start.isoformat()}")
    print(f"Stop: {now.isoformat()}")
    print(f"Elapsed: {delta}")
    print(f"Points: {points:.2f}")

    with open(goal_path, "w") as f:
        json.dump(goal, f)

    # Confirm upload
    if force_upload:
        _upload(slug, points)
        # Delete the goal file
        goal_path.unlink()
        return

    if typer.confirm("Upload points to Beeminder?"):
        _upload(slug, points)
        # Delete the goal file
        goal_path.unlink()
        return

    print("Goal not uploaded. File saved. Upload with `beetimer upload`. Delete with `beetimer delete`.")


@app.command()
def upload(slug: str):
    """Upload a goal."""
    goal = load_goal_file(slug)
    goal_path = Path.home() / ".config" / "beetimer" / f"{slug}.json"

    points = get_points(goal)

    print(f"Goal: {slug}, Points: {points:.2f}. Uploading...")

    _upload(slug, points)

    # Confirm delete
    if not typer.confirm("Delete goal file?"):
        return

    # Delete the goal file
    goal_path.unlink()


def _upload(slug, points):
    pyminder = Pyminder(user=CONFIG["username"], token=CONFIG["auth_token"])
    pyminder._beeminder.create_datapoint(slug, points, datetime.datetime.now().timestamp(), "upload from pyminder")


@app.command()
def delete(slug: str):
    """Delete a goal."""
    goal_path = Path.home() / ".config" / "beetimer" / f"{slug}.json"
    if not goal_path.exists():
        typer.echo(f"Goal {slug} not started.")
        raise typer.Exit(1)

    goal_path.unlink()

    typer.echo(f"Deleted goal {slug}.")
