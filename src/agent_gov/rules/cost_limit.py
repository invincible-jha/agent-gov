"""Cost limit rule — enforce per-action and aggregate spend thresholds.

Checks the numeric cost of an action against configurable per-action and
cumulative aggregate limits.  The aggregate check reads from a simple
in-memory accumulator within the rule instance; for multi-process deployments
the accumulator should be replaced with an external store.

Configuration parameters
------------------------
max_cost_per_action : float
    Maximum allowed cost for a single action.  ``0`` means unlimited.
    Defaults to ``0``.
max_cost_aggregate : float
    Maximum cumulative cost across all evaluated actions for this rule
    instance.  ``0`` means unlimited.  Defaults to ``0``.
cost_field : str
    Key in the action dict that holds the numeric cost value.
    Defaults to ``"cost"``.

Example config
--------------
.. code-block:: yaml

    type: cost_limit
    params:
      max_cost_per_action: 0.10
      max_cost_aggregate: 5.00
      cost_field: estimated_cost
"""
from __future__ import annotations

from agent_gov.policy.rule import PolicyRule, RuleVerdict


class CostLimitRule(PolicyRule):
    """Enforce per-action and aggregate cost thresholds.

    Rule type name: ``cost_limit``
    """

    name: str = "cost_limit"

    def __init__(self) -> None:
        self._aggregate_cost: float = 0.0

    def reset_aggregate(self) -> None:
        """Reset the in-memory aggregate cost accumulator to zero."""
        self._aggregate_cost = 0.0

    @property
    def aggregate_cost(self) -> float:
        """Return the current cumulative cost total."""
        return self._aggregate_cost

    def evaluate(
        self,
        action: dict[str, object],
        config: dict[str, object],
    ) -> RuleVerdict:
        """Check action cost against configured thresholds.

        Parameters
        ----------
        action:
            Must contain the key identified by ``cost_field`` (default
            ``"cost"``).  The value must be numeric (``int`` or ``float``).
            Missing cost field is treated as ``0.0``.
        config:
            Supported keys: ``max_cost_per_action``, ``max_cost_aggregate``,
            ``cost_field``.

        Returns
        -------
        RuleVerdict
            ``passed=False`` when either threshold is exceeded.
        """
        cost_field: str = str(config.get("cost_field", "cost"))
        max_per_action: float = float(config.get("max_cost_per_action", 0))
        max_aggregate: float = float(config.get("max_cost_aggregate", 0))

        raw_cost = action.get(cost_field, 0)
        try:
            action_cost = float(raw_cost)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return RuleVerdict(
                rule_name=self.name,
                passed=False,
                severity="medium",
                message=(
                    f"Cost field {cost_field!r} has non-numeric value "
                    f"{raw_cost!r}; cannot evaluate cost limit."
                ),
                details={"cost_field": cost_field, "raw_value": str(raw_cost)},
            )

        if action_cost < 0:
            return RuleVerdict(
                rule_name=self.name,
                passed=False,
                severity="medium",
                message=f"Cost value {action_cost} is negative; invalid cost.",
                details={"action_cost": action_cost},
            )

        # Per-action check
        if max_per_action > 0 and action_cost > max_per_action:
            return RuleVerdict(
                rule_name=self.name,
                passed=False,
                severity="high",
                message=(
                    f"Action cost {action_cost:.4f} exceeds per-action limit "
                    f"{max_per_action:.4f}."
                ),
                details={
                    "action_cost": action_cost,
                    "max_cost_per_action": max_per_action,
                    "aggregate_cost": self._aggregate_cost,
                },
            )

        # Aggregate check (evaluated before accumulating)
        projected_aggregate = self._aggregate_cost + action_cost
        if max_aggregate > 0 and projected_aggregate > max_aggregate:
            return RuleVerdict(
                rule_name=self.name,
                passed=False,
                severity="high",
                message=(
                    f"Cumulative cost {projected_aggregate:.4f} would exceed "
                    f"aggregate limit {max_aggregate:.4f}."
                ),
                details={
                    "action_cost": action_cost,
                    "aggregate_cost": self._aggregate_cost,
                    "projected_aggregate": projected_aggregate,
                    "max_cost_aggregate": max_aggregate,
                },
            )

        # Accumulate only after passing both checks
        self._aggregate_cost += action_cost

        return RuleVerdict(
            rule_name=self.name,
            passed=True,
            severity="medium",
            message=f"Cost {action_cost:.4f} within limits.",
            details={
                "action_cost": action_cost,
                "aggregate_cost": self._aggregate_cost,
            },
        )

    def validate_config(self, config: dict[str, object]) -> list[str]:
        """Validate cost threshold values are non-negative numbers."""
        errors: list[str] = []
        for key in ("max_cost_per_action", "max_cost_aggregate"):
            value = config.get(key)
            if value is not None:
                try:
                    if float(value) < 0:  # type: ignore[arg-type]
                        errors.append(f"cost_limit: {key!r} must be non-negative.")
                except (TypeError, ValueError):
                    errors.append(f"cost_limit: {key!r} must be a number, got {value!r}.")
        return errors
