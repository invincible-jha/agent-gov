"""Simple HTTP dashboard server for the live compliance dashboard.

Provides a minimal read-only HTTP interface over the compliance data
using the Python standard library ``http.server`` module.  No FastAPI
or third-party HTTP frameworks are required.

Optional FastAPI integration
-----------------------------
If FastAPI is installed in the environment, callers can import
:func:`create_fastapi_app` to get an ASGI app instead.  This is
detected at import time — the module never hard-requires FastAPI.

Usage (stdlib server)
---------------------
::

    from agent_gov.dashboard.dashboard_server import DashboardServer

    server = DashboardServer(collector=collector, scorer=scorer, host="127.0.0.1", port=8765)
    server.serve_forever()  # blocks; use serve_once() for single-request tests
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING
from urllib.parse import urlparse, parse_qs

if TYPE_CHECKING:
    from agent_gov.dashboard.evidence_collector import EvidenceCollector
    from agent_gov.dashboard.posture_scorer import PostureScorer
    from agent_gov.dashboard.report_generator import ReportGenerator


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------


def _build_handler(
    collector: EvidenceCollector,
    scorer: PostureScorer,
    generator: ReportGenerator,
) -> type[BaseHTTPRequestHandler]:
    """Build a ``BaseHTTPRequestHandler`` subclass bound to the given services.

    Parameters
    ----------
    collector:
        Evidence collector instance.
    scorer:
        Posture scorer instance.
    generator:
        Report generator instance.

    Returns
    -------
    type[BaseHTTPRequestHandler]
        A request handler class with the services in closure.
    """

    class _Handler(BaseHTTPRequestHandler):
        """Handles GET requests for the compliance dashboard API."""

        _collector = collector
        _scorer = scorer
        _generator = generator

        def log_message(self, fmt: str, *args: object) -> None:
            """Suppress default access log output."""
            pass  # noqa: PIE790

        def do_GET(self) -> None:  # noqa: N802
            """Route GET requests to the appropriate endpoint."""
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")
            params = parse_qs(parsed.query)

            if path == "" or path == "/":
                self._handle_root()
            elif path == "/health":
                self._handle_health()
            elif path == "/api/posture":
                self._handle_posture()
            elif path == "/api/evidence":
                self._handle_evidence(params)
            elif path == "/api/report/json":
                self._handle_report_json()
            elif path == "/api/report/markdown":
                self._handle_report_markdown()
            elif path == "/api/policies":
                self._handle_policies()
            else:
                self._send_json(404, {"error": "Not found", "path": path})

        # ------------------------------------------------------------------
        # Endpoint handlers
        # ------------------------------------------------------------------

        def _handle_root(self) -> None:
            """Return an index of available API endpoints."""
            data = {
                "service": "agent-gov compliance dashboard",
                "endpoints": [
                    "/health",
                    "/api/posture",
                    "/api/evidence",
                    "/api/evidence?policy_id=<id>",
                    "/api/evidence?result=pass|fail|skip",
                    "/api/report/json",
                    "/api/report/markdown",
                    "/api/policies",
                ],
            }
            self._send_json(200, data)

        def _handle_health(self) -> None:
            """Return a simple health check response."""
            self._send_json(200, {"status": "ok", "entries": self._collector.count})

        def _handle_posture(self) -> None:
            """Return the current posture score."""
            evidence = self._collector.all_entries()
            posture = self._scorer.score(evidence)
            self._send_json(200, posture.to_dict())

        def _handle_evidence(self, params: dict[str, list[str]]) -> None:
            """Return filtered evidence entries."""
            policy_id = (params.get("policy_id") or [None])[0]
            rule_id = (params.get("rule_id") or [None])[0]
            result = (params.get("result") or [None])[0]

            entries = self._collector.query(
                policy_id=policy_id,
                rule_id=rule_id,
                result=result,
            )
            data = {
                "count": len(entries),
                "entries": [e.to_dict() for e in entries],
            }
            self._send_json(200, data)

        def _handle_report_json(self) -> None:
            """Return the full JSON compliance report."""
            evidence = self._collector.all_entries()
            posture = self._scorer.score(evidence)
            report = self._generator.generate_json(evidence, posture)
            self._send_json(200, report)

        def _handle_report_markdown(self) -> None:
            """Return the Markdown compliance report."""
            evidence = self._collector.all_entries()
            posture = self._scorer.score(evidence)
            md = self._generator.generate_markdown(evidence, posture)
            self._send_response(200, md.encode("utf-8"), content_type="text/markdown; charset=utf-8")

        def _handle_policies(self) -> None:
            """Return the list of known policy IDs."""
            self._send_json(200, {"policies": self._collector.policy_ids()})

        # ------------------------------------------------------------------
        # Response helpers
        # ------------------------------------------------------------------

        def _send_json(self, status: int, data: dict[str, object]) -> None:
            """Serialize *data* to JSON and send as HTTP response."""
            body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
            self._send_response(status, body, content_type="application/json; charset=utf-8")

        def _send_response(
            self,
            status: int,
            body: bytes,
            content_type: str = "text/plain; charset=utf-8",
        ) -> None:
            """Send a raw HTTP response."""
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)

    return _Handler


# ---------------------------------------------------------------------------
# Server wrapper
# ---------------------------------------------------------------------------


class DashboardServer:
    """Compliance dashboard HTTP server.

    Wraps Python's built-in ``HTTPServer`` with a minimal read-only API
    for the compliance dashboard.

    Parameters
    ----------
    collector:
        The evidence collector to serve data from.
    scorer:
        Posture scorer instance.
    generator:
        Report generator instance.
    host:
        Bind host (default ``"127.0.0.1"``).
    port:
        Bind port (default ``8765``).
    """

    def __init__(
        self,
        collector: EvidenceCollector,
        scorer: PostureScorer,
        generator: ReportGenerator,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self._collector = collector
        self._scorer = scorer
        self._generator = generator
        self._host = host
        self._port = port
        self._server: HTTPServer | None = None

    def build_server(self) -> HTTPServer:
        """Build and return the underlying ``HTTPServer`` without starting it.

        Returns
        -------
        HTTPServer
        """
        handler_cls = _build_handler(self._collector, self._scorer, self._generator)
        server = HTTPServer((self._host, self._port), handler_cls)
        self._server = server
        return server

    def serve_forever(self) -> None:
        """Start the HTTP server and block until interrupted.

        Raises
        ------
        KeyboardInterrupt
            Propagated from the underlying server; triggers clean shutdown.
        """
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


# ---------------------------------------------------------------------------
# Optional FastAPI integration
# ---------------------------------------------------------------------------


def create_fastapi_app(
    collector: EvidenceCollector,
    scorer: PostureScorer,
    generator: ReportGenerator,
) -> object:
    """Create a FastAPI ASGI application for the compliance dashboard.

    This function is provided as an *optional* integration point.  It
    requires ``fastapi`` to be installed.  When not available, raises
    ``ImportError`` with a helpful message.

    Parameters
    ----------
    collector:
        Evidence collector instance.
    scorer:
        Posture scorer instance.
    generator:
        Report generator instance.

    Returns
    -------
    fastapi.FastAPI
        ASGI application.

    Raises
    ------
    ImportError
        When ``fastapi`` is not installed.
    """
    try:
        import fastapi  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "FastAPI is not installed.  Install it with: pip install fastapi"
        ) from exc

    app = fastapi.FastAPI(title="agent-gov Compliance Dashboard")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "entries": collector.count}

    @app.get("/api/posture")
    def posture() -> dict[str, object]:
        evidence = collector.all_entries()
        return scorer.score(evidence).to_dict()

    @app.get("/api/evidence")
    def evidence_endpoint(
        policy_id: str | None = None,
        rule_id: str | None = None,
        result: str | None = None,
    ) -> dict[str, object]:
        entries = collector.query(policy_id=policy_id, rule_id=rule_id, result=result)
        return {"count": len(entries), "entries": [e.to_dict() for e in entries]}

    @app.get("/api/report/json")
    def report_json() -> dict[str, object]:
        evidence = collector.all_entries()
        score = scorer.score(evidence)
        return generator.generate_json(evidence, score)

    @app.get("/api/policies")
    def policies() -> dict[str, object]:
        return {"policies": collector.policy_ids()}

    return app


__all__ = [
    "DashboardServer",
    "create_fastapi_app",
]
