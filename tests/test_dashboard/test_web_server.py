"""Tests for agent_gov.dashboard.server — WebDashboardServer."""
from __future__ import annotations

import io
import json
from http.server import HTTPServer
from unittest.mock import MagicMock

import pytest

from agent_gov.dashboard.evidence_collector import EvidenceCollector, EvidenceEntry
from agent_gov.dashboard.posture_scorer import PostureScorer
from agent_gov.dashboard.report_generator import ReportGenerator
from agent_gov.dashboard.server import WebDashboardServer, _build_web_handler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_collector_with_entries() -> EvidenceCollector:
    """Return a populated EvidenceCollector for testing."""
    from datetime import datetime, timezone

    collector = EvidenceCollector()
    for policy, rule, result in [
        ("eu-ai-act", "A13", "pass"),
        ("eu-ai-act", "A9", "fail"),
        ("gdpr", "A17", "pass"),
        ("gdpr", "A35", "skip"),
    ]:
        collector.record(
            EvidenceEntry(
                timestamp=datetime.now(timezone.utc),
                policy_id=policy,
                rule_id=rule,
                result=result,
                context={},
            )
        )
    return collector


def _make_services() -> tuple[EvidenceCollector, PostureScorer, ReportGenerator]:
    collector = _make_collector_with_entries()
    scorer = PostureScorer()
    generator = ReportGenerator()
    return collector, scorer, generator


def _make_handler_and_output(
    path: str,
    collector: EvidenceCollector,
    scorer: PostureScorer,
    generator: ReportGenerator,
) -> tuple[object, io.BytesIO]:
    """Build a handler pointed at *path* and return the handler + output buffer."""
    handler_cls = _build_web_handler(collector, scorer, generator)

    output = io.BytesIO()
    request = MagicMock()
    server = MagicMock()
    server.server_address = ("127.0.0.1", 8084)

    handler = handler_cls.__new__(handler_cls)
    handler.request = request
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = server
    handler.rfile = io.BytesIO(b"")
    handler.wfile = output
    handler.path = path
    # Required by BaseHTTPRequestHandler.send_response / send_header
    handler.request_version = "HTTP/1.1"
    handler.requestline = f"GET {path} HTTP/1.1"
    handler.close_connection = True
    return handler, output


def _call_get(path: str) -> bytes:
    """Call do_GET on a fresh handler and return raw response bytes."""
    collector, scorer, generator = _make_services()
    handler, output = _make_handler_and_output(path, collector, scorer, generator)
    handler.do_GET()
    return output.getvalue()


def _call_get_json(path: str) -> dict[str, object]:
    """Call do_GET and parse the JSON body (skips HTTP headers)."""
    raw = _call_get(path)
    # Strip HTTP preamble (find first blank line, then JSON body follows)
    body_start = raw.find(b"\r\n\r\n")
    if body_start == -1:
        body_start = raw.find(b"\n\n")
        body = raw[body_start + 2 :]
    else:
        body = raw[body_start + 4 :]
    return json.loads(body)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_ok(self) -> None:
        data = _call_get_json("/health")
        assert data["status"] == "ok"

    def test_health_service_name(self) -> None:
        data = _call_get_json("/health")
        assert data["service"] == "agent-gov-dashboard"

    def test_health_includes_entry_count(self) -> None:
        data = _call_get_json("/health")
        assert "entries" in data
        assert isinstance(data["entries"], int)


# ---------------------------------------------------------------------------
# Static file serving
# ---------------------------------------------------------------------------


class TestStaticFiles:
    def test_root_returns_html_content(self) -> None:
        raw = _call_get("/")
        assert b"text/html" in raw or b"<!DOCTYPE html" in raw or b"<html" in raw

    def test_index_html_explicit(self) -> None:
        raw = _call_get("/index.html")
        assert b"agent" in raw.lower() or b"<html" in raw.lower()

    def test_styles_css_served(self) -> None:
        raw = _call_get("/styles.css")
        assert b"text/css" in raw or b"--bg" in raw

    def test_app_js_served(self) -> None:
        raw = _call_get("/app.js")
        assert b"javascript" in raw or b"function" in raw or b"const" in raw


