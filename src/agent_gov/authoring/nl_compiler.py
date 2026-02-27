"""NlCompiler — convert natural language policy statements to YAML policy format.

Uses keyword extraction and pattern matching templates to transform plain English
policy statements into structured policy YAML.

Example
-------
::

    from agent_gov.authoring.nl_compiler import NlCompiler

    compiler = NlCompiler()
    result = compiler.compile("Block PII in responses")
    print(result.to_yaml())
    # name: generated-policy
    # rules:
    #   - name: block-pii-in-response
    #     type: pii_check
    #     action: block
    #     target: response
    #     severity: high
"""
from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from typing import Optional


class NlCompilerError(Exception):
    """Raised when a statement cannot be compiled to a policy rule."""


@dataclass
class ParsedStatement:
    """Intermediate representation of a parsed natural language statement.

    Attributes
    ----------
    raw_text:
        The original natural language text.
    action:
        Extracted action keyword: ``"block"``, ``"allow"``, ``"audit"``, ``"rate_limit"``.
    subject:
        The thing being regulated (e.g. ``"pii"``, ``"keywords"``, ``"cost"``).
    target:
        Where the rule applies: ``"request"``, ``"response"``, ``"tool_call"``, ``"any"``.
    parameters:
        Additional extracted parameters (e.g. max cost, keyword list).
    confidence:
        Confidence score (0.0–1.0) that the parsing is correct.
    """

    raw_text: str
    action: str = "block"
    subject: str = ""
    target: str = "any"
    parameters: dict[str, object] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class CompiledRule:
    """A single compiled policy rule ready for serialization.

    Attributes
    ----------
    name:
        Auto-generated rule name derived from action and subject.
    rule_type:
        The policy engine rule type string (e.g. ``"pii_check"``).
    action:
        Action to take when the rule triggers.
    target:
        Target context for the rule.
    severity:
        Severity level for violations.
    params:
        Parameters passed to the rule engine.
    """

    name: str
    rule_type: str
    action: str = "block"
    target: str = "any"
    severity: str = "medium"
    params: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "name": self.name,
            "type": self.rule_type,
            "action": self.action,
            "target": self.target,
            "severity": self.severity,
            "params": self.params,
        }

    def to_yaml_fragment(self, indent: int = 2) -> str:
        """Render this rule as a YAML fragment string."""
        pad = " " * indent
        lines = [
            f"- name: {self.name}",
            f"{pad}  type: {self.rule_type}",
            f"{pad}  action: {self.action}",
            f"{pad}  target: {self.target}",
            f"{pad}  severity: {self.severity}",
        ]
        if self.params:
            lines.append(f"{pad}  params:")
            for key, value in self.params.items():
                if isinstance(value, list):
                    lines.append(f"{pad}    {key}:")
                    for item in value:
                        lines.append(f"{pad}      - {item}")
                elif isinstance(value, bool):
                    lines.append(f"{pad}    {key}: {'true' if value else 'false'}")
                else:
                    lines.append(f"{pad}    {key}: {value}")
        return ("\n" + pad).join(lines)


@dataclass
class CompiledPolicy:
    """A compiled policy containing one or more rules.

    Attributes
    ----------
    name:
        Policy name.
    description:
        Human-readable description of the policy.
    rules:
        List of compiled rules.
    source_statements:
        Original natural language statements used to generate the policy.
    warnings:
        Non-fatal issues encountered during compilation.
    """

    name: str
    description: str = ""
    rules: list[CompiledRule] = field(default_factory=list)
    source_statements: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Serialise to a plain dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "rules": [r.to_dict() for r in self.rules],
        }

    def to_yaml(self) -> str:
        """Render the full policy as a YAML string."""
        lines = [
            f"name: {self.name}",
            f'description: "{self.description}"',
            "rules:",
        ]
        for rule in self.rules:
            lines.append("  " + rule.to_yaml_fragment(indent=2))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Keyword tables
# ---------------------------------------------------------------------------

_ACTION_KEYWORDS: dict[str, str] = {
    "block": "block",
    "deny": "block",
    "reject": "block",
    "prevent": "block",
    "disallow": "block",
    "forbid": "block",
    "stop": "block",
    "allow": "allow",
    "permit": "allow",
    "enable": "allow",
    "whitelist": "allow",
    "audit": "audit",
    "log": "audit",
    "monitor": "audit",
    "track": "audit",
    "record": "audit",
    "rate limit": "rate_limit",
    "rate-limit": "rate_limit",
    "throttle": "rate_limit",
    "limit": "rate_limit",
}

