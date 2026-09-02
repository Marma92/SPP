"""The credentials the settings screen reads and writes.

They land in the data directory's `.env`, which `config` already prefers over a
clone's — so a repository checkout keeps working until the screen is used, and
is quietly superseded once it is.
"""

import os

from libs import config

SECRET = True

# (heading, [(variable, label, secret)]) — the whole shape of the screen.
GROUPS = (
    (
        "Flickr",
        (
            ("FLICKR_API_KEY", "API key", not SECRET),
            ("FLICKR_API_SECRET", "API secret", SECRET),
        ),
    ),
    (
        "Instagram",
        (
            ("INSTAGRAM_USERNAME", "Username", not SECRET),
            ("INSTAGRAM_PASSWORD", "Password", SECRET),
            ("INSTAGRAM_SESSIONID", "Session id (used instead of the password)", SECRET),
        ),
    ),
    (
        "Bluesky",
        (
            ("BLUESKY_HANDLE", "Handle", not SECRET),
            ("BLUESKY_APP_PASSWORD", "App password", SECRET),
        ),
    ),
    (
        "Mastodon",
        (
            ("MASTODON_INSTANCE", "Instance (e.g. mastodon.social)", not SECRET),
            ("MASTODON_TOKEN", "Access token", SECRET),
            ("MASTODON_MAX_CHARS", "Caption limit of that instance (blank = 500)", not SECRET),
        ),
    ),
    (
        "Pixelfed",
        (
            ("PIXELFED_INSTANCE", "Instance (e.g. pixelfed.social)", not SECRET),
            ("PIXELFED_TOKEN", "Access token", SECRET),
            ("PIXELFED_MAX_CHARS", "Caption limit of that instance (blank = 500)", not SECRET),
        ),
    ),
    (
        "General",
        (
            ("SPP_PLATFORMS", "Platforms posted to by default (blank = all)", not SECRET),
            ("SPP_LANGS", "Language of your captions", not SECRET),
        ),
    ),
)

VARIABLES = tuple(name for _heading, fields in GROUPS for name, _label, _secret in fields)

HEADER = (
    "# Written by SPP. Editing it by hand is fine; the settings screen will\n"
    "# rewrite the whole file the next time it saves.\n"
)


def current():
    """What each variable is set to right now, from wherever it came."""
    return {name: os.getenv(name, "") for name in VARIABLES}


def _quote(value):
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return '"%s"' % escaped


def write(values):
    """Replace the data directory's .env, then make the change take effect."""
    lines = [HEADER]
    for heading, fields in GROUPS:
        lines.append("# --- %s" % heading)
        for name, _label, _secret in fields:
            lines.append("%s=%s" % (name, _quote(values.get(name, "").strip())))
        lines.append("")

    config.ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.ENV_FILE.write_text("\n".join(lines), encoding="utf-8")
    try:
        # Readable by its owner only, where the platform has a say in it.
        config.ENV_FILE.chmod(0o600)
    except OSError:
        pass

    config.reload()
    return config.ENV_FILE
