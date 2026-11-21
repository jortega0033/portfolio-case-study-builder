"""API checks CS-B01..CS-B10, CS-B13, CS-B16 against a real loopback server."""

import unittest

try:
    from helpers import LANTERN, ServerCase  # unittest discover -s tests
except ImportError:  # python -m unittest tests.test_api
    from tests.helpers import LANTERN, ServerCase


class HealthAndCreate(ServerCase):
    def test_b01_health(self):
        status, _, body = self.request("GET", "/api/v1/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok", "schema_version": 1})

    def test_b02_create_default(self):
        proj = self.create()
        self.assertEqual(proj["revision"], 1)
        self.assertEqual(proj["title"], "Untitled case study")
        self.assertEqual(len(proj["sections"]), 1)
        self.assertRegex(proj["id"], r"^[0-9a-f]{32}$")

    def test_server_binds_loopback_only(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_list_ordering_and_counts(self):
        a = self.create({"title": "Alpha", "sections": []})
        b = self.create(LANTERN)
        status, _, body = self.request("GET", "/api/v1/projects")
        self.assertEqual(status, 200)
        by_id = {p["id"]: p for p in body["projects"]}
        self.assertEqual(by_id[a["id"]]["section_count"], 0)
        self.assertEqual(by_id[b["id"]]["section_count"], 3)
        self.assertEqual(set(by_id), {a["id"], b["id"]})
        for p in body["projects"]:
            self.assertEqual(set(p), {"id", "title", "revision", "updated_at", "section_count"})


class SaveAndReload(ServerCase):
    def test_b03_save_and_reload_preserves_order(self):
        proj = self.create()
        status, _, saved = self.save(proj, LANTERN["title"], LANTERN["sections"])
        self.assertEqual(status, 200)
        self.assertEqual(saved["revision"], 2)
        status, _, got = self.request("GET", f"/api/v1/projects/{proj['id']}")
        self.assertEqual(got["title"], LANTERN["title"])
        self.assertEqual([s["heading"] for s in got["sections"]], ["Overview", "Constraints", "Outcome"])
        self.assertEqual([s["body"] for s in got["sections"]], [s["body"] for s in LANTERN["sections"]])
        self.assertEqual(len({s["id"] for s in got["sections"]}), 3)

    def test_reorder_preserves_ids(self):
        proj = self.create(LANTERN)
        a, b, c = proj["sections"]
        status, _, saved = self.save(proj, sections=[c, a, b])
        self.assertEqual(status, 200)
        self.assertEqual([s["id"] for s in saved["sections"]], [c["id"], a["id"], b["id"]])
        self.assertEqual([s["heading"] for s in saved["sections"]], ["Outcome", "Overview", "Constraints"])

    def test_identical_save_still_bumps_revision(self):
        proj = self.create(LANTERN)
        _, _, s1 = self.save(proj)
        _, _, s2 = self.save(s1)
        self.assertEqual((s1["revision"], s2["revision"]), (2, 3))

    def test_delete_all_sections_allowed(self):
        proj = self.create(LANTERN)
        status, _, saved = self.save(proj, sections=[])
        self.assertEqual(status, 200)
        self.assertEqual(saved["sections"], [])

    def test_crlf_normalised_and_title_trimmed(self):
        proj = self.create()
        _, _, saved = self.save(proj, title="  Padded  ", sections=[{"heading": " H ", "body": "a\r\nb"}])
        self.assertEqual(saved["title"], "Padded")
        self.assertEqual(saved["sections"][0]["heading"], "H")
        self.assertEqual(saved["sections"][0]["body"], "a\nb")

    def test_b05_revision_conflict(self):
        proj = self.create(LANTERN)
        first = [dict(s) for s in proj["sections"]]
        first[0]["heading"] = "First writer"
        second = [dict(s) for s in proj["sections"]]
        second[0]["heading"] = "Second writer"
        status, _, _ = self.save(proj, sections=first)
        self.assertEqual(status, 200)
        status, _, err = self.save(proj, sections=second)
        self.assertEqual(status, 409)
        self.assertEqual(err["error"]["code"], "revision_conflict")
        self.assertEqual(err["error"]["details"]["current_revision"], 2)
        _, _, got = self.request("GET", f"/api/v1/projects/{proj['id']}")
        self.assertEqual(got["sections"][0]["heading"], "First writer")
        self.assertEqual(got["revision"], 2)


class Validation(ServerCase):
    def setUp(self):
        super().setUp()
        self.proj = self.create(LANTERN)

    def assert_rejected(self, body_changes, code="invalid_field", status_expected=400):
        body = {"title": "T", "base_revision": 1, "sections": [{"heading": "h", "body": "b"}]}
        body.update(body_changes)
        status, _, err = self.request("PUT", f"/api/v1/projects/{self.proj['id']}", body)
        self.assertEqual(status, status_expected, err)
        self.assertEqual(err["error"]["code"], code)
        # I3: stored data unchanged
        _, _, got = self.request("GET", f"/api/v1/projects/{self.proj['id']}")
        self.assertEqual(got, self.proj)
        return err

    def test_b06_invalid_fields(self):
        self.assert_rejected({"title": ""})
        self.assert_rejected({"title": "   "})
        self.assert_rejected({"title": "x" * 121})
        self.assert_rejected({"title": 5})
        self.assert_rejected({"sections": [{"heading": "x" * 161, "body": ""}]})
        self.assert_rejected({"sections": [{"heading": "h", "body": "x" * 20001}]})
        self.assert_rejected({"sections": [{"heading": "h", "body": ""}] * 51})
        self.assert_rejected({"sections": "nope"})
        self.assert_rejected({"sections": [{"heading": 1, "body": ""}]})
        self.assert_rejected({"sections": [{"heading": "h", "body": "bad\x07char"}]})
        self.assert_rejected({"sections": [{"heading": "h", "body": "", "extra": 1}]})
        self.assert_rejected({"sections": [{"id": "dup", "heading": "a", "body": ""},
                                           {"id": "dup", "heading": "b", "body": ""}]})
        self.assert_rejected({"sections": [{"id": "bad id!", "heading": "a", "body": ""}]})
        self.assert_rejected({"base_revision": 0})
        self.assert_rejected({"base_revision": True})
        self.assert_rejected({"base_revision": "1"})
        self.assert_rejected({"surprise": 1})

    def test_limits_accepted_at_boundary(self):
        body = {"title": "x" * 120, "base_revision": 1,
                "sections": [{"heading": "h" * 160, "body": "b" * 20000}] + [{"heading": "", "body": ""}] * 49}
        status, _, saved = self.request("PUT", f"/api/v1/projects/{self.proj['id']}", body)
        self.assertEqual(status, 200)
        self.assertEqual(len(saved["sections"]), 50)

    def test_field_detail_names_path(self):
        err = self.assert_rejected({"sections": [{"heading": "ok", "body": ""}, {"heading": 3, "body": ""}]})
        self.assertEqual(err["error"]["details"]["field"], "sections[1].heading")

    def test_invalid_json_and_non_object(self):
        for raw in (b"{not json", b"[1,2]", b"\xff\xfe"):
            status, _, err = self.request("PUT", f"/api/v1/projects/{self.proj['id']}", raw=raw,
                                          headers={"Content-Type": "application/json"})
            self.assertEqual(status, 400)
            self.assertEqual(err["error"]["code"], "invalid_json")

    def test_b13_rejected_save_after_good_save_leaves_state(self):
        _, _, good = self.save(self.proj, title="Good")
        status, _, _ = self.request("PUT", f"/api/v1/projects/{self.proj['id']}",
                                    {"title": "", "base_revision": good["revision"], "sections": []})
        self.assertEqual(status, 400)
        _, _, got = self.request("GET", f"/api/v1/projects/{self.proj['id']}")
        self.assertEqual(got, good)

    def test_put_unknown_project_is_404(self):
        status, _, err = self.request("PUT", "/api/v1/projects/" + "0" * 32,
                                      {"title": "T", "base_revision": 1, "sections": []})
        self.assertEqual(status, 404)
        self.assertEqual(err["error"]["code"], "not_found")


class Limits(ServerCase):
    def test_b07_payload_too_large(self):
        proj = self.create()
        # Declare an oversized body without sending it: the server must reject on the header alone.
        status, _, err = self.request("PUT", f"/api/v1/projects/{proj['id']}", raw=b"{}",
                                      headers={"Content-Type": "application/json",
                                               "Content-Length": "262145"})
        self.assertEqual(status, 413)
        self.assertEqual(err["error"]["code"], "payload_too_large")

    def test_b07_content_type_and_length(self):
        status, _, err = self.request("POST", "/api/v1/projects", raw=b"{}",
                                      headers={"Content-Type": "text/plain"})
        self.assertEqual((status, err["error"]["code"]), (415, "unsupported_media_type"))
        status, _, err = self.request("POST", "/api/v1/projects", raw=b"{}",
                                      headers={"Content-Type": "application/json",
                                               "Transfer-Encoding": "chunked", "Content-Length": "2"})
        self.assertEqual((status, err["error"]["code"]), (411, "length_required"))

    def test_content_type_with_charset_ok(self):
        status, _, _ = self.request("POST", "/api/v1/projects", raw=b"{}",
                                    headers={"Content-Type": "application/json; charset=utf-8"})
        self.assertEqual(status, 201)


class HostAndOrigin(ServerCase):
    def test_b08_foreign_host_rejected(self):
        for path in ("/api/v1/health", "/"):
            status, _, err = self.request("GET", path, host="evil.example:80")
            self.assertEqual(status, 403)
            self.assertEqual(err["error"]["code"], "forbidden_host")
        status, _, err = self.request("GET", "/api/v1/health", host="127.0.0.1:1")
        self.assertEqual(status, 403)

    def test_localhost_host_allowed(self):
        status, _, _ = self.request("GET", "/api/v1/health", host=f"localhost:{self.port}")
        self.assertEqual(status, 200)

    def test_b09_origin_required_for_writes(self):
        for origin in (False, "http://evil.example", "null", f"https://127.0.0.1:{self.port}"):
            status, _, err = self.request("POST", "/api/v1/projects", {}, origin=origin)
            self.assertEqual(status, 403, origin)
            self.assertEqual(err["error"]["code"], "forbidden_origin")
        proj = self.create()
        status, _, err = self.request("PUT", f"/api/v1/projects/{proj['id']}",
                                      {"title": "T", "base_revision": 1, "sections": []},
                                      origin="http://evil.example")
        self.assertEqual(status, 403)
        _, _, got = self.request("GET", f"/api/v1/projects/{proj['id']}")
        self.assertEqual(got["revision"], 1)

    def test_origin_not_required_for_get(self):
        status, _, _ = self.request("GET", "/api/v1/health", origin=False)
        self.assertEqual(status, 200)

    def test_localhost_origin_matches_localhost_host(self):
        h = f"localhost:{self.port}"
        status, _, _ = self.request("POST", "/api/v1/projects", {}, host=h, origin=f"http://{h}")
        self.assertEqual(status, 201)

    def test_no_cors_headers_and_security_headers(self):
        _, resp, _ = self.request("GET", "/api/v1/health")
        self.assertIsNone(resp.getheader("Access-Control-Allow-Origin"))
        self.assertIn("default-src 'none'", resp.getheader("Content-Security-Policy"))
        self.assertEqual(resp.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.getheader("Cache-Control"), "no-store")


class Routing(ServerCase):
    def test_b16_unknown_and_wrong_method(self):
        status, _, err = self.request("GET", "/nope")
        self.assertEqual((status, err["error"]["code"]), (404, "not_found"))
        status, _, _ = self.request("GET", "/api/v1/projects/xyz")
        self.assertEqual(status, 404)
        status, _, _ = self.request("GET", "/api/v1/projects/" + "a" * 32)
        self.assertEqual(status, 404)
        status, _, _ = self.request("GET", "/static/other.js")
        self.assertEqual(status, 404)
        status, _, _ = self.request("GET", "/static/../server.py")
        self.assertEqual(status, 404)
        status, resp, err = self.request("DELETE", "/api/v1/projects/" + "a" * 32)
        self.assertEqual((status, err["error"]["code"]), (405, "method_not_allowed"))
        self.assertIn("GET", resp.getheader("Allow"))
        status, resp, _ = self.request("POST", "/api/v1/health", {})
        self.assertEqual(status, 405)
        self.assertEqual(resp.getheader("Allow"), "GET")


class VerbatimText(ServerCase):
    def test_b10_markup_like_text_round_trips_verbatim(self):
        heading = "<script>alert(1)</script>"
        body = '<img src=x onerror=alert(1)> & "quotes"'
        proj = self.create()
        _, _, saved = self.save(proj, title="<b>t</b>", sections=[{"heading": heading, "body": body}])
        _, resp, got = self.request("GET", f"/api/v1/projects/{proj['id']}")
        self.assertEqual(got["sections"][0]["heading"], heading)
        self.assertEqual(got["sections"][0]["body"], body)
        self.assertEqual(got["title"], "<b>t</b>")
        self.assertTrue(resp.getheader("Content-Type").startswith("application/json"))


if __name__ == "__main__":
    unittest.main()
