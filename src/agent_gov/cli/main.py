"""CLI entry point for agent-gov.

Invoked as::

    agent-gov [OPTIONS] COMMAND [ARGS]...

or, during development::

    python -m agent_gov.cli.main
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agent_gov import __version__

console = Console()
err_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(version=__version__, prog_name="agent-gov")
def cli() -> None:
    """AI agent governance and compliance engine with policy enforcement."""


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------


@cli.command(name="version")
def version_command() -> None:
    """Show detailed version information."""
    import platform

    console.print(Panel.fit(
        f"[bold cyan]agent-gov[/bold cyan] [green]v{__version__}[/green]\n"
        f"Python {platform.python_version()}  |  {platform.system()} {platform.machine()}",
        title="Version Info",
        border_style="cyan",
    ))


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


@cli.command(name="check")
@click.option(
    "--policy",
    "policy_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to the policy YAML file.",
)
@click.option(
    "--action",
    "action_json",
    required=True,
    help="Action payload as a JSON string.",
)
@click.option(
    "--audit-log",
    "audit_log_path",
    default=None,
    type=click.Path(dir_okay=False),
    help="Optional path to an audit JSONL file for logging results.",
)
@click.option(
    "--agent-id",
    "agent_id",
    default="cli-user",
    help="Agent ID to record in the audit log (default: cli-user).",
)
def check_command(
    policy_path: str,
    action_json: str,
    audit_log_path: Optional[str],
    agent_id: str,
) -> None:
    """Evaluate an action against a policy and print the verdict."""
    from agent_gov.policy.evaluator import PolicyEvaluator
    from agent_gov.policy.loader import PolicyLoader, PolicyLoadError

    # Load policy
    loader = PolicyLoader()
    try:
        policy = loader.load_file(policy_path)
    except PolicyLoadError as exc:
        err_console.print(f"[red]Error loading policy:[/red] {exc}")
        sys.exit(1)

    # Parse action
    try:
        action: dict[str, object] = json.loads(action_json)
    except json.JSONDecodeError as exc:
        err_console.print(f"[red]Invalid JSON for --action:[/red] {exc}")
        sys.exit(1)

    if not isinstance(action, dict):
        err_console.print("[red]--action must be a JSON object (dict).[/red]")
        sys.exit(1)

    # Evaluate
    evaluator = PolicyEvaluator()
    report = evaluator.evaluate(policy, action)

    # Display result
    status_style = "green" if report.passed else "red"
    status_text = "PASS" if report.passed else "FAIL"

    console.print(
        Panel.fit(
            f"[bold {status_style}]{status_text}[/bold {status_style}]  "
            f"policy=[cyan]{report.policy_name}[/cyan]  "
            f"violations=[yellow]{report.violation_count}[/yellow]  "
            f"severity=[magenta]{report.highest_severity}[/magenta]",
            title="Evaluation Result",
            border_style=status_style,
        )
    )

    if report.verdicts:
        table = Table(title="Rule Verdicts", box=None, padding=(0, 1))
        table.add_column("Rule", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Severity")
        table.add_column("Message")

        for verdict in report.verdicts:
            status_display = (
                Text("PASS", style="green") if verdict.passed else Text("FAIL", style="red")
            )
            table.add_row(
                verdict.rule_name,
                status_display,
                verdict.severity,
                verdict.message,
            )
        console.print(table)

    # Audit logging
    if audit_log_path:
        from agent_gov.audit.logger import AuditLogger

        audit_logger = AuditLogger(audit_log_path)
        entry = audit_logger.log_from_report(report, agent_id=agent_id)
        console.print(f"\n[dim]Audit entry logged → {audit_log_path}[/dim]")

    sys.exit(0 if report.passed else 2)


# ---------------------------------------------------------------------------
# audit group
# ---------------------------------------------------------------------------


@cli.group(name="audit")
def audit_group() -> None:
    """Commands for inspecting the audit log."""


@audit_group.command(name="show")
@click.option(
    "--log",
    "log_path",
    default="audit.jsonl",
    type=click.Path(dir_okay=False),
    help="Path to the audit JSONL file (default: audit.jsonl).",
)
@click.option(
    "--last",
    "last_n",
    default=20,
    show_default=True,
    help="Number of most-recent entries to display.",
)
def audit_show_command(log_path: str, last_n: int) -> None:
    """Show the most recent audit log entries."""
    from agent_gov.audit.reader import AuditReader

    reader = AuditReader(log_path)
    if not Path(log_path).exists():
        console.print(f"[yellow]Audit log not found:[/yellow] {log_path}")
        return

    entries = reader.last(last_n)
    if not entries:
        console.print("[yellow]No audit entries found.[/yellow]")
        return

    table = Table(title=f"Last {last_n} Audit Entries", box=None, padding=(0, 1))
    table.add_column("Timestamp", style="dim")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Action Type")
    table.add_column("Policy")
    table.add_column("Verdict", justify="center")

    for entry in reversed(entries):
        verdict_text = (
            Text("PASS", style="green") if entry.verdict == "pass" else Text("FAIL", style="red")
        )
        table.add_row(
            entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            entry.agent_id,
            entry.action_type,
            entry.policy_name,
            verdict_text,
        )

    console.print(table)
    stats = reader.stats()
    console.print(
        f"\n[dim]Total: {stats['total']}  Pass: {stats['pass_count']}  "
        f"Fail: {stats['fail_count']}[/dim]"
    )


@audit_group.command(name="query")
@click.option(
    "--log",
    "log_path",
    default="audit.jsonl",
    type=click.Path(dir_okay=False),
    help="Path to the audit JSONL file (default: audit.jsonl).",
)
@click.option("--agent-id", "agent_id", default=None, help="Filter by agent ID.")
@click.option("--action-type", "action_type", default=None, help="Filter by action type.")
@click.option("--verdict", "verdict", default=None, type=click.Choice(["pass", "fail"]))
@click.option("--policy", "policy_name", default=None, help="Filter by policy name.")
@click.option(
    "--since",
    "since_str",
    default=None,
    help="ISO date/datetime lower bound (e.g. 2024-01-01 or 2024-01-01T12:00:00).",
)
@click.option(
    "--limit",
    "limit",
    default=50,
    show_default=True,
    help="Maximum number of entries to display.",
)
def audit_query_command(
    log_path: str,
    agent_id: Optional[str],
    action_type: Optional[str],
    verdict: Optional[str],
    policy_name: Optional[str],
    since_str: Optional[str],
    limit: int,
) -> None:
    """Query the audit log with filters."""
    from agent_gov.audit.reader import AuditReader

    since: Optional[datetime] = None
    if since_str:
        try:
            since = datetime.fromisoformat(since_str)
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
        except ValueError:
            err_console.print(f"[red]Invalid --since date:[/red] {since_str!r}")
            sys.exit(1)

    reader = AuditReader(log_path)
    if not Path(log_path).exists():
        console.print(f"[yellow]Audit log not found:[/yellow] {log_path}")
        return

    entries = reader.query(
        agent_id=agent_id,
        action_type=action_type,
        verdict=verdict,
        policy_name=policy_name,
        since=since,
    )
    entries = entries[-limit:]

    if not entries:
        console.print("[yellow]No entries match the given filters.[/yellow]")
        return

    table = Table(title=f"Query Results ({len(entries)} entries)", box=None, padding=(0, 1))
    table.add_column("Timestamp", style="dim")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Action Type")
    table.add_column("Policy")
    table.add_column("Verdict", justify="center")

    for entry in entries:
        verdict_text = (
            Text("PASS", style="green") if entry.verdict == "pass" else Text("FAIL", style="red")
        )
        table.add_row(
            entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            entry.agent_id,
            entry.action_type,
            entry.policy_name,
            verdict_text,
        )
    console.print(table)


# ---------------------------------------------------------------------------
# report group
# ---------------------------------------------------------------------------


@cli.group(name="report")
def report_group() -> None:
    """Commands for generating governance and compliance reports."""


@report_group.command(name="generate")
@click.option(
    "--policy",
    "policy_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the policy YAML file.",
)
@click.option(
    "--format",
    "output_format",
    default="md",
    type=click.Choice(["md", "json"]),
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output",
    "output_path",
    default=None,
    help="Output file path.  Defaults to report.md or report.json.",
)
@click.option(
    "--audit-log",
    "audit_log_path",
    default="audit.jsonl",
    type=click.Path(dir_okay=False),
    help="Path to the audit log for including audit data (default: audit.jsonl).",
)
@click.option(
    "--title",
    "title",
    default="Agent Governance Report",
    show_default=True,
    help="Report title.",
)
def report_generate_command(
    policy_path: str,
    output_format: str,
    output_path: Optional[str],
    audit_log_path: str,
    title: str,
) -> None:
    """Generate a governance report from a policy and audit log."""
    from agent_gov.audit.reader import AuditReader
    from agent_gov.policy.loader import PolicyLoader, PolicyLoadError
    from agent_gov.reporting.generator import ReportGenerator
    from agent_gov.reporting.json_report import JsonReporter
    from agent_gov.reporting.markdown import MarkdownReporter

    # Load policy
    loader = PolicyLoader()
    try:
        policy = loader.load_file(policy_path)
    except PolicyLoadError as exc:
        err_console.print(f"[red]Error loading policy:[/red] {exc}")
        sys.exit(1)

    # Build reader if audit log exists
    audit_reader: Optional[AuditReader] = None
    if Path(audit_log_path).exists():
        audit_reader = AuditReader(audit_log_path)

    generator = ReportGenerator(audit_reader=audit_reader)
    payload = generator.governance_report(policy_name=policy.name, title=title)

    # Resolve output path
    default_ext = ".md" if output_format == "md" else ".json"
    resolved_output = Path(output_path) if output_path else Path(f"report{default_ext}")

    if output_format == "md":
        reporter = MarkdownReporter()
        written = reporter.write_governance(payload, resolved_output)
    else:
        reporter_json = JsonReporter()
        written = reporter_json.write(payload, resolved_output)

    console.print(f"[green]Report written to:[/green] {written}")


# ---------------------------------------------------------------------------
# frameworks group
# ---------------------------------------------------------------------------


@cli.group(name="frameworks")
def frameworks_group() -> None:
    """Commands for working with compliance frameworks."""


@frameworks_group.command(name="list")
def frameworks_list_command() -> None:
    """List all available compliance frameworks."""
    from agent_gov.plugins.registry import framework_registry

    table = Table(title="Available Compliance Frameworks", box=None, padding=(0, 1))
    table.add_column("Name", style="cyan")
    table.add_column("Version")
    table.add_column("Description")

    for fw_name in framework_registry.list_names():
        fw_cls = framework_registry.get(fw_name)
        instance = fw_cls()
        table.add_row(
            fw_name,
            getattr(instance, "version", "—"),
            getattr(instance, "description", "")[:80],
        )

    console.print(table)


@frameworks_group.command(name="check")
@click.option(
    "--framework",
    "framework_name",
    required=True,
    help="Framework name (e.g. gdpr, hipaa, eu-ai-act, soc2).",
)
@click.option(
    "--evidence",
    "evidence_path",
    default=None,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to a YAML file containing evidence keyed by checklist item ID.",
)
@click.option(
    "--output",
    "output_path",
    default=None,
    help="Optional path to write the framework report (JSON).",
)
def frameworks_check_command(
    framework_name: str,
    evidence_path: Optional[str],
    output_path: Optional[str],
) -> None:
    """Run a compliance checklist against evidence."""
    import yaml

    from agent_gov.plugins.registry import framework_registry
    from agent_gov.reporting.json_report import JsonReporter

    if framework_name not in framework_registry:
        available = framework_registry.list_names()
        err_console.print(
            f"[red]Unknown framework:[/red] {framework_name!r}. "
            f"Available: {available!r}"
        )
        sys.exit(1)

    fw_cls = framework_registry.get(framework_name)
    framework = fw_cls()

    evidence: dict[str, object] = {}
    if evidence_path:
        try:
            raw = Path(evidence_path).read_text(encoding="utf-8")
            loaded = yaml.safe_load(raw)
            if isinstance(loaded, dict):
                evidence = loaded
        except Exception as exc:
            err_console.print(f"[red]Error reading evidence file:[/red] {exc}")
            sys.exit(1)

    report = framework.run_check(evidence)

    # Display
    score_color = "green" if report.score >= 0.8 else "yellow" if report.score >= 0.5 else "red"
    console.print(
        Panel.fit(
            f"[bold]Framework:[/bold] [cyan]{framework_name}[/cyan]\n"
            f"[bold]Score:[/bold] [{score_color}]{report.score_percent:.1f}%[/{score_color}]  "
            f"Passed: [green]{report.passed_count}[/green] / {len(report.results)}  "
            f"Failed: [red]{report.failed_count}[/red]  "
            f"Unknown: [yellow]{report.unknown_count}[/yellow]",
            title="Compliance Check",
            border_style=score_color,
        )
    )

    table = Table(box=None, padding=(0, 1))
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Category")
    table.add_column("Status", justify="center")
    table.add_column("Evidence")

    for result in report.results:
        status_map = {
            "pass": Text("PASS", style="green"),
            "fail": Text("FAIL", style="red"),
            "unknown": Text("UNKNOWN", style="yellow"),
        }
        table.add_row(
            result.item.id,
            result.item.name,
            result.item.category or "—",
            status_map.get(result.status, Text(result.status)),
            result.evidence[:60] if result.evidence else "—",
        )
    console.print(table)

    # Write output if requested
    if output_path:
        reporter = JsonReporter()
        written = reporter.write(report.to_dict(), output_path)
        console.print(f"\n[green]Report written to:[/green] {written}")


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------


@cli.command(name="init")
@click.option(
    "--preset",
    "preset",
    default="standard",
    type=click.Choice(["minimal", "standard", "strict"]),
    show_default=True,
    help="Policy preset to initialize.",
)
@click.option(
    "--output",
    "output_path",
    default="policy.yaml",
    show_default=True,
    help="Destination path for the generated policy file.",
)
def init_command(preset: str, output_path: str) -> None:
    """Initialize a project with a policy pack."""
    import importlib.resources

    # Load the pack from the package data
    packs_dir = Path(__file__).parent.parent / "packs"
    pack_file = packs_dir / f"{preset}.yaml"

    if not pack_file.exists():
        err_console.print(f"[red]Pack file not found:[/red] {pack_file}")
        sys.exit(1)

    destination = Path(output_path)
    if destination.exists():
        if not click.confirm(
            f"[yellow]{output_path}[/yellow] already exists. Overwrite?", default=False
        ):
            console.print("[yellow]Aborted.[/yellow]")
            return

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(pack_file.read_text(encoding="utf-8"), encoding="utf-8")

    console.print(
        f"[green]Initialized[/green] [cyan]{preset}[/cyan] policy pack → [bold]{output_path}[/bold]"
    )
    console.print(
        "\nNext steps:\n"
        f"  1. Review and customize {output_path}\n"
        "  2. Evaluate an action:\n"
        f'     agent-gov check --policy {output_path} --action \'{"{"}"type": "search"{"}"}\'',
    )


# ---------------------------------------------------------------------------
# plugins
# ---------------------------------------------------------------------------


@cli.group(name="plugins")
def plugins_group() -> None:
    """List and inspect registered rules and frameworks."""


@plugins_group.command(name="list")
def plugins_list_command() -> None:
    """List all registered rules and compliance frameworks."""
    from agent_gov.plugins.registry import framework_registry, rule_registry

    # Rules table
    rule_table = Table(title="Registered Rules", box=None, padding=(0, 1))
    rule_table.add_column("Name", style="cyan")
    rule_table.add_column("Class")

    for rule_name in rule_registry.list_names():
        rule_cls = rule_registry.get(rule_name)
        rule_table.add_row(rule_name, rule_cls.__qualname__)

    console.print(rule_table)
    console.print()

    # Frameworks table
    fw_table = Table(title="Registered Frameworks", box=None, padding=(0, 1))
    fw_table.add_column("Name", style="cyan")
    fw_table.add_column("Version")
    fw_table.add_column("Class")

    for fw_name in framework_registry.list_names():
        fw_cls = framework_registry.get(fw_name)
        instance = fw_cls()
        fw_table.add_row(
            fw_name,
            getattr(instance, "version", "—"),
            fw_cls.__qualname__,
        )

    console.print(fw_table)


if __name__ == "__main__":
    cli()
