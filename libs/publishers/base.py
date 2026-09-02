"""The contract every platform implements.

Text rendering and image preparation are deliberately separate: rendering a
caption is instantaneous and happens on every keystroke in the GUI, while
resizing a picture is expensive and only needs doing once per photo.

Adding a platform means adding one module here and listing it in
`libs/publishers/__init__.py` -- nothing else in the project changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from libs.config import MissingCredentials


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

    def split_text(self, post):
        """(kept, dropped): what the platform will publish, and what it cuts."""
        return post.caption, ""

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
