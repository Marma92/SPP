"""The contract every platform implements.

Text rendering and image preparation are deliberately separate: rendering a
caption is instantaneous and happens on every keystroke in the GUI, while
resizing a picture is expensive and only needs doing once per photo.

Adding a platform means adding one module here and listing it in
`libs/publishers/__init__.py` -- nothing else in the project changes.
"""

import importlib.util
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from libs.config import MissingCredentials

ELLIPSIS = "…"


@dataclass
class Prepared:
    """Exactly what will be sent, so a preview can show it without posting."""

    image: Path
    text: str


class Publisher(ABC):
    name = ""
    # Short description of what this platform receives, for a preview tab.
    image_label = ""
    # Caption limit in the platform's own counting unit; None if there is none.
    limit = None
    # Client libraries that publish() imports lazily. Naming them here is what
    # lets a missing one surface before a post is composed, instead of at the
    # moment of upload, with everything already typed in.
    requires = ()

    def missing_requirement(self):
        """The first client library this platform needs and cannot find."""
        for module in self.requires:
            try:
                found = importlib.util.find_spec(module) is not None
            except (ImportError, ValueError):
                found = False
            if not found:
                return module
        return None

    def unavailable(self):
        """One line saying why this platform cannot be used, or None if it can."""
        missing = self.missing_requirement()
        if missing:
            return "%s is not installed -- run pip install -r requirements.txt" % missing
        try:
            self.credentials()
        except MissingCredentials as error:
            return str(error)
        return None

    @abstractmethod
    def credentials(self):
        """Load this platform's credentials, raising MissingCredentials."""

    def is_configured(self):
        try:
            self.credentials()
        except MissingCredentials:
            return False
        return True

    def measure(self, text):
        """Length of `text` the way this platform counts it."""
        return len(text)

    def normalise(self, text):
        """The form this platform will see, before anything is counted."""
        return text

    def split_text(self, post):
        """(kept, dropped): what the platform will publish, and what it cuts.

        One algorithm for every platform; each supplies its own ruler through
        `measure`, so a grapheme counter and a character counter cut in the
        same place for the same reason.
        """
        text = self.normalise(post.caption)
        if self.limit is None or self.measure(text) <= self.limit:
            return text, ""

        budget = self.limit - self.measure(ELLIPSIS)
        cut = 0
        used = 0
        for index, char in enumerate(text):
            used += self.measure(char)
            if used > budget:
                break
            cut = index + 1
        return text[:cut].rstrip() + ELLIPSIS, text[cut:]

    def render_text(self, post):
        return self.split_text(post)[0]

    @abstractmethod
    def prepare_image(self, post):
        """Resize the picture for this platform and return the file written."""

    def prepare(self, post):
        return Prepared(image=self.prepare_image(post), text=self.render_text(post))

    @abstractmethod
    def publish(self, post, prepared):
        """Actually post, and return a one-line detail for the summary."""
