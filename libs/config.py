"""Credentials and paths, read from the environment.

Everything used to live in `auth/*.py` modules that were imported at the top of
`spplib`, which meant the library could not even be imported -- let alone
tested -- without all three files present. Credentials now come from a
git-ignored `.env` file and are only read when a platform is actually used.
"""

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _data_dir():
    """Where the app may write, whoever installed it and wherever from.

    An app installed under Program Files may not write beside its own
    executable, so nothing hangs off the project root any more. SPP_DATA_DIR
    overrides it, which is what tests and a portable install use.
    """
    override = os.getenv("SPP_DATA_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = os.getenv("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "SPP"


DATA_DIR = _data_dir()
RESIZE_DIR = DATA_DIR / "resizes"
INSTAGRAM_DIR = DATA_DIR / "instagram"
BLUESKY_DIR = DATA_DIR / "bluesky"
SESSION_DIR = DATA_DIR / "sessions"
STATE_DIR = DATA_DIR / "state"
INSTAGRAM_SESSION_FILE = SESSION_DIR / "instagram_session.json"
BLUESKY_SESSION_FILE = SESSION_DIR / "bluesky_session.txt"
LAST_POST_FILE = STATE_DIR / "last_post.json"


def _adopt_clone_data():
    """Carry an existing clone's sessions and remembered fields over, once.

    Throwing away sessions/ would mean facing Instagram's verification
    challenge again, so this copies rather than moves, and never overwrites
    anything already in the data directory. The resized pictures are
    disposable and are left behind.
    """
    for name in ("sessions", "state"):
        source = PROJECT_ROOT / name
        target = DATA_DIR / name
        if source.is_dir() and not target.exists():
            shutil.copytree(source, target)


_adopt_clone_data()

# A clone keeps its .env where it has always been; an installed copy finds one
# beside its data. The first file found wins, since load_dotenv leaves
# variables already set alone.
for _candidate in (DATA_DIR / ".env", PROJECT_ROOT / ".env"):
    load_dotenv(_candidate)

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
