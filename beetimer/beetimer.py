import json
from pathlib import Path
from typing import Optional

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
