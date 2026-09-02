"""Credentials and paths, read from the environment.

Everything used to live in `auth/*.py` modules that were imported at the top of
`spplib`, which meant the library could not even be imported -- let alone
tested -- without all three files present. Credentials now come from a
git-ignored `.env` file and are only read when a platform is actually used.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# All working folders hang off the project root, not off the current working
# directory: running `python photopost.py` from anywhere used to scatter files
# around (the session file was even written to `../sessions/`).
RESIZE_DIR = PROJECT_ROOT / "resizes"
INSTAGRAM_DIR = PROJECT_ROOT / "instagram"
BLUESKY_DIR = PROJECT_ROOT / "bluesky"
SESSION_DIR = PROJECT_ROOT / "sessions"
STATE_DIR = PROJECT_ROOT / "state"
INSTAGRAM_SESSION_FILE = SESSION_DIR / "instagram_session.json"
BLUESKY_SESSION_FILE = SESSION_DIR / "bluesky_session.txt"
LAST_POST_FILE = STATE_DIR / "last_post.json"

load_dotenv(PROJECT_ROOT / ".env")

# Optional default platform selection, e.g. SPP_PLATFORMS=flickr,instagram
DEFAULT_PLATFORMS = os.getenv("SPP_PLATFORMS", "")

# Language the captions are written in, declared to the platforms that ask
# for it. Bluesky filters and offers translation on this.
POST_LANGS = [code.strip() for code in os.getenv("SPP_LANGS", "fr").split(",") if code.strip()]


class MissingCredentials(RuntimeError):
    """Raised when a platform is asked to post without being configured."""


def _require(platform, *names):
    values = [os.getenv(name, "").strip() for name in names]
    missing = [name for name, value in zip(names, values) if not value]
    if missing:
        raise MissingCredentials(
            "%s is not configured: %s missing from .env "
            "(copy .env.example and fill it in)" % (platform, ", ".join(missing))
        )
    return values


@dataclass(frozen=True)
class FlickrAuth:
    api_key: str
    api_secret: str

    @classmethod
    def load(cls):
        return cls(*_require("Flickr", "FLICKR_API_KEY", "FLICKR_API_SECRET"))


@dataclass(frozen=True)
class InstagramAuth:
    username: str
    password: str
    sessionid: str

    @classmethod
    def load(cls):
        # A sessionid lifted from a browser that has already cleared Instagram's
        # verification is the way past a native challenge: the checkpoint is
        # tied to the device that triggered it, and resolving it in a browser
        # never clears it for the library's own device.
        sessionid = os.getenv("INSTAGRAM_SESSIONID", "").strip()
        if sessionid:
            return cls(os.getenv("INSTAGRAM_USERNAME", "").strip(), "", sessionid)
        return cls(
            *_require("Instagram", "INSTAGRAM_USERNAME", "INSTAGRAM_PASSWORD"), ""
        )


@dataclass(frozen=True)
class BlueskyAuth:
    handle: str
    app_password: str

    @classmethod
    def load(cls):
        return cls(*_require("Bluesky", "BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD"))
