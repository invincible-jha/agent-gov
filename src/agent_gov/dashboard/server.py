"""HTTP web dashboard server for agent-gov.

Extends the existing compliance API with a full single-page web dashboard
(policy rules table, audit log viewer, compliance gauge, framework matrix)
using only the Python standard library.  No external web frameworks required.

Usage
-----
::

    from agent_gov.dashboard.server import WebDashboardServer

    server = WebDashboardServer(
        collector=collector,
        scorer=scorer,
        generator=generator,
        host="127.0.0.1",
        port=8084,
    )
    server.start()  # blocks; Ctrl-C to stop
"""
from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

if TYPE_CHECKING:
    from agent_gov.dashboard.evidence_collector import EvidenceCollector
    from agent_gov.dashboard.posture_scorer import PostureScorer
    from agent_gov.dashboard.report_generator import ReportGenerator

_STATIC_DIR = Path(__file__).parent / "static"

# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------


def _build_web_handler(
    collector: EvidenceCollector,
    scorer: PostureScorer,
    generator: ReportGenerator,
) -> type[BaseHTTPRequestHandler]:
    """Build an HTTP request handler bound to the given compliance services."""

    class _Handler(BaseHTTPRequestHandler):
        _collector = collector
        _scorer = scorer
        _generator = generator

        def log_message(self, fmt: str, *args: object) -> None:  # pragma: no cover
            pass

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            params = parse_qs(parsed.query)

            # Static files
            if path == "/" or path == "/index.html":
                self._serve_static("index.html")
            elif path == "/app.js":
                self._serve_static("app.js")
            elif path == "/styles.css":
                self._serve_static("styles.css")

            # Health
            elif path == "/health":
                self._send_json(200, {
                    "status": "ok",
                    "service": "agent-gov-dashboard",
                    "entries": self._collector.count,
                })

            # Policies list
            elif path == "/api/policies":
                policy_ids = self._collector.policy_ids()
                evidence = self._collector.all_entries()
                policies: list[dict[str, object]] = []
                for policy_id in policy_ids:
                    entries = self._collector.query(policy_id=policy_id)
                    pass_count = sum(1 for e in entries if e.result == "pass")
                    fail_count = sum(1 for e in entries if e.result == "fail")
                    skip_count = sum(1 for e in entries if e.result == "skip")
                    total = len(entries)
                    policies.append({
                        "policy_id": policy_id,
                        "total": total,
                        "pass": pass_count,
                        "fail": fail_count,
                        "skip": skip_count,
                        "pass_rate": round(pass_count / total, 3) if total else 0.0,
                        "status": "pass" if fail_count == 0 else "fail",
                    })
                # Global stats
                total_evidence = len(evidence)
                total_pass = sum(1 for e in evidence if e.result == "pass")
                total_fail = sum(1 for e in evidence if e.result == "fail")
                self._send_json(200, {
                    "policies": policies,
                    "total_policies": len(policies),
                    "total_evidence": total_evidence,
                    "global_pass_rate": round(total_pass / total_evidence, 3) if total_evidence else 0.0,
                    "global_fail_count": total_fail,
                })

            # Audit log
            elif path == "/api/audit":
                policy_id = (params.get("policy_id") or [None])[0]
                rule_id = (params.get("rule_id") or [None])[0]
                result_filter = (params.get("result") or [None])[0]
                limit = int((params.get("limit") or ["200"])[0])
                entries = self._collector.query(
                    policy_id=policy_id,
                    rule_id=rule_id,
                    result=result_filter,
                )
                entries_list = [e.to_dict() for e in entries[-limit:]]
                self._send_json(200, {
                    "entries": entries_list,
                    "count": len(entries_list),
                    "total": self._collector.count,
                })

            # Compliance posture / gauge
            elif path == "/api/compliance":
                evidence = self._collector.all_entries()
                posture = self._scorer.score(evidence)
                posture_dict = posture.to_dict()
                # Framework coverage matrix
                framework_coverage: dict[str, object] = {}
                for policy_id in self._collector.policy_ids():
                    policy_evidence = self._collector.query(policy_id=policy_id)
                    total = len(policy_evidence)
                    pass_count = sum(1 for e in policy_evidence if e.result == "pass")
                    framework_coverage[policy_id] = {
                        "total": total,
                        "pass": pass_count,
                        "coverage_pct": round(pass_count / total * 100, 1) if total else 0.0,
                    }
                posture_dict["framework_coverage"] = framework_coverage
                self._send_json(200, posture_dict)

            # Legacy posture endpoint (backwards compat)
            elif path == "/api/posture":
                evidence = self._collector.all_entries()
                posture = self._scorer.score(evidence)
                self._send_json(200, posture.to_dict())

            # Evidence (legacy endpoint)
            elif path == "/api/evidence":
                policy_id = (params.get("policy_id") or [None])[0]
                rule_id = (params.get("rule_id") or [None])[0]
                result_filter = (params.get("result") or [None])[0]
                entries = self._collector.query(
                    policy_id=policy_id,
                    rule_id=rule_id,
                    result=result_filter,
                )
                self._send_json(200, {
                    "count": len(entries),
                    "entries": [e.to_dict() for e in entries],
                })

            else:
                self._send_json(404, {"error": "Not found", "path": path})

        def _serve_static(self, filename: str) -> None:
            file_path = _STATIC_DIR / filename
            if not file_path.exists():
                self._send_json(404, {"error": f"Static file not found: {filename}"})
                return
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or "application/octet-stream"
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status: int, data: dict[str, object]) -> None:
            body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)

    return _Handler


# ---------------------------------------------------------------------------
# Server wrapper
# ---------------------------------------------------------------------------


class WebDashboardServer:
    """Agent-gov full web dashboard server.

    Extends the compliance API with a single-page HTML dashboard.

    Parameters
    ----------
    collector:
        Evidence collector instance.
    scorer:
        Posture scorer instance.
    generator:
        Report generator instance.
    host:
        Bind host (default ``"127.0.0.1"``).
    port:
        Bind port (default ``8084``).
    """

    def __init__(
        self,
        collector: EvidenceCollector,
        scorer: PostureScorer,
        generator: ReportGenerator,
        host: str = "127.0.0.1",
        port: int = 8084,
    ) -> None:
        self._collector = collector
        self._scorer = scorer
        self._generator = generator
        self._host = host
        self._port = port
        self._server: HTTPServer | None = None

    def build_server(self) -> HTTPServer:
        """Build and return the underlying ``HTTPServer`` without starting it."""
        handler_cls = _build_web_handler(self._collector, self._scorer, self._generator)
        server = HTTPServer((self._host, self._port), handler_cls)
        self._server = server
        return server

    def start(self) -> None:
        """Start the HTTP server and block until interrupted."""
        server = self.build_server()
        try:
            server.serve_forever()
        finally:
            server.server_close()

    def shutdown(self) -> None:
        """Stop the server if it is running."""
        if self._server is not None:
            self._server.shutdown()

    @property
    def address(self) -> str:
        """Return the server's bind address as ``host:port``."""
        return f"{self._host}:{self._port}"


__all__ = [
    "WebDashboardServer",
]
