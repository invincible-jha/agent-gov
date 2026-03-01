/**
 * HTTP client for the agent-gov governance API.
 *
 * Delegates all HTTP transport to `@aumos/sdk-core` which provides
 * automatic retry with exponential back-off, timeout management via
 * `AbortSignal.timeout`, interceptor support, and a typed error hierarchy.
 *
 * The public-facing `ApiResult<T>` envelope is preserved for full
 * backward compatibility with existing callers.
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

import {
  createHttpClient,
  HttpError,
  NetworkError,
  TimeoutError,
  AumosError,
  type HttpClient,
} from "@aumos/sdk-core";

import type {
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
// Internal adapter — maps sdk-core ResponseData / errors to ApiResult
// ---------------------------------------------------------------------------

/**
 * Executes `operation` and normalises the result into an `ApiResult<T>`.
 *
 * Success: extracts `data` from the `ResponseData` envelope.
 * Failure: converts sdk-core typed errors into the legacy `ApiResult` shape.
 */
async function callApi<T>(
  operation: () => Promise<{ readonly data: T; readonly status: number }>,
): Promise<ApiResult<T>> {
  try {
    const response = await operation();
    return { ok: true, data: response.data };
  } catch (error: unknown) {
    if (error instanceof HttpError) {
      return {
        ok: false,
        error: { error: error.message, detail: String(error.body ?? "") },
        status: error.statusCode,
      };
    }
    if (error instanceof TimeoutError) {
      return {
        ok: false,
        error: { error: "Request timed out", detail: error.message },
        status: 0,
      };
    }
    if (error instanceof NetworkError) {
      return {
        ok: false,
        error: { error: "Network error", detail: error.message },
        status: 0,
      };
    }
    if (error instanceof AumosError) {
      return {
        ok: false,
        error: { error: error.code, detail: error.message },
        status: error.statusCode ?? 0,
      };
    }
    const message = error instanceof Error ? error.message : String(error);
    return {
      ok: false,
      error: { error: "Unexpected error", detail: message },
      status: 0,
    };
  }
}

// ---------------------------------------------------------------------------
// Client interface
// ---------------------------------------------------------------------------

/** Typed HTTP client for the agent-gov governance server. */
export interface AgentGovClient {
  /**
   * Evaluate an agent action against a named policy.
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
   * @param query - Optional filter parameters (agentId, policyName, verdict, limit).
   * @returns Array of AuditEntry records matching the filter criteria.
   */
  getAuditLog(
    query?: AuditLogQuery,
  ): Promise<ApiResult<readonly AuditEntry[]>>;

  /**
   * Generate a cost-of-compliance report for a regulatory framework.
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
  const http: HttpClient = createHttpClient({
    baseUrl: config.baseUrl,
    timeout: config.timeoutMs ?? 30_000,
    defaultHeaders: config.headers,
  });

  return {
    checkCompliance(
      request: CheckComplianceRequest,
    ): Promise<ApiResult<ComplianceReport>> {
      return callApi(() => http.post<ComplianceReport>("/compliance/check", request));
    },

    getAuditLog(
      query: AuditLogQuery = {},
    ): Promise<ApiResult<readonly AuditEntry[]>> {
      const queryParams: Record<string, string> = {};
      if (query.agentId !== undefined) queryParams["agent_id"] = query.agentId;
      if (query.policyName !== undefined) queryParams["policy_name"] = query.policyName;
      if (query.verdict !== undefined) queryParams["verdict"] = query.verdict;
      if (query.limit !== undefined) queryParams["limit"] = String(query.limit);
      return callApi(() =>
        http.get<readonly AuditEntry[]>("/audit/log", { queryParams }),
      );
    },

    generateReport(
      request: GenerateReportRequest,
    ): Promise<ApiResult<ComplianceCostReport>> {
      return callApi(() => http.post<ComplianceCostReport>("/compliance/report", request));
    },

    validatePolicy(
      request: ValidatePolicyRequest,
    ): Promise<ApiResult<ValidatePolicyResponse>> {
      return callApi(() => http.post<ValidatePolicyResponse>("/policies/validate", request));
    },
  };
}