_SUBJECT_KEYWORDS: dict[str, tuple[str, str, dict[str, object]]] = {
    # pattern → (subject, rule_type, default_params)
    "pii": ("pii", "pii_check", {"check_email": True, "check_ssn": True, "check_phone": True}),
    "personal information": ("pii", "pii_check", {"check_email": True, "check_ssn": True}),
    "personal data": ("pii", "pii_check", {"check_email": True, "check_ssn": True}),
    "email": ("pii", "pii_check", {"check_email": True}),
    "ssn": ("pii", "pii_check", {"check_ssn": True}),
    "social security": ("pii", "pii_check", {"check_ssn": True}),
    "keyword": ("keywords", "keyword_block", {}),
    "keywords": ("keywords", "keyword_block", {}),
    "profanity": ("keywords", "keyword_block", {"keywords": ["profanity"]}),
    "banned word": ("keywords", "keyword_block", {}),
    "cost": ("cost", "cost_limit", {"max_cost": 1.0}),
    "budget": ("cost", "cost_limit", {"max_cost": 10.0}),
    "spend": ("cost", "cost_limit", {"max_cost": 1.0}),
    "token": ("cost", "cost_limit", {"max_tokens": 4096}),
    "tokens": ("cost", "cost_limit", {"max_tokens": 4096}),
    "role": ("role", "role_check", {}),
    "permission": ("role", "role_check", {}),
    "unauthorized": ("role", "role_check", {}),
    "admin": ("role", "role_check", {"required_roles": ["admin"]}),
}

_TARGET_KEYWORDS: dict[str, str] = {
    "response": "response",
    "output": "response",
    "reply": "response",
    "answer": "response",
    "request": "request",
    "input": "request",
    "query": "request",
    "prompt": "request",
    "tool": "tool_call",
    "tool call": "tool_call",
    "function call": "tool_call",
    "action": "tool_call",
}

_SEVERITY_KEYWORDS: dict[str, str] = {
    "critical": "critical",
    "severe": "critical",
    "high": "high",
    "important": "high",
    "medium": "medium",
    "moderate": "medium",
    "low": "low",
    "minor": "low",
    "warning": "low",
}


def _extract_action(text_lower: str) -> str:
    """Extract the action keyword from normalized text."""
    # Check multi-word first
    for keyword, action in sorted(_ACTION_KEYWORDS.items(), key=lambda kv: -len(kv[0])):
        if keyword in text_lower:
            return action
    return "block"  # default


def _extract_subject(
    text_lower: str,
) -> tuple[str, str, dict[str, object]]:
    """Return (subject, rule_type, default_params) from normalized text."""
    for keyword, (subject, rule_type, params) in sorted(
        _SUBJECT_KEYWORDS.items(), key=lambda kv: -len(kv[0])
    ):
        if keyword in text_lower:
            return subject, rule_type, dict(params)
    return "", "", {}


def _extract_target(text_lower: str) -> str:
    """Extract the target context from normalized text."""
    for keyword, target in sorted(_TARGET_KEYWORDS.items(), key=lambda kv: -len(kv[0])):
        if keyword in text_lower:
            return target
    return "any"


def _extract_severity(text_lower: str) -> str:
    """Extract severity from normalized text."""
    for keyword, severity in _SEVERITY_KEYWORDS.items():
        if keyword in text_lower:
            return severity
    return "medium"


