"""CLI entry point for game-workflow.

This module provides the main CLI interface using Typer with Rich formatting.
"""

import asyncio
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from game_workflow.config import get_settings
from game_workflow.hooks.slack_approval import SlackApprovalHook
from game_workflow.orchestrator import StateNotFoundError, Workflow, WorkflowPhase, WorkflowState

# Initialize Typer app
app = typer.Typer(
    name="game-workflow",
    help="Fully automated game creation pipeline using Claude.",
    no_args_is_help=True,
)

# State subcommand group
state_app = typer.Typer(help="Workflow state management commands.")
app.add_typer(state_app, name="state")

# Rich console for formatted output
console = Console()


def _get_phase_color(phase: WorkflowPhase) -> str:
    """Get the display color for a phase.

    Args:
        phase: The workflow phase.

    Returns:
        Rich color name.
    """
    colors = {
        WorkflowPhase.INIT: "blue",
        WorkflowPhase.DESIGN: "cyan",
        WorkflowPhase.BUILD: "yellow",
        WorkflowPhase.QA: "magenta",
        WorkflowPhase.PUBLISH: "green",
        WorkflowPhase.COMPLETE: "bold green",
        WorkflowPhase.FAILED: "bold red",
    }
    return colors.get(phase, "white")


def _display_state(state: WorkflowState, verbose: bool = False) -> None:
    """Display a workflow state.

    Args:
        state: The workflow state to display.
        verbose: Show detailed information.
    """
    phase_color = _get_phase_color(state.phase)

    # Create status panel
    status_lines = [
        f"[bold]ID:[/bold] {state.id}",
        f"[bold]Phase:[/bold] [{phase_color}]{state.phase.value}[/{phase_color}]",
        f"[bold]Engine:[/bold] {state.engine}",
        f"[bold]Created:[/bold] {state.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"[bold]Updated:[/bold] {state.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    if state.prompt:
        # Truncate long prompts
        prompt_display = state.prompt[:100] + "..." if len(state.prompt) > 100 else state.prompt
        status_lines.append(f"[bold]Prompt:[/bold] {prompt_display}")

    console.print(Panel("\n".join(status_lines), title="Workflow Status", border_style="blue"))

    if verbose:
        # Show artifacts
        if state.artifacts:
            artifact_table = Table(title="Artifacts")
            artifact_table.add_column("Name", style="cyan")
            artifact_table.add_column("Path", style="green")

            for name, path in state.artifacts.items():
                artifact_table.add_row(name, str(path))

            console.print(artifact_table)

        # Show approvals
        if state.approvals:
            approval_table = Table(title="Approvals")
            approval_table.add_column("Gate", style="cyan")
            approval_table.add_column("Status", style="green")

            for gate, approved in state.approvals.items():
                status_text = "[green]✓ Approved[/green]" if approved else "[red]✗ Rejected[/red]"
                approval_table.add_row(gate, status_text)

            console.print(approval_table)

        # Show errors
        if state.errors:
            console.print("[bold red]Errors:[/bold red]")
            for error in state.errors:
                console.print(f"  • {error}")

        # Show checkpoints
        if state.checkpoints:
            checkpoint_table = Table(title="Checkpoints")
            checkpoint_table.add_column("ID", style="cyan")
            checkpoint_table.add_column("Phase", style="yellow")
            checkpoint_table.add_column("Time", style="green")
            checkpoint_table.add_column("Description", style="white")

            for cp in state.checkpoints[-5:]:  # Show last 5
                checkpoint_table.add_row(
                    cp.checkpoint_id,
                    cp.phase.value,
                    cp.created_at.strftime("%H:%M:%S"),
                    cp.description or "-",
                )

            console.print(checkpoint_table)


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Game concept prompt"),
    engine: Literal["phaser", "godot"] = typer.Option(
        None, "--engine", "-e", help="Game engine to use"
    ),
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Directory for workflow outputs (default: state dir)"
    ),
) -> None:
    """Start a new game creation workflow from a prompt."""
    settings = get_settings()
    engine_to_use = engine or settings.workflow.default_engine

    console.print("[bold blue]Starting new workflow[/bold blue]")
    console.print(f"[bold]Prompt:[/bold] {prompt}")
    console.print(f"[bold]Engine:[/bold] {engine_to_use}")
    if output_dir:
        console.print(f"[bold]Output:[/bold] {output_dir}")
    console.print()

    # Configure Slack approval hook if credentials are available
    approval_hook = None
    if settings.slack.bot_token:
        approval_hook = SlackApprovalHook(
            channel=settings.slack.channel,
            token=settings.slack.bot_token,
        )
        console.print(f"[bold]Slack:[/bold] Approval gates enabled ({settings.slack.channel})")
    else:
        console.print(
            "[yellow]Warning:[/yellow] No Slack token configured, approvals will be auto-granted"
        )

    workflow = Workflow(
        prompt=prompt,
        engine=engine_to_use,
        output_dir=output_dir,
        approval_hook=approval_hook,
    )
    console.print(f"[green]Created workflow:[/green] {workflow.state.id}")

    # Run the workflow
    console.print("\n[bold]Running workflow...[/bold]\n")
    result = asyncio.run(workflow.run())

    # Display results
    if result["status"] == "complete":
        console.print("\n[bold green]✓ Workflow completed successfully![/bold green]")
    else:
        console.print("\n[bold red]✗ Workflow failed[/bold red]")
        if result["errors"]:
            console.print("[red]Errors:[/red]")
            for error in result["errors"]:
                console.print(f"  • {error}")

    _display_state(workflow.state)


