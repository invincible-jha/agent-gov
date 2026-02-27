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


# ---------------------------------------------------------------------------
# eu-ai-act classify
# ---------------------------------------------------------------------------


@cli.command(name="classify")
@click.option(
    "--description",
    "-d",
    "description",
    required=True,
    help="Free-text description of the AI system.",
)
@click.option(
    "--use-case",
    "-u",
    "use_case",
    multiple=True,
    help="Intended use case (repeatable).",
)
@click.option(
    "--data-category",
    "-c",
    "data_category",
    multiple=True,
    help="Data category processed by the system (repeatable).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
    help="Output format.",
)
def classify_command(
    description: str,
    use_case: tuple[str, ...],
    data_category: tuple[str, ...],
    output_format: str,
) -> None:
    """Classify an AI system's risk level per the EU AI Act (Annex III)."""
    import dataclasses

    from agent_gov.frameworks.eu_ai_act_classifier import EUAIActClassifier

    classifier = EUAIActClassifier()
    result = classifier.classify(
        system_description=description,
        use_cases=list(use_case) if use_case else None,
        data_categories=list(data_category) if data_category else None,
    )

    if output_format == "json":
        click.echo(json.dumps(dataclasses.asdict(result), indent=2))
        return

    # Rich table output
    level_colours: dict[str, str] = {
        "unacceptable": "red",
        "high": "yellow",
        "limited": "cyan",
        "minimal": "green",
    }
    colour = level_colours.get(result.level.value, "white")

    console.print(
        Panel.fit(
            f"[bold {colour}]{result.level.value.upper()}[/bold {colour}]\n"
            f"[bold]Category:[/bold] {result.annex_iii_category}\n"
            f"[bold]Confidence:[/bold] {result.confidence:.0%}\n"
            f"[bold]Reasoning:[/bold] {result.reasoning}",
            title="EU AI Act Risk Classification",
            border_style=colour,
        )
    )

    if result.article_references:
        console.print(
            f"[bold]Articles:[/bold] {', '.join(result.article_references)}"
        )

    if result.obligations:
        table = Table(title="Obligations", box=None, padding=(0, 1))
        table.add_column("Requirement", style="cyan")
        for obligation in result.obligations:
            table.add_row(obligation)
        console.print(table)


# ---------------------------------------------------------------------------
# eu-ai-act document
# ---------------------------------------------------------------------------


@cli.command(name="document")
@click.option(
    "--system-name",
    "system_name",
    required=True,
    help="Name of the AI system.",
)
@click.option(
    "--provider",
    "provider",
    required=True,
    help="Provider organisation name.",
)
@click.option(
    "--description",
    "description",
    required=True,
    help="General description of the AI system.",
)
@click.option(
    "--output",
    "-o",
    "output",
    required=True,
    help="Output directory for generated documentation files.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "json", "both"]),
    default="both",
    show_default=True,
    help="Export format.",
)
def document_command(
    system_name: str,
    provider: str,
    description: str,
    output: str,
    output_format: str,
) -> None:
    """Generate EU AI Act Annex IV technical documentation."""
    from pathlib import Path as _Path

    from agent_gov.frameworks.eu_ai_act_docs import AnnexIVDocumentation

    doc = AnnexIVDocumentation(
        system_name=system_name,
        provider_name=provider,
        system_description=description,
        intended_purpose=description,
    )

    out_path = _Path(output)
    out_path.mkdir(parents=True, exist_ok=True)
    created: list[str] = []

    if output_format in ("markdown", "both"):
        md_path = out_path / "annex-iv-technical-documentation.md"
        md_path.write_text(doc.to_markdown(), encoding="utf-8")
        created.append(str(md_path))

    if output_format in ("json", "both"):
        import dataclasses

        json_path = out_path / "annex-iv-data.json"
        json_path.write_text(
            json.dumps(dataclasses.asdict(doc), indent=2),
            encoding="utf-8",
        )
        created.append(str(json_path))

    for file_path in created:
        console.print(f"[green]Created:[/green] {file_path}")

    console.print(
        f"\n[bold]Documentation generated[/bold] for [cyan]{system_name}[/cyan] "
        f"in [bold]{output}[/bold]"
    )


# ---------------------------------------------------------------------------
# policy library group
# ---------------------------------------------------------------------------


@cli.group(name="policy")
def policy_group() -> None:
    """Commands for managing the governance policy library."""


