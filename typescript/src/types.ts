/**
 * TypeScript interfaces for the agent-gov governance framework.
 *
 * Mirrors the Pydantic/dataclass models defined in:
 *   agent_gov.policy.schema     — PolicyRule, PolicyConfig, RuleConfig
 *   agent_gov.policy.rule       — RuleVerdict
 *   agent_gov.policy.result     — EvaluationReport
 *   agent_gov.audit.entry       — AuditEntry
 *   agent_gov.compliance_cost.calculator — CostReport
 *
 * All interfaces use readonly fields to match Python frozen models.
 */

// ---------------------------------------------------------------------------
// Enumerations
// ---------------------------------------------------------------------------

/**
 * Severity levels for policy rule violations.
 * Maps to the Python Severity enum in agent_gov.policy.schema.
 */
export type Severity = "low" | "medium" | "high" | "critical";

/**
 * Compliance frameworks supported by the governance engine.
 * Each identifier maps to a built-in requirement catalogue.
 */
export type ComplianceFramework = "eu_ai_act" | "gdpr" | "hipaa" | "soc2";

/**
 * Automation level for a compliance requirement.
 * Controls how labour hours are estimated in cost calculations.
 */
export type AutomationLevel = "fully_automated" | "semi_automated" | "manual";

/**
 * Audit verdict — the outcome of a policy evaluation.
 */
export type AuditVerdict = "pass" | "fail";

// ---------------------------------------------------------------------------
// Policy rule types
// ---------------------------------------------------------------------------

/**
 * Configuration for a single rule within a policy.
 * Maps to RuleConfig in agent_gov.policy.schema.
 */
export interface PolicyRule {
  /** Human-readable label for this rule within the policy. */
  readonly name: string;
  /**
   * Rule type identifier — matches the rule class `name` attribute used
   * for rule registry lookup.
   */
  readonly type: string;
  /** When false the rule is skipped during evaluation. Default true. */
  readonly enabled: boolean;
  /** Default severity applied to verdicts produced by this rule. */
  readonly severity: Severity;
  /** Arbitrary key/value parameters forwarded to the rule evaluate call. */
  readonly params: Readonly<Record<string, unknown>>;
}

/**
 * Top-level policy configuration.
 * Maps to PolicyConfig in agent_gov.policy.schema.
 */
export interface GovernanceConfig {
  /** Unique identifier for this policy. */
  readonly name: string;
  /** Semantic version string for tracking policy changes. */
  readonly version: string;
  /** Free-text description of what this policy governs. */
  readonly description: string;
  /** Ordered list of rule configurations to evaluate. */
  readonly rules: readonly PolicyRule[];
  /** Arbitrary string key/value metadata (author, team, ticket, etc.). */
  readonly metadata: Readonly<Record<string, string>>;
}

// ---------------------------------------------------------------------------
// Rule verdict and evaluation report
// ---------------------------------------------------------------------------

/**
 * Result produced by a single rule evaluation.
 * Maps to RuleVerdict in agent_gov.policy.rule.
 */
export interface RuleVerdict {
  /** The name of the rule that produced this verdict. */
  readonly rule_name: string;
  /** True when the action satisfies the rule; false when it violates it. */
  readonly passed: boolean;
  /** Severity level of this verdict. */
  readonly severity: Severity;
  /** Human-readable explanation, typically set when passed is false. */
  readonly message: string;
  /** Arbitrary structured data providing additional context. */
  readonly details: Readonly<Record<string, unknown>>;
}

/**
 * Complete result of evaluating one action against a policy.
 * Maps to EvaluationReport in agent_gov.policy.result.
 */
export interface ComplianceReport {
  /** Name of the policy that generated this report. */
  readonly policy_name: string;
  /** The original action dictionary that was evaluated. */
  readonly action: Readonly<Record<string, unknown>>;
  /** One RuleVerdict per enabled rule that was evaluated. */
  readonly verdicts: readonly RuleVerdict[];
  /** True only when all verdicts report passed=true. */
  readonly passed: boolean;
  /** ISO-8601 UTC timestamp at which the evaluation completed. */
  readonly timestamp: string;
  /** Number of rules that flagged a violation. */
  readonly violation_count: number;
  /** Highest severity among all failed verdicts; "none" when no failures. */
  readonly highest_severity: Severity | "none";
}

// ---------------------------------------------------------------------------
// Audit log
// ---------------------------------------------------------------------------

/**
 * A single immutable audit log record.
 * Maps to AuditEntry in agent_gov.audit.entry.
 */