@app.command()
def status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
) -> None:
    """Check the status of the current/latest workflow."""
    state = WorkflowState.get_latest()

    if state is None:
        console.print("[yellow]No workflow found.[/yellow]")
        console.print("Use [bold]game-workflow run[/bold] to start a new workflow.")
        return

    _display_state(state, verbose=verbose)


@app.command()
def cancel(
    state_id: str = typer.Option(None, "--id", help="Specific workflow ID to cancel"),
    force: bool = typer.Option(False, "--force", "-f", help="Cancel without confirmation"),
) -> None:
    """Cancel a workflow."""
    state: WorkflowState | None = None
    if state_id:
        try:
            state = WorkflowState.load(state_id)
        except StateNotFoundError:
            console.print(f"[red]Workflow not found:[/red] {state_id}")
            raise typer.Exit(1) from None
    else:
        state = WorkflowState.get_latest()

    if state is None:
        console.print("[yellow]No workflow to cancel.[/yellow]")
        return

    if state.phase.is_terminal:
        console.print(
            f"[yellow]Workflow {state.id} is already in terminal state: {state.phase.value}[/yellow]"
        )
        return

    if not force:
        confirmed = typer.confirm(f"Cancel workflow {state.id}?")
        if not confirmed:
            console.print("[yellow]Cancelled.[/yellow]")
            return

    workflow = Workflow(prompt=state.prompt, engine=state.engine, state=state)
    asyncio.run(workflow.cancel())
    console.print(f"[green]Workflow {state.id} cancelled.[/green]")


@app.command()
def resume(
    state_id: str = typer.Option(None, "--id", help="Specific workflow ID to resume"),
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Directory for workflow outputs (overrides saved setting)"
    ),
) -> None:
    """Resume a workflow from its last state."""
    settings = get_settings()

    # Configure Slack approval hook if credentials are available
    approval_hook = None
    if settings.slack.bot_token:
        approval_hook = SlackApprovalHook(
            channel=settings.slack.channel,
            token=settings.slack.bot_token,
        )

    workflow: Workflow | None = None
    if state_id:
        try:
            workflow = Workflow.resume(state_id, output_dir=output_dir, approval_hook=approval_hook)
        except StateNotFoundError:
            console.print(f"[red]Workflow not found:[/red] {state_id}")
            raise typer.Exit(1) from None
    else:
        workflow = Workflow.resume_latest(output_dir=output_dir, approval_hook=approval_hook)

    if workflow is None:
        console.print("[yellow]No workflow to resume.[/yellow]")
        console.print("Use [bold]game-workflow run[/bold] to start a new workflow.")
        return

    console.print(f"[bold blue]Resuming workflow:[/bold blue] {workflow.state.id}")
    console.print(f"[bold]Current phase:[/bold] {workflow.state.phase.value}")
    if output_dir:
        console.print(f"[bold]Output:[/bold] {output_dir}")
    console.print()

    # Run the workflow
    result = asyncio.run(workflow.run())

    # Display results
    if result["status"] == "complete":
        console.print("\n[bold green]✓ Workflow completed successfully![/bold green]")
    else:
        console.print("\n[bold red]✗ Workflow failed[/bold red]")

    _display_state(workflow.state)


