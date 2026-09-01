"""What is being posted, and how it reads.

A single `Post` carries the picture and everything the prompts collected, so
publishers take one argument instead of nine positional strings.
"""

import re
from dataclasses import dataclass
from pathlib import Path

# The caption blocks are separated by a lone dot, which is how Instagram
# renders a readable paragraph break.
BLOCK_SEPARATOR = "\n.\n"

DETAIL_ICONS = (
    ("camera", "📷"),
    ("lens", "👁️"),
    ("film", "🎞️"),
    ("lab", "🧪"),
    ("scan", "💿"),
    ("date", "🗓️"),
)


def hashtagify(tags):
    """Turn a loose list of words into hashtags, leaving existing ones alone."""
    return re.sub(r"#?(\w+)", r"#\1", tags)


def _terminated(text):
    return text if text.endswith((".", "!", "?")) else text + "."


@dataclass
class Post:
    filepath: Path
    title: str = ""
    description: str = ""
    tags: str = ""
    camera: str = ""
    lens: str = ""
    film: str = ""
    lab: str = ""
    scan: str = ""
    date: str = ""
    location: str = ""
    lat: str = ""
    lng: str = ""
    usertag: str = ""

    @property
    def hashtags(self):
        return hashtagify(self.tags)

    @property
    def gear(self):
        """The camera/lens/film block, skipping whatever was left blank."""
        return "\n".join(
            "%s %s" % (icon, _terminated(getattr(self, field)))
            for field, icon in DETAIL_ICONS
            if getattr(self, field)
        )

    @property
    def caption(self):
        blocks = [
            _terminated(self.title) if self.title else "",
            self.gear,
            _terminated(self.description) if self.description else "",
            self.hashtags,
        ]
        return BLOCK_SEPARATOR.join(block for block in blocks if block)
