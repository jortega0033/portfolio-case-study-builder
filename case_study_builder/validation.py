"""Request payload validation. Pure functions, no I/O."""

from __future__ import annotations

import re
import secrets

MAX_TITLE = 120
MAX_HEADING = 160
MAX_BODY = 20000
MAX_SECTIONS = 50
DEFAULT_TITLE = "Untitled case study"

_SECTION_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,40}\Z")
# Control characters except \n and \t (\r is normalised before checking).
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


class ValidationError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def _bad(field: str, message: str) -> ValidationError:
    return ValidationError("invalid_field", message, {"field": field})


def _text(value, field: str, max_len: int, min_len: int, strip: bool) -> str:
    if not isinstance(value, str):
        raise _bad(field, f"{field} must be a string")
    value = value.replace("\r\n", "\n")
    if strip:
        value = value.strip()
    if _CONTROL_RE.search(value):
        raise _bad(field, f"{field} contains control characters")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise _bad(field, f"{field} contains invalid unicode") from None
    if len(value) < min_len:
        raise _bad(field, f"{field} must be at least {min_len} character(s)")
    if len(value) > max_len:
        raise _bad(field, f"{field} must be at most {max_len} characters")
    return value


def _sections(value) -> list[dict]:
    if not isinstance(value, list):
        raise _bad("sections", "sections must be an array")
    if len(value) > MAX_SECTIONS:
        raise _bad("sections", f"at most {MAX_SECTIONS} sections allowed")
    out: list[dict] = []
    seen: set[str] = set()
    for i, item in enumerate(value):
        prefix = f"sections[{i}]"
        if not isinstance(item, dict):
            raise _bad(prefix, f"{prefix} must be an object")
        for key in item:
            if key not in ("id", "heading", "body"):
                raise _bad(f"{prefix}.{key}", f"unknown field {key!r}")
        for key in ("heading", "body"):
            if key not in item:
                raise _bad(f"{prefix}.{key}", f"{prefix}.{key} is required")
        sid = item.get("id")
        if sid is not None:
            if not isinstance(sid, str) or not _SECTION_ID_RE.match(sid):
                raise _bad(f"{prefix}.id", "section id must match [A-Za-z0-9_-]{1,40}")
            if sid in seen:
                raise _bad(f"{prefix}.id", "duplicate section id")
            seen.add(sid)
        out.append({
            "id": sid,
            "heading": _text(item["heading"], f"{prefix}.heading", MAX_HEADING, 0, True),
            "body": _text(item["body"], f"{prefix}.body", MAX_BODY, 0, False),
        })
    for s in out:
        if s["id"] is None:
            while True:
                sid = "s" + secrets.token_hex(4)
                if sid not in seen:
                    break
            seen.add(sid)
            s["id"] = sid
    return out


def validate_project_payload(obj, require_revision: bool) -> dict:
    """Validate a create (require_revision=False) or update (True) body.

    Returns {"title", "sections"} plus "base_revision" when required.
    Create applies defaults for missing title/sections; update requires all.
    """
    if not isinstance(obj, dict):
        raise ValidationError("invalid_json", "request body must be a JSON object")
    allowed = {"title", "sections"} | ({"base_revision"} if require_revision else set())
    for key in obj:
        if key not in allowed:
            raise _bad(str(key), f"unknown field {key!r}")
    required = allowed if require_revision else set()
    for key in required:
        if key not in obj:
            raise _bad(key, f"{key} is required")

    result: dict = {}
    if require_revision:
        rev = obj["base_revision"]
        if isinstance(rev, bool) or not isinstance(rev, int) or rev < 1:
            raise _bad("base_revision", "base_revision must be an integer >= 1")
        result["base_revision"] = rev

    if "title" in obj:
        result["title"] = _text(obj["title"], "title", MAX_TITLE, 1, True)
    else:
        result["title"] = DEFAULT_TITLE

    if "sections" in obj:
        result["sections"] = _sections(obj["sections"])
    else:
        result["sections"] = _sections([{"heading": "", "body": ""}])
    return result