# State subcommands


@state_app.command("show")
def state_show(
    state_id: str = typer.Argument(None, help="Workflow ID to show (default: latest)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
) -> None:
    """Show details of a workflow state."""
    state: WorkflowState | None = None
    if state_id:
        try:
            state = WorkflowState.load(state_id)
        except StateNotFoundError:
            console.print(f"[red]Workflow not found:[/red] {state_id}")
            raise typer.Exit(1) from None
    else:
        state = WorkflowState.get_latest()

    if state is None:
        console.print("[yellow]No workflow found.[/yellow]")
        return

    _display_state(state, verbose=verbose)


@state_app.command("list")
def state_list(
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of states to show"),
) -> None:
    """List all saved workflow states."""
    states = WorkflowState.list_all()

    if not states:
        console.print("[yellow]No workflow states found.[/yellow]")
        return

    table = Table(title=f"Workflow States (showing {min(len(states), limit)} of {len(states)})")
    table.add_column("ID", style="cyan")
    table.add_column("Phase", style="yellow")
    table.add_column("Engine", style="green")
    table.add_column("Created", style="blue")
    table.add_column("Prompt", style="white", max_width=40)

    for state in states[:limit]:
        phase_color = _get_phase_color(state.phase)
        prompt_display = state.prompt[:37] + "..." if len(state.prompt) > 40 else state.prompt

        table.add_row(
            state.id,
            f"[{phase_color}]{state.phase.value}[/{phase_color}]",
            state.engine,
            state.created_at.strftime("%Y-%m-%d %H:%M"),
            prompt_display,
        )

    console.print(table)


@state_app.command("reset")
def state_reset(
    state_id: str = typer.Argument(None, help="Specific workflow ID to delete"),
    all_states: bool = typer.Option(False, "--all", help="Delete all workflow states"),
    force: bool = typer.Option(False, "--force", "-f", help="Delete without confirmation"),
) -> None:
    """Delete workflow state(s)."""
    if all_states:
        states = WorkflowState.list_all()
        if not states:
            console.print("[yellow]No workflow states to delete.[/yellow]")
            return

        if not force:
            confirmed = typer.confirm(f"Delete all {len(states)} workflow states?")
            if not confirmed:
                console.print("[yellow]Cancelled.[/yellow]")
                return

        for state in states:
            WorkflowState.delete(state.id)

        console.print(f"[green]Deleted {len(states)} workflow states.[/green]")

    elif state_id:
        if not WorkflowState.delete(state_id):
            console.print(f"[red]Workflow not found:[/red] {state_id}")
            raise typer.Exit(1)

        console.print(f"[green]Deleted workflow:[/green] {state_id}")

    else:
        console.print("[yellow]Specify --id or --all to delete states.[/yellow]")
        console.print("Use [bold]game-workflow state list[/bold] to see available states.")


@state_app.command("cleanup")
def state_cleanup(
    keep: int = typer.Option(10, "--keep", "-k", help="Number of recent states to keep"),
    force: bool = typer.Option(False, "--force", "-f", help="Cleanup without confirmation"),
) -> None:
    """Remove old workflow states, keeping recent ones."""
    states = WorkflowState.list_all()

    if len(states) <= keep:
        console.print(f"[yellow]Only {len(states)} states exist, nothing to clean up.[/yellow]")
        return

    to_delete = len(states) - keep

    if not force:
        confirmed = typer.confirm(
            f"Delete {to_delete} old workflow states (keeping {keep} newest)?"
        )
        if not confirmed:
            console.print("[yellow]Cancelled.[/yellow]")
            return

    deleted = WorkflowState.cleanup_old(keep_count=keep)
    console.print(f"[green]Deleted {deleted} old workflow states.[/green]")


@app.command()
def version() -> None:
    """Show the version information."""
    from game_workflow import __version__

    console.print(f"[bold]game-workflow[/bold] version {__version__}")


if __name__ == "__main__":
    app()
