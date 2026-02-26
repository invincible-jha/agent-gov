"""Role-based access control rule.

Checks that the agent performing the action holds at least one of the required
roles specified in the rule configuration.  Matching is string-based with
optional wildcard (``*``) support using :mod:`fnmatch`.

Configuration parameters
------------------------
required_roles : list[str]
    One or more role names that are sufficient to pass the check.
    Wildcards (``*``) are supported via :func:`fnmatch.fnmatchcase`.
agent_role_field : str
    Key in the action dict that contains the agent's role(s).
    May be a string or a list of strings.  Defaults to ``"agent_role"``.

Example config
--------------
.. code-block:: yaml

    type: role_check
    params:
      required_roles:
        - admin
        - "ops:*"
      agent_role_field: role
"""
from __future__ import annotations

import fnmatch

from agent_gov.policy.rule import PolicyRule, RuleVerdict


class RoleCheckRule(PolicyRule):
    """Verify the agent holds a required role before the action is allowed.

    Rule type name: ``role_check``
    """

    name: str = "role_check"

    def evaluate(
        self,
        action: dict[str, object],
        config: dict[str, object],
    ) -> RuleVerdict:
        """Check that the agent role satisfies at least one required role.

        Parameters
        ----------
        action:
            Must contain the key specified by ``agent_role_field`` (default
            ``"agent_role"``).  The value may be a ``str`` or ``list[str]``.
        config:
            Supported keys:
            - ``required_roles``: ``list[str]`` — roles that satisfy the check.
            - ``agent_role_field``: ``str`` — field name containing agent role(s).

        Returns
        -------
        RuleVerdict
            ``passed=False`` when the agent role does not match any required role.
        """
        required_roles: list[str] = _coerce_string_list(
            config.get("required_roles", [])
        )
        role_field: str = str(config.get("agent_role_field", "agent_role"))

        if not required_roles:
            return RuleVerdict(
                rule_name=self.name,
                passed=True,
                severity="medium",
                message="No required roles configured — check passes by default.",
            )

        raw_role = action.get(role_field)
        if raw_role is None:
            return RuleVerdict(
                rule_name=self.name,
                passed=False,
                severity="high",
                message=(
                    f"Action does not contain a role field {role_field!r}. "
                    "Cannot verify agent role."
                ),
                details={"role_field": role_field, "required_roles": required_roles},
            )

        agent_roles: list[str] = _coerce_string_list(raw_role)

        for agent_role in agent_roles:
            for required_pattern in required_roles:
                if fnmatch.fnmatchcase(agent_role, required_pattern):
                    return RuleVerdict(
                        rule_name=self.name,
                        passed=True,
                        severity="medium",
                        message=f"Agent role {agent_role!r} satisfies {required_pattern!r}.",
                        details={
                            "agent_roles": agent_roles,
                            "matched_pattern": required_pattern,
                        },
                    )

        return RuleVerdict(
            rule_name=self.name,
            passed=False,
            severity="high",
            message=(
                f"Agent role(s) {agent_roles!r} do not satisfy any required role "
                f"pattern(s): {required_roles!r}."
            ),
            details={
                "agent_roles": agent_roles,
                "required_roles": required_roles,
                "role_field": role_field,
            },
        )

    def validate_config(self, config: dict[str, object]) -> list[str]:
        """Validate that ``required_roles`` is a non-empty list of strings."""
        errors: list[str] = []
        required_roles = config.get("required_roles")
        if required_roles is None:
            errors.append("role_check: 'required_roles' is not configured.")
        elif not isinstance(required_roles, list):
            errors.append(
                f"role_check: 'required_roles' must be a list, got {type(required_roles).__name__}."
            )
        elif not required_roles:
            errors.append("role_check: 'required_roles' must not be empty.")
        return errors


def _coerce_string_list(value: object) -> list[str]:
    """Convert a string or list-of-strings to a guaranteed list of strings."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