# ---------------------------------------------------------------------------
# API: /api/policies
# ---------------------------------------------------------------------------


class TestPoliciesEndpoint:
    def test_policies_returns_list(self) -> None:
        data = _call_get_json("/api/policies")
        assert "policies" in data
        assert isinstance(data["policies"], list)

    def test_policies_total_count(self) -> None:
        data = _call_get_json("/api/policies")
        assert data["total_policies"] == 2  # eu-ai-act, gdpr

    def test_policies_have_pass_fail_counts(self) -> None:
        data = _call_get_json("/api/policies")
        for policy in data["policies"]:
            assert "pass" in policy
            assert "fail" in policy
            assert "pass_rate" in policy

    def test_policies_status_badge(self) -> None:
        data = _call_get_json("/api/policies")
        statuses = {p["policy_id"]: p["status"] for p in data["policies"]}
        # eu-ai-act has 1 fail
        assert statuses.get("eu-ai-act") == "fail"
        # gdpr has 0 fail (1 pass, 1 skip)
        assert statuses.get("gdpr") == "pass"


# ---------------------------------------------------------------------------
# API: /api/audit
# ---------------------------------------------------------------------------


class TestAuditEndpoint:
    def test_audit_returns_entries(self) -> None:
        data = _call_get_json("/api/audit")
        assert "entries" in data
        assert data["count"] >= 4

    def test_audit_filter_by_policy(self) -> None:
        data = _call_get_json("/api/audit?policy_id=eu-ai-act")
        assert all(e["policy_id"] == "eu-ai-act" for e in data["entries"])
        assert data["count"] == 2

    def test_audit_filter_by_result(self) -> None:
        data = _call_get_json("/api/audit?result=pass")
        assert all(e["result"] == "pass" for e in data["entries"])

    def test_audit_filter_fail_only(self) -> None:
        data = _call_get_json("/api/audit?result=fail")
        assert data["count"] == 1
        assert data["entries"][0]["rule_id"] == "A9"


# ---------------------------------------------------------------------------
# API: /api/compliance
# ---------------------------------------------------------------------------


class TestComplianceEndpoint:
    def test_compliance_returns_framework_coverage(self) -> None:
        data = _call_get_json("/api/compliance")
        assert "framework_coverage" in data
        coverage = data["framework_coverage"]
        assert "eu-ai-act" in coverage
        assert "gdpr" in coverage

    def test_compliance_coverage_has_required_fields(self) -> None:
        data = _call_get_json("/api/compliance")
        for fw_data in data["framework_coverage"].values():
            assert "total" in fw_data
            assert "pass" in fw_data
            assert "coverage_pct" in fw_data


# ---------------------------------------------------------------------------
# 404 handling
# ---------------------------------------------------------------------------


class TestNotFound:
    def test_unknown_path_returns_404(self) -> None:
        raw = _call_get("/api/nonexistent")
        assert b"404" in raw


# ---------------------------------------------------------------------------
# WebDashboardServer instantiation
# ---------------------------------------------------------------------------


class TestWebDashboardServer:
    def test_server_instantiates(self) -> None:
        collector, scorer, generator = _make_services()
        server = WebDashboardServer(collector=collector, scorer=scorer, generator=generator)
        assert server.address == "127.0.0.1:8084"

    def test_build_server_returns_http_server(self) -> None:
        collector, scorer, generator = _make_services()
        server = WebDashboardServer(
            collector=collector, scorer=scorer, generator=generator, port=0
        )
        http_server = server.build_server()
        try:
            assert isinstance(http_server, HTTPServer)
        finally:
            http_server.server_close()

    def test_custom_host_port(self) -> None:
        collector, scorer, generator = _make_services()
        server = WebDashboardServer(
            collector=collector, scorer=scorer, generator=generator,
            host="0.0.0.0", port=9999,
        )
        assert server.address == "0.0.0.0:9999"
