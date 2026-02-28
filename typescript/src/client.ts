/**
 * HTTP client for the agent-gov governance API.
 *
 * Uses the Fetch API (available natively in Node 18+, browsers, and Deno).
 * No external dependencies required.
 *
 * @example
 * ```ts
 * import { createAgentGovClient } from "@aumos/agent-gov";
 *
 * const client = createAgentGovClient({ baseUrl: "http://localhost:8070" });
 *
 * const result = await client.checkCompliance({
 *   agent_id: "my-agent",
 *   policy_name: "default",
 *   action: { type: "search", query: "user emails" },
 * });
 *
 * if (result.ok && result.data.passed) {
 *   console.log("Action approved by governance policy");
 * }
 * ```
 */

import type {
  ApiError,
  ApiResult,
  AuditEntry,
  AuditLogQuery,
  CheckComplianceRequest,
  ComplianceCostReport,
  ComplianceReport,
  GenerateReportRequest,
  ValidatePolicyRequest,
  ValidatePolicyResponse,
} from "./types.js";

// ---------------------------------------------------------------------------
// Client configuration
// ---------------------------------------------------------------------------

/** Configuration options for the AgentGovClient. */
export interface AgentGovClientConfig {
  /** Base URL of the agent-gov server (e.g. "http://localhost:8070"). */
  readonly baseUrl: string;
  /** Optional request timeout in milliseconds (default: 30000). */
  readonly timeoutMs?: number;
  /** Optional extra HTTP headers sent with every request. */
  readonly headers?: Readonly<Record<string, string>>;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

async function fetchJson<T>(
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<ApiResult<T>> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    clearTimeout(timeoutId);

    const body = await response.json() as unknown;

    if (!response.ok) {
      const errorBody = body as Partial<ApiError>;
      return {
        ok: false,
        error: {
          error: errorBody.error ?? "Unknown error",
          detail: errorBody.detail ?? "",
        },
        status: response.status,
      };
    }

    return { ok: true, data: body as T };
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    const message = err instanceof Error ? err.message : String(err);
    return {
      ok: false,
      error: { error: "Network error", detail: message },
      status: 0,
    };
  }
}

function buildHeaders(
  extraHeaders: Readonly<Record<string, string>> | undefined,
): Record<string, string> {
  return {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...extraHeaders,
  };
}

// ---------------------------------------------------------------------------
// Client interface
// ---------------------------------------------------------------------------

/** Typed HTTP client for the agent-gov governance server. */
export interface AgentGovClient {
  /**
   * Evaluate an agent action against a named policy.
   *
   * Sends the action payload to the governance engine and returns a full
   * ComplianceReport with per-rule verdicts, pass/fail status, and severity.
   *
   * @param request - The agent ID, action payload, and target policy name.
   * @returns A ComplianceReport with all rule verdicts and an overall verdict.
   */
  checkCompliance(
    request: CheckComplianceRequest,
  ): Promise<ApiResult<ComplianceReport>>;

  /**
   * Retrieve the audit log with optional filtering.
   *
   * Returns entries in reverse chronological order (most recent first).
   *
   * @param query - Optional filter parameters (agentId, policyName, verdict, limit).
   * @returns Array of AuditEntry records matching the filter criteria.
   */
  getAuditLog(
    query?: AuditLogQuery,
  ): Promise<ApiResult<readonly AuditEntry[]>>;

  /**
   * Generate a cost-of-compliance report for a regulatory framework.
   *
   * Computes per-requirement cost estimates under the given automation
   * scenario and returns aggregated totals with savings percentages.
   *
   * @param request - Framework name, automation coverage overrides, and hourly rate.
   * @returns A ComplianceCostReport with full cost breakdown.
   */
  generateReport(
    request: GenerateReportRequest,
  ): Promise<ApiResult<ComplianceCostReport>>;

  /**
   * Validate a policy configuration without persisting it.
   *
   * Checks rule type references, parameter schemas, and structural
   * correctness. Returns a list of validation errors when the policy
   * is invalid.
   *
   * @param request - The full policy configuration to validate.
   * @returns Validation result with error messages and enabled rule count.
   */
  validatePolicy(
    request: ValidatePolicyRequest,
  ): Promise<ApiResult<ValidatePolicyResponse>>;
}

// ---------------------------------------------------------------------------
// Client factory
// ---------------------------------------------------------------------------

/**
 * Create a typed HTTP client for the agent-gov governance server.
 *
 * @param config - Client configuration including base URL.
 * @returns An AgentGovClient instance.
 */
export function createAgentGovClient(
  config: AgentGovClientConfig,
): AgentGovClient {
  const { baseUrl, timeoutMs = 30_000, headers: extraHeaders } = config;
  const baseHeaders = buildHeaders(extraHeaders);

  return {
    async checkCompliance(
      request: CheckComplianceRequest,
    ): Promise<ApiResult<ComplianceReport>> {
      return fetchJson<ComplianceReport>(
        `${baseUrl}/compliance/check`,
        {
          method: "POST",
          headers: baseHeaders,
          body: JSON.stringify(request),
        },
        timeoutMs,
      );
    },

    async getAuditLog(
      query: AuditLogQuery = {},
    ): Promise<ApiResult<readonly AuditEntry[]>> {
      const params = new URLSearchParams();
      if (query.agentId !== undefined) {
        params.set("agent_id", query.agentId);
      }
      if (query.policyName !== undefined) {
        params.set("policy_name", query.policyName);
      }
      if (query.verdict !== undefined) {
        params.set("verdict", query.verdict);
      }
      if (query.limit !== undefined) {
        params.set("limit", String(query.limit));
      }

      const queryString = params.toString();
      const url = queryString
        ? `${baseUrl}/audit/log?${queryString}`
        : `${baseUrl}/audit/log`;

      return fetchJson<readonly AuditEntry[]>(
        url,
        { method: "GET", headers: baseHeaders },
        timeoutMs,
      );
    },

    async generateReport(
      request: GenerateReportRequest,
    ): Promise<ApiResult<ComplianceCostReport>> {
      return fetchJson<ComplianceCostReport>(
        `${baseUrl}/compliance/report`,
        {
          method: "POST",
          headers: baseHeaders,
          body: JSON.stringify(request),
        },
        timeoutMs,
      );
    },

    async validatePolicy(
      request: ValidatePolicyRequest,
    ): Promise<ApiResult<ValidatePolicyResponse>> {
      return fetchJson<ValidatePolicyResponse>(
        `${baseUrl}/policies/validate`,
        {
          method: "POST",
          headers: baseHeaders,
          body: JSON.stringify(request),
        },
        timeoutMs,
      );
    },
  };
}

