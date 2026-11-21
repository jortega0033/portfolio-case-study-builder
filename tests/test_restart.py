"""CS-B04 persistence across restart, in-process and through the real CLI entry point."""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

try:
    from helpers import LANTERN, ServerCase
except ImportError:
    from tests.helpers import LANTERN, ServerCase

ROOT = Path(__file__).resolve().parent.parent


class InProcessRestart(ServerCase):
    def test_b04_data_survives_server_restart(self):
        proj = self.create(LANTERN)
        _, _, saved = self.save(proj, sections=list(reversed(proj["sections"])))
        self.stop_server()
        self.start_server()
        status, _, got = self.request("GET", f"/api/v1/projects/{proj['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(got, saved)
        self.assertEqual(got["revision"], 2)
        self.assertEqual([s["heading"] for s in got["sections"]], ["Outcome", "Constraints", "Overview"])
        # revision checks keep working after restart
        status, _, _ = self.save(proj)  # stale base_revision 1
        self.assertEqual(status, 409)

    def test_schema_metadata(self):
        self.create()
        con = sqlite3.connect(Path(self.data_dir) / "case_studies.sqlite3")
        try:
            self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 1)
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"projects", "sections"} <= tables)
        finally:
            con.close()


class CliProcess(unittest.TestCase):
    def launch(self, data_dir):
        proc = subprocess.Popen(
            [sys.executable, "-m", "case_study_builder", "--data-dir", data_dir, "--port", "0"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(self.stop, proc)
        line = {}
        t = threading.Thread(target=lambda: line.setdefault("v", proc.stdout.readline()), daemon=True)
        t.start()
        t.join(15)
        self.assertIn("v", line, "server did not print its address in time")
        self.assertRegex(line["v"], r"^Serving on http://127\.0\.0\.1:\d+/")
        return proc, int(line["v"].strip().rsplit(":", 1)[1].rstrip("/"))

    @staticmethod
    def stop(proc):
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        for pipe in (proc.stdout, proc.stderr):
            if pipe:
                pipe.close()

    @staticmethod
    def call(port, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method)
        req.add_header("Origin", f"http://127.0.0.1:{port}")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())

    def test_b04_cli_restart_reopens_saved_project(self):
        with tempfile.TemporaryDirectory() as d:
            data_dir = os.path.join(d, "nested", "data")  # created on demand
            proc, port = self.launch(data_dir)
            _, proj = self.call(port, "POST", "/api/v1/projects", LANTERN)
            _, saved = self.call(port, "PUT", f"/api/v1/projects/{proj['id']}",
                                 {"title": "Renamed", "base_revision": 1, "sections": proj["sections"]})
            self.stop(proc)
            proc2, port2 = self.launch(data_dir)
            status, got = self.call(port2, "GET", f"/api/v1/projects/{proj['id']}")
            self.assertEqual(status, 200)
            self.assertEqual(got, saved)
            self.assertEqual(got["title"], "Renamed")

    def test_newer_schema_is_refused_with_exit_code_2(self):
        with tempfile.TemporaryDirectory() as d:
            con = sqlite3.connect(os.path.join(d, "case_studies.sqlite3"))
            con.execute("PRAGMA user_version = 2")
            con.execute("CREATE TABLE t(x)")
            con.commit()
            con.close()
            r = subprocess.run([sys.executable, "-m", "case_study_builder", "--data-dir", d, "--port", "0"],
                               cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertNotIn("Traceback", r.stderr)

    def test_missing_arguments_fail(self):
        r = subprocess.run([sys.executable, "-m", "case_study_builder"], cwd=ROOT,
                           capture_output=True, text=True, timeout=30)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
