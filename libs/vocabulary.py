"""Everything the photographer has ever typed, kept to be offered back.

`lastpost` remembers one value per field, the most recent, and pre-fills with
it. This is the wider net: every distinct camera, lens, film, lab, scanner and
place, so typing three letters is enough to find one again months later.
"""

import json

from libs.config import VOCABULARY_FILE

# The fields worth completing: those whose values come back, spelled the same
# way, post after post. Titles and legends never repeat, and are left out.
FIELDS = ("camera", "lens", "film", "lab", "scan", "location")

# Per field. Long enough for years of posting, short enough to stay readable.
LIMIT = 60


def load():
    """Known values per field, most recently used first."""
    try:
        stored = json.loads(VOCABULARY_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {field: [] for field in FIELDS}

    known = {}
    for field in FIELDS:
        values = stored.get(field)
        known[field] = [
            str(value) for value in values if str(value).strip()
        ] if isinstance(values, list) else []
    return known


def remember(post):
    """Fold one post's values in, newest first, without duplicating them."""
    known = load()
    for field in FIELDS:
        value = getattr(post, field, "").strip()
        if not value:
            continue
        # Case-insensitive: "Portra 400" and "portra 400" are the same film,
        # and the spelling that survives is the one just used.
        rest = [
            other for other in known[field] if other.casefold() != value.casefold()
        ]
        known[field] = [value] + rest[: LIMIT - 1]

    VOCABULARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    VOCABULARY_FILE.write_text(
        json.dumps(known, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return known