export interface AuditEntry {
  /** Unique identifier for the agent that performed the action. */
  readonly agent_id: string;
  /** Short category/type string for the action (e.g. "search", "write"). */
  readonly action_type: string;
  /** Full action payload as passed to the policy evaluator. */
  readonly action_data: Readonly<Record<string, unknown>>;
  /** Overall verdict: "pass" or "fail". */
  readonly verdict: AuditVerdict;
  /** Name of the policy that produced the verdict. */
  readonly policy_name: string;
  /** ISO-8601 UTC timestamp of the evaluation. */
  readonly timestamp: string;
  /** Arbitrary additional context (run ID, environment, etc.). */
  readonly metadata: Readonly<Record<string, string>>;
}

// ---------------------------------------------------------------------------
// Compliance cost types
// ---------------------------------------------------------------------------

/**
 * Per-requirement cost detail line within a CostReport.
 */
export interface RequirementCostDetail {
  /** Short unique identifier within the framework. */
  readonly requirement_id: string;
  /** Plain-language description of the requirement. */
  readonly description: string;
  /** Current automation level for this requirement. */
  readonly automation_level: AutomationLevel;
  /** Hours estimate when handled manually. */
  readonly hours_manual: number;
  /** Hours estimate under the current automation scenario. */
  readonly hours_automated: number;
  /** Cost in currency units under full manual mode. */
  readonly cost_manual: number;
  /** Cost in currency units under the current automation scenario. */
  readonly cost_automated: number;
  /** Cost saving from automation (cost_manual - cost_automated). */
  readonly savings: number;
}

/**
 * Cost-of-compliance report for a single framework and automation scenario.
 * Maps to CostReport in agent_gov.compliance_cost.calculator.
 */
export interface ComplianceCostReport {
  /** The regulatory framework being reported on. */
  readonly framework: ComplianceFramework | string;
  /** Total number of requirements in the framework. */
  readonly total_requirements: number;
  /** Count of requirements classified as fully_automated. */
  readonly automated_count: number;
  /** Count of semi_automated requirements. */
  readonly semi_automated_count: number;
  /** Count of manual requirements. */
  readonly manual_count: number;
  /** Sum of manual-mode hours across all requirements. */
  readonly total_hours_manual: number;
  /** Sum of automated-mode hours across all requirements. */
  readonly total_hours_automated: number;
  /** Total cost in currency units under fully manual mode. */
  readonly total_cost_manual: number;
  /** Total cost in currency units under the current automation scenario. */
  readonly total_cost_with_automation: number;
  /** Percentage cost reduction from automation. */
  readonly savings_percentage: number;
  /** Hourly rate used in the calculation. */
  readonly hourly_rate: number;
  /** Per-requirement cost detail lines. */
  readonly requirement_details: readonly RequirementCostDetail[];
}

// ---------------------------------------------------------------------------
// Request payload types
// ---------------------------------------------------------------------------

/**
 * Request body for the checkCompliance endpoint.
 */
export interface CheckComplianceRequest {
  /** Identifier of the agent performing the action. */
  readonly agent_id: string;
  /** The action payload to evaluate. */
  readonly action: Readonly<Record<string, unknown>>;
  /** Name of the policy to evaluate against. */
  readonly policy_name: string;
}

/**
 * Request body for the validatePolicy endpoint.
 */
export interface ValidatePolicyRequest {
  /** The full policy configuration to validate. */
  readonly policy: GovernanceConfig;
}

/**
 * Response from the validatePolicy endpoint. */
export interface ValidatePolicyResponse {
  /** Whether the policy configuration is valid. */
  readonly valid: boolean;
  /** Validation error messages; empty when valid. */
  readonly errors: readonly string[];
  /** Number of enabled rules in the policy. */
  readonly enabled_rule_count: number;
}

/**
 * Request body for the generateReport endpoint.
 */
export interface GenerateReportRequest {
  /** The regulatory framework to generate a cost report for. */
  readonly framework: ComplianceFramework | string;
  /** Automation level overrides per requirement_id. */
  readonly automation_coverage?: Readonly<Record<string, AutomationLevel>>;
  /** Hourly labour rate in currency units (default 150.0). */
  readonly hourly_rate?: number;
}

/**
 * Query parameters for the getAuditLog endpoint.
 */
export interface AuditLogQuery {
  /** Filter by agent ID. */
  readonly agentId?: string;
  /** Filter by policy name. */
  readonly policyName?: string;
  /** Filter by verdict. */
  readonly verdict?: AuditVerdict;
  /** Maximum number of entries to return (default 100). */
  readonly limit?: number;
}

// ---------------------------------------------------------------------------
// API result wrapper (shared pattern)
// ---------------------------------------------------------------------------

/** Standard error payload returned by the agent-gov API. */
export interface ApiError {
  readonly error: string;
  readonly detail: string;
}

/** Result type for all client operations. */
export type ApiResult<T> =
  | { readonly ok: true; readonly data: T }
  | { readonly ok: false; readonly error: ApiError; readonly status: number };
