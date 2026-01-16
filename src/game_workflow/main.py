"""CLI entry point for game-workflow.

This module provides the main CLI interface using Typer.
"""

import typer

app = typer.Typer(
    name="game-workflow",
    help="Fully automated game creation pipeline using Claude.",
    no_args_is_help=True,
)


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Game concept prompt"),
    engine: str = typer.Option("phaser", help="Game engine to use (phaser or godot)"),
) -> None:
    """Start a new game creation workflow from a prompt."""
    typer.echo(f"Starting workflow with prompt: {prompt}")
    typer.echo(f"Using engine: {engine}")
    # TODO: Implement workflow orchestration


@app.command()
def status() -> None:
    """Check the status of the current workflow."""
    typer.echo("No active workflow.")
    # TODO: Implement status checking


@app.command()
def cancel() -> None:
    """Cancel the current workflow."""
    typer.echo("No active workflow to cancel.")
    # TODO: Implement workflow cancellation


@app.command()
def resume(
    checkpoint: str = typer.Option(None, help="Checkpoint ID to resume from"),
) -> None:
    """Resume a workflow from a checkpoint."""
    if checkpoint:
        typer.echo(f"Resuming from checkpoint: {checkpoint}")
    else:
        typer.echo("Resuming from last checkpoint...")
    # TODO: Implement workflow resumption


if __name__ == "__main__":
    app()
