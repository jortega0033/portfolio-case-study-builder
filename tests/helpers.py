"""Shared helpers: a real loopback server on an ephemeral port with a disposable database."""

import http.client
import json
import tempfile
import threading
import unittest

from case_study_builder.server import create_server

LANTERN = {
    "title": "Lantern Library: A Reading Lamp Redesign",
    "sections": [
        {"heading": "Overview", "body": "A small team reworked a fictional desk lamp for night reading."},
        {"heading": "Constraints", "body": "Budget, materials, and a two-week schedule."},
        {"heading": "Outcome", "body": "Prototype tested with ten invented readers."},
    ],
}


class ServerCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.data_dir = self._tmp.name
        self.start_server()

    def start_server(self):
        self.server = create_server(self.data_dir, 0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)

    def tearDown(self):
        self.stop_server()

    def request(self, method, path, body=None, headers=None, raw=None, origin=True, host=None):
        """Return (status, headers, parsed_json_or_bytes). Same-origin Origin is sent by default."""
        h = {}
        hostval = host or f"127.0.0.1:{self.port}"
        if origin is True:
            h["Origin"] = f"http://{hostval}"
        elif origin:
            h["Origin"] = origin
        data = raw
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            h["Content-Type"] = "application/json"
        h.update(headers or {})
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
            conn.putheader("Host", hostval)
            for k, v in h.items():
                conn.putheader(k, v)
            if data is not None and "Content-Length" not in h:
                conn.putheader("Content-Length", str(len(data)))
            conn.endheaders(data if data is not None else None)
            resp = conn.getresponse()
            payload = resp.read()
            ctype = resp.getheader("Content-Type", "")
            parsed = json.loads(payload) if ctype.startswith("application/json") else payload
            return resp.status, resp, parsed
        finally:
            conn.close()

    def create(self, payload=None):
        status, _, proj = self.request("POST", "/api/v1/projects", payload if payload is not None else {})
        self.assertEqual(status, 201, proj)
        return proj

    def save(self, proj, title=None, sections=None, base_revision=None):
        body = {
            "title": title if title is not None else proj["title"],
            "base_revision": base_revision if base_revision is not None else proj["revision"],
            "sections": sections if sections is not None else proj["sections"],
        }
        return self.request("PUT", f"/api/v1/projects/{proj['id']}", body)
