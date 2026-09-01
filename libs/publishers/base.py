"""The contract every platform implements.

Adding a platform means adding one module here and listing it in
`libs/publishers/__init__.py` -- nothing else in the project changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from libs.config import MissingCredentials


@dataclass
class Prepared:
    """Exactly what will be sent, so --dry-run can show it without posting."""

    image: Path
    text: str


@dataclass
class Result:
    platform: str
    ok: bool
    detail: str


class Publisher(ABC):
    name = ""

    @abstractmethod
    def credentials(self):
        """Load this platform's credentials, raising MissingCredentials."""

    def is_configured(self):
        try:
            self.credentials()
        except MissingCredentials:
            return False
        return True

    @abstractmethod
    def prepare(self, post):
        """Resize the picture and render the text, without touching the network."""

    @abstractmethod
    def publish(self, post, prepared):
        """Actually post, and return a one-line detail for the summary."""
