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
SESSION_DIR = PROJECT_ROOT / "sessions"
INSTAGRAM_SESSION_FILE = SESSION_DIR / "instagram_session.json"

load_dotenv(PROJECT_ROOT / ".env")


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
class TwitterAuth:
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_token_secret: str

    @classmethod
    def load(cls):
        return cls(*_require(
            "Twitter",
            "TWITTER_CONSUMER_KEY",
            "TWITTER_CONSUMER_SECRET",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET",
        ))


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

    @classmethod
    def load(cls):
        return cls(*_require("Instagram", "INSTAGRAM_USERNAME", "INSTAGRAM_PASSWORD"))
