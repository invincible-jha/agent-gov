/**
 * @aumos/agent-gov
 *
 * TypeScript client for the AumOS agent-gov governance framework.
 * Provides policy evaluation, compliance checking, audit logging,
 * and cost-of-compliance reporting.
 */

// Client and configuration
export type { AgentGovClient, AgentGovClientConfig } from "./client.js";
export { createAgentGovClient } from "./client.js";

// Core governance types
export type {
  Severity,
  ComplianceFramework,
  AutomationLevel,
  AuditVerdict,
  PolicyRule,
  GovernanceConfig,
  RuleVerdict,
  ComplianceReport,
  AuditEntry,
  RequirementCostDetail,
  ComplianceCostReport,
  CheckComplianceRequest,
  ValidatePolicyRequest,
  ValidatePolicyResponse,
  GenerateReportRequest,
  AuditLogQuery,
  ApiError,
  ApiResult,
} from "./types.js";