def _extract_cost_limit(text: str) -> Optional[float]:
    """Extract a numeric cost limit from text like 'max $5.00' or 'limit to 2.50'."""
    pattern = r"\$?\s*(\d+(?:\.\d+)?)"
    match = re.search(pattern, text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _extract_keywords_list(text: str) -> list[str]:
    """Extract a list of quoted words from text like 'words "foo", "bar"'."""
    return re.findall(r'"([^"]+)"', text)


def _make_rule_name(action: str, subject: str, target: str) -> str:
    """Generate a slug rule name from action, subject, and target."""
    parts = [action, subject.replace(" ", "-")]
    if target and target != "any":
        parts.append(target.replace("_", "-"))
    return "-".join(p for p in parts if p)


class NlCompiler:
    """Compile natural language policy statements to structured policy YAML.

    Supports statements like:
    - "Block PII in responses"
    - "Audit all tool calls"
    - "Rate limit requests to $5.00 per call"
    - "Block keywords 'foo', 'bar' in requests"
    - "Deny unauthorized role access"
    - "Allow only admin role"

    Parameters
    ----------
    policy_name:
        Default name used when creating policies.  Can be overridden per call.
    strict:
        When True, raise NlCompilerError if a statement cannot be parsed.
        When False, add a warning and skip the statement.

    Example
    -------
    ::

        compiler = NlCompiler()
        result = compiler.compile_many([
            "Block PII in responses",
            "Audit all tool calls",
        ], policy_name="my-policy")
        print(result.to_yaml())
    """

    def __init__(
        self,
        *,
        policy_name: str = "generated-policy",
        strict: bool = False,
    ) -> None:
        self._default_policy_name = policy_name
        self._strict = strict

    def parse_statement(self, statement: str) -> ParsedStatement:
        """Parse a single natural language statement into a ParsedStatement.

        Parameters
        ----------
        statement:
            A plain English policy statement.

        Returns
        -------
        ParsedStatement
            Parsed intermediate representation.

        Raises
        ------
        NlCompilerError
            If strict mode is enabled and the statement cannot be parsed.
        """
        cleaned = statement.strip()
        text_lower = cleaned.lower()

        action = _extract_action(text_lower)
        subject, _rule_type, params = _extract_subject(text_lower)
        target = _extract_target(text_lower)
        severity = _extract_severity(text_lower)

        # Enhance params with extracted values
        if subject == "cost":
            cost_limit = _extract_cost_limit(cleaned)
            if cost_limit is not None:
                params["max_cost"] = cost_limit

        if subject == "keywords":
            keyword_list = _extract_keywords_list(cleaned)
            if keyword_list:
                params["keywords"] = keyword_list

        confidence = 1.0 if subject else 0.3
        if not subject and self._strict:
            raise NlCompilerError(
                f"Cannot determine policy subject from statement: {statement!r}"
            )

        return ParsedStatement(
            raw_text=cleaned,
            action=action,
            subject=subject,
            target=target,
            parameters={**params, "severity": severity},
            confidence=confidence,
        )

    def compile_statement(self, statement: str) -> Optional[CompiledRule]:
        """Compile a single natural language statement to a CompiledRule.

        Returns None if the statement cannot be compiled and strict=False.

        Raises
        ------
        NlCompilerError
            If strict=True and compilation fails.
        """
        text_lower = statement.strip().lower()
        subject, rule_type, default_params = _extract_subject(text_lower)
        action = _extract_action(text_lower)
        target = _extract_target(text_lower)
        severity = _extract_severity(text_lower)

        if not subject:
            if self._strict:
                raise NlCompilerError(
                    f"Cannot determine rule subject from: {statement!r}"
                )
            return None

        params = dict(default_params)

        # Enhance params from statement
        if subject == "cost":
            cost_limit = _extract_cost_limit(statement)
            if cost_limit is not None:
                params["max_cost"] = cost_limit

        if subject == "keywords":
            keyword_list = _extract_keywords_list(statement)
            if keyword_list:
                params["keywords"] = keyword_list

        rule_name = _make_rule_name(action, subject, target)

        return CompiledRule(
            name=rule_name,
            rule_type=rule_type,
            action=action,
            target=target,
            severity=severity,
            params=params,
        )

    def compile(
        self,
        statement: str,
        *,
        policy_name: Optional[str] = None,
        description: str = "",
    ) -> CompiledPolicy:
        """Compile a single statement into a one-rule policy.

        Parameters
        ----------
        statement:
            Natural language policy statement.
        policy_name:
            Override for the policy name.
        description:
            Optional policy description.

        Returns
        -------
        CompiledPolicy
            Policy with one compiled rule (or zero rules if compilation failed).
        """
        name = policy_name or self._default_policy_name
        policy = CompiledPolicy(
            name=name,
            description=description or f"Policy generated from: {statement}",
            source_statements=[statement],
        )
        rule = self.compile_statement(statement)
        if rule is not None:
            policy.rules.append(rule)
        else:
            policy.warnings.append(f"Could not compile statement: {statement!r}")
        return policy

    def compile_many(
        self,
        statements: list[str],
        *,
        policy_name: Optional[str] = None,
        description: str = "",
    ) -> CompiledPolicy:
        """Compile multiple statements into a single multi-rule policy.

        Parameters
        ----------
        statements:
            List of natural language policy statements.
        policy_name:
            Override for the policy name.
        description:
            Optional policy description.

        Returns
        -------
        CompiledPolicy
            Policy aggregating all successfully compiled rules.
        """
        name = policy_name or self._default_policy_name
        policy = CompiledPolicy(
            name=name,
            description=description or "Policy generated from natural language statements.",
            source_statements=list(statements),
        )

        seen_names: set[str] = set()
        for statement in statements:
            rule = self.compile_statement(statement)
            if rule is None:
                policy.warnings.append(f"Could not compile statement: {statement!r}")
                continue

            # Deduplicate rule names
            original_name = rule.name
            counter = 1
            while rule.name in seen_names:
                rule.name = f"{original_name}-{counter}"
                counter += 1
            seen_names.add(rule.name)
            policy.rules.append(rule)

        return policy

    def compile_text_block(
        self,
        text: str,
        *,
        policy_name: Optional[str] = None,
        description: str = "",
    ) -> CompiledPolicy:
        """Compile a multi-line text block where each line is a statement.

        Empty lines and lines starting with ``#`` are treated as comments and
        skipped.

        Parameters
        ----------
        text:
            Multi-line string with one statement per line.
        policy_name:
            Override for the policy name.
        description:
            Optional policy description.
        """
        statements = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        return self.compile_many(
            statements,
            policy_name=policy_name,
            description=description,
        )
