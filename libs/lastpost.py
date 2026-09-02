"""Remembering the fields the EXIF can never know.

Film, lab and scanner are the same for a whole roll, sometimes for months, and
no camera writes them. They are carried over from the previous post.
"""

import json

from libs.config import LAST_POST_FILE

REMEMBERED = ("film", "lab", "scan")


def load():
    """The remembered fields, or empty strings when there is nothing yet."""
    try:
        stored = json.loads(LAST_POST_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {field: "" for field in REMEMBERED}
    return {field: str(stored.get(field, "")) for field in REMEMBERED}


def save(post):
    LAST_POST_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_POST_FILE.write_text(
        json.dumps({field: getattr(post, field) for field in REMEMBERED}, indent=2),
        encoding="utf-8",
    )
