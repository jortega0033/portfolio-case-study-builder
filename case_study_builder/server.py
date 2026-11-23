"""Loopback-only HTTP server for the case study builder."""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .storage import NotFound, RevisionConflict, Storage
from .validation import ValidationError, validate_project_payload

MAX_BODY_BYTES = 262144
STATIC_DIR = Path(__file__).resolve().parent / "static"
_ID_RE = re.compile(r"[0-9a-f]{32}\Z")
_PROJECT_PATH_RE = re.compile(r"/api/v1/projects/([^/]+)\Z")

CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
       "img-src 'self' data:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")

STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/static/tokens.css": ("tokens.css", "text/css; charset=utf-8"),
    "/static/app.css": ("app.css", "text/css; charset=utf-8"),
    "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
}

_STATUS_FOR_CODE = {
    "invalid_json": 400, "invalid_field": 400, "forbidden_host": 403,
    "forbidden_origin": 403, "not_found": 404, "method_not_allowed": 405,
    "revision_conflict": 409, "length_required": 411, "payload_too_large": 413,
    "unsupported_media_type": 415, "internal_error": 500,
}


class ApiError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None,
                 headers: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.headers = headers or {}


def _reject_constant(name):
    raise ValueError("non-standard JSON constant")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "CaseStudyBuilder"
    sys_version = ""

    # -- plumbing ---------------------------------------------------------
    def log_message(self, format, *args):  # quiet; never log user content
        pass

    def _send(self, status: int, body: bytes, content_type: str,
              extra: dict | None = None, api: bool = True) -> None:
        if self.command in ("POST", "PUT") and not getattr(self, "_body_read", False):
            self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        if self.close_connection:
            self.send_header("Connection", "close")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, obj, extra: dict | None = None) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(status, data, "application/json; charset=utf-8", extra)

    def _error(self, err: ApiError) -> None:
        status = _STATUS_FOR_CODE.get(err.code, 400)
        self._json(status, {"error": {"code": err.code, "message": err.message,
                                      "details": err.details}}, err.headers)

    # -- dispatch ---------------------------------------------------------
    def _handle(self) -> None:
        self._body_read = False
        try:
            self._route()
        except ApiError as e:
            self._error(e)
        except ValidationError as e:
            self._error(ApiError(e.code, e.message, e.details))
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except Exception:
            try:
                self._error(ApiError("internal_error", "Internal server error"))
            except Exception:
                self.close_connection = True

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = _handle

    def _check_host(self) -> str:
        host = self.headers.get("Host", "")
        port = self.server.server_address[1]
        if host.lower() not in (f"127.0.0.1:{port}", f"localhost:{port}"):
            raise ApiError("forbidden_host", "Host not allowed")
        return host

    def _route(self) -> None:
        host = self._check_host()
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        method = self.command

        allow = None
        project_id = None
        if path in STATIC_FILES:
            allow = "GET"
        elif path == "/api/v1/health":
            allow = "GET"
        elif path == "/api/v1/projects":
            allow = "GET, POST"
        else:
            m = _PROJECT_PATH_RE.match(path)
            if m and _ID_RE.match(m.group(1)):
                project_id = m.group(1)
                allow = "GET, PUT"
        if allow is None:
            raise ApiError("not_found", "Not found")
        if method not in [a.strip() for a in allow.split(",")]:
            raise ApiError("method_not_allowed", "Method not allowed", headers={"Allow": allow})

        if method in ("POST", "PUT"):
            origin = self.headers.get("Origin")
            if origin is None or origin.lower() != f"http://{host}".lower():
                raise ApiError("forbidden_origin", "Origin not allowed")

        storage: Storage = self.server.storage
        if path in STATIC_FILES:
            return self._static(path)
        if path == "/api/v1/health":
            return self._json(200, {"status": "ok", "schema_version": 1})
        if path == "/api/v1/projects":
            if method == "GET":
                return self._json(200, {"projects": storage.list_projects()})
            data = validate_project_payload(self._read_json(), require_revision=False)
            proj = storage.create_project(data["title"], data["sections"])
            return self._json(201, proj, {"Location": f"/api/v1/projects/{proj['id']}"})
        if method == "GET":
            try:
                return self._json(200, storage.get_project(project_id))
            except NotFound:
                raise ApiError("not_found", "Project not found") from None
        data = validate_project_payload(self._read_json(), require_revision=True)
        try:
            proj = storage.update_project(project_id, data["title"], data["sections"],
                                          data["base_revision"])
        except NotFound:
            raise ApiError("not_found", "Project not found") from None
        except RevisionConflict as e:
            raise ApiError("revision_conflict",
                           "Project was modified; reload to get the latest revision",
                           {"current_revision": e.current_revision}) from None
        return self._json(200, proj)

    def _static(self, path: str) -> None:
        name, ctype = STATIC_FILES[path]
        try:
            data = (STATIC_DIR / name).read_bytes()
        except OSError:
            raise ApiError("not_found", "Not found") from None
        self._send(200, data, ctype, api=False)

    def _read_json(self):
        ctype = self.headers.get("Content-Type", "")
        if ctype.split(";", 1)[0].strip().lower() != "application/json":
            raise ApiError("unsupported_media_type", "Content-Type must be application/json")
        if self.headers.get("Transfer-Encoding") is not None:
            raise ApiError("length_required", "Chunked bodies are not supported")
        raw = self.headers.get("Content-Length")
        if raw is None or not raw.strip().isascii() or not raw.strip().isdigit():
            raise ApiError("length_required", "Content-Length required")
        length = int(raw)
        if length > MAX_BODY_BYTES:
            raise ApiError("payload_too_large", "Request body too large")
        body = self.rfile.read(length) if length else b""
        self._body_read = True
        if len(body) != length:
            self.close_connection = True
            raise ApiError("invalid_json", "Incomplete request body")
        try:
            return json.loads(body.decode("utf-8"), parse_constant=_reject_constant)
        except (ValueError, RecursionError):
            raise ApiError("invalid_json", "Request body is not valid JSON") from None


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):  # no tracebacks to stderr
        pass


def create_server(data_dir: str, port: int = 0) -> ThreadingHTTPServer:
    """Create (but do not start) a server bound to 127.0.0.1 only."""
    path = Path(data_dir)
    path.mkdir(parents=True, exist_ok=True)
    storage = Storage(path / "case_studies.sqlite3")  # may raise SchemaTooNew
    server = _Server(("127.0.0.1", port), Handler)
    server.storage = storage
    return server
