"""Named sets of values worth coming back to.

`lastpost` proposes whatever you did last, which is right most of the time and
wrong the moment you alternate between two cameras. A preset is the deliberate
version: a body, a film and a lab you name once and pick again.
"""

import json

from libs.config import PRESETS_FILE

# What a preset may carry. Anything specific to one frame -- title, legend,
# alt text, coordinates -- has no business being reused.
FIELDS = ("camera", "lens", "film", "lab", "scan", "tags", "location")


def load():
    """{name: {field: value}}, in name order, ignoring anything malformed."""
    try:
        stored = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(stored, dict):
        return {}

    presets = {}
    for name in sorted(stored, key=str.casefold):
        values = stored[name]
        if not isinstance(values, dict):
            continue
        kept = {
            field: str(values[field]).strip()
            for field in FIELDS
            if isinstance(values.get(field), str) and values[field].strip()
        }
        if kept:
            presets[str(name)] = kept
    return presets


def save(name, values):
    """Store one preset under `name`, replacing any preset of that name."""
    name = name.strip()
    if not name:
        raise ValueError("a preset needs a name")

    kept = {
        field: value.strip()
        for field, value in values.items()
        if field in FIELDS and value.strip()
    }
    if not kept:
        raise ValueError("a preset needs at least one value")

    presets = load()
    presets[name] = kept
    _write(presets)
    return presets


def delete(name):
    presets = load()
    presets.pop(name, None)
    _write(presets)
    return presets


def _write(presets):
    PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PRESETS_FILE.write_text(
        json.dumps(presets, indent=2, ensure_ascii=False), encoding="utf-8"
    )
