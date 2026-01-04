"""Typer CLI client application."""

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="GM Chatbot CLI")
console = Console()
BASE_URL = "http://localhost:8000/api/v1"


@app.command()
def campaigns():
    """List all campaigns."""
    try:
        response = httpx.get(f"{BASE_URL}/campaigns")
        response.raise_for_status()
        data = response.json()

        if data.get("success") and data.get("data"):
            table = Table(title="Campaigns")
            table.add_column("ID")
            table.add_column("Name")
            table.add_column("System")
            table.add_column("Status")

            for campaign in data["data"]:
                table.add_row(
                    campaign["metadata"]["id"][:8],
                    campaign["name"],
                    campaign["rule_system"],
                    campaign["status"],
                )

            console.print(table)
        else:
            console.print("No campaigns found")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def roll(expression: str, reason: str = ""):
    """Roll dice using the dice tool."""
    try:
        response = httpx.post(
            f"{BASE_URL}/tools/dice/roll",
            params={"expression": expression, "reason": reason},
        )
        response.raise_for_status()
        result = response.json()["data"]

        console.print(f"🎲 [bold]{expression}[/bold] → [green]{result['total']}[/green]")
        console.print(f"   Rolls: {result['rolls']} + {result['modifier']}")
        if result.get("breakdown"):
            console.print(f"   {result['breakdown']}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def chat(campaign_id: str, message: str):
    """Send a message to the GM."""
    try:
        response = httpx.post(
            f"{BASE_URL}/campaigns/{campaign_id}/chat",
            json={"message": message, "campaign_id": campaign_id},
        )
        response.raise_for_status()
        result = response.json()["data"]

        console.print(f"[bold]GM:[/bold] {result['response']}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    app()