@policy_group.command(name="list")
@click.option(
    "--source",
    "source_dir",
    default=None,
    type=click.Path(file_okay=False),
    help="Directory to scan for policy YAML files.  Defaults to the built-in library.",
)
@click.option(
    "--domain",
    "domain",
    default=None,
    type=click.Choice(["healthcare", "finance", "eu-ai-act", "general", "gdpr"]),
    help="Filter policies by compliance domain.",
)
@click.option(
    "--severity",
    "severity",
    default=None,
    type=click.Choice(["critical", "high", "medium", "low"]),
    help="Filter policies by severity level.",
)
def policy_list_command(
    source_dir: Optional[str],
    domain: Optional[str],
    severity: Optional[str],
) -> None:
    """List available governance policies from the policy library."""
    from pathlib import Path as _Path

    from agent_gov.policies.loader import LibraryPolicyLoadError, LibraryPolicyLoader

    # Resolve source directory: use built-in library if not specified
    if source_dir:
        resolved_source = _Path(source_dir)
    else:
        resolved_source = _Path(__file__).parent.parent.parent.parent.parent / "policies"
        if not resolved_source.exists():
            # Fall back to relative path from cwd
            resolved_source = _Path.cwd() / "policies"

    if not resolved_source.exists():
        err_console.print(
            f"[red]Policy library directory not found:[/red] {resolved_source}\n"
            "Use [cyan]--source[/cyan] to specify the policies directory."
        )
        sys.exit(1)

    loader = LibraryPolicyLoader()
    try:
        policies = loader.load_directory(
            resolved_source,
            recursive=True,
            domain_filter=domain,
        )
    except LibraryPolicyLoadError as exc:
        err_console.print(f"[red]Error loading policies:[/red] {exc}")
        sys.exit(1)

    # Apply severity filter (not natively supported in loader)
    if severity:
        policies = [p for p in policies if p.severity.value == severity]

    if not policies:
        console.print("[yellow]No policies found matching the given filters.[/yellow]")
        return

    table = Table(title=f"Policy Library ({len(policies)} policies)", box=None, padding=(0, 1))
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Domain", style="magenta")
    table.add_column("Severity", justify="center")
    table.add_column("Rules", justify="right")
    table.add_column("Tags")

    severity_styles: dict[str, str] = {
        "critical": "red",
        "high": "yellow",
        "medium": "cyan",
        "low": "green",
    }

    for policy in sorted(policies, key=lambda p: (p.domain.value, p.id)):
        sev_style = severity_styles.get(policy.severity.value, "white")
        table.add_row(
            policy.id,
            policy.name,
            policy.domain.value,
            Text(policy.severity.value.upper(), style=sev_style),
            str(len(policy.rules)),
            ", ".join(policy.tags[:3]),
        )

    console.print(table)


@policy_group.command(name="install")
@click.option(
    "--source",
    "source_dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, readable=True),
    help="Source directory containing policy YAML files.",
)
@click.option(
    "--target",
    "target_dir",
    required=True,
    type=click.Path(file_okay=False),
    help="Target directory to install policies into.",
)
@click.option(
    "--domain",
    "domain",
    default=None,
    type=click.Choice(["healthcare", "finance", "eu-ai-act", "general", "gdpr"]),
    help="Only install policies for this domain.",
)
@click.option(
    "--no-overwrite",
    "no_overwrite",
    is_flag=True,
    default=False,
    help="Skip files that already exist in the target directory.",
)
@click.option(
    "--dry-run",
    "dry_run",
    is_flag=True,
    default=False,
    help="Preview what would be installed without copying files.",
)
def policy_install_command(
    source_dir: str,
    target_dir: str,
    domain: Optional[str],
    no_overwrite: bool,
    dry_run: bool,
) -> None:
    """Install governance policies from a source directory into a target directory."""
    from agent_gov.policies.installer import LibraryPolicyInstaller

    installer = LibraryPolicyInstaller()

    try:
        results = installer.install(
            source=source_dir,
            target=target_dir,
            domain=domain,
            overwrite=not no_overwrite,
            dry_run=dry_run,
        )
    except ValueError as exc:
        err_console.print(f"[red]Install error:[/red] {exc}")
        sys.exit(1)

    if not results:
        console.print("[yellow]No policy files found in source directory.[/yellow]")
        return

    dry_run_label = " [dim](dry-run)[/dim]" if dry_run else ""
    table = Table(
        title=f"Policy Installation{dry_run_label}",
        box=None,
        padding=(0, 1),
    )
    table.add_column("Policy ID", style="cyan")
    table.add_column("Domain", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Destination")

    installed_count = 0
    skipped_count = 0
    error_count = 0

    for result in results:
        if result.error:
            status_text = Text("ERROR", style="red")
            error_count += 1
        elif result.skipped:
            status_text = Text("SKIPPED", style="yellow")
            skipped_count += 1
        elif result.dry_run:
            status_text = Text("WOULD INSTALL", style="cyan")
            installed_count += 1
        else:
            status_text = Text("INSTALLED", style="green")
            installed_count += 1

        table.add_row(
            result.policy_id,
            result.domain,
            status_text,
            str(result.target_path),
        )

    console.print(table)
    console.print(
        f"\n[dim]Installed: {installed_count}  "
        f"Skipped: {skipped_count}  "
        f"Errors: {error_count}[/dim]"
    )

    if error_count > 0:
        sys.exit(1)


@policy_group.command(name="validate")
@click.argument(
    "policy_file",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
def policy_validate_command(policy_file: str) -> None:
    """Validate a governance policy YAML file against the library schema."""
    from pathlib import Path as _Path

    from agent_gov.policies.validator import LibraryPolicyValidator

    validator = LibraryPolicyValidator()
    result = validator.validate_file(_Path(policy_file))

    if result.valid:
        console.print(
            Panel.fit(
                f"[bold green]VALID[/bold green]  [cyan]{policy_file}[/cyan]",
                title="Policy Validation",
                border_style="green",
            )
        )
    else:
        error_lines = "\n".join(f"  • {err}" for err in result.errors)
        console.print(
            Panel.fit(
                f"[bold red]INVALID[/bold red]  [cyan]{policy_file}[/cyan]\n\n{error_lines}",
                title="Policy Validation",
                border_style="red",
            )
        )
        sys.exit(2)


if __name__ == "__main__":
    cli()
