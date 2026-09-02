"""Bluesky, over the AT Protocol.

Credentials are a handle plus an *app password* (Settings > Privacy and
security > App passwords), never the account password itself.
"""

import re
import unicodedata

from libs import config
from libs.images import prepare_for_bluesky
from libs.publishers.base import Publisher

# Bluesky caps a post at 300 graphemes.
POST_MAX_GRAPHEMES = 300
ELLIPSIS = "\u2026"

# Combining marks and format characters -- variation selectors, zero-width
# joiners -- do not start a new grapheme, so they must not be counted.
# "\U0001F39E\uFE0F" is one grapheme, not two.
ZERO_WIDTH_CATEGORIES = {"Mn", "Me", "Cf"}

TAG_PATTERN = re.compile(r"(#\w+)")


def grapheme_length(text):
    return sum(
        1 for char in text if unicodedata.category(char) not in ZERO_WIDTH_CATEGORIES
    )


def rich_text(text):
    """Rebuild the caption with real facets, so the hashtags are clickable."""
    from atproto import client_utils

    builder = client_utils.TextBuilder()
    for chunk in TAG_PATTERN.split(text):
        if not chunk:
            continue
        if chunk.startswith("#") and len(chunk) > 1:
            builder.tag(chunk, chunk[1:])
        else:
            builder.text(chunk)
    return builder


class BlueskyPublisher(Publisher):
    name = "bluesky"
    requires = ("atproto",)
    image_label = "2000 px"
    limit = POST_MAX_GRAPHEMES

    def credentials(self):
        return config.BlueskyAuth.load()

    def measure(self, text):
        return grapheme_length(text)

    def split_text(self, post):
        text = unicodedata.normalize("NFC", post.caption)
        if grapheme_length(text) <= POST_MAX_GRAPHEMES:
            return text, ""

        budget = POST_MAX_GRAPHEMES - grapheme_length(ELLIPSIS)
        cut = 0
        used = 0
        for index, char in enumerate(text):
            if unicodedata.category(char) not in ZERO_WIDTH_CATEGORIES:
                used += 1
            if used > budget:
                break
            cut = index + 1
        return text[:cut].rstrip() + ELLIPSIS, text[cut:]

    def prepare_image(self, post):
        return prepare_for_bluesky(post.filepath)

    def _connect(self, auth):
        from atproto import Client

        if config.BLUESKY_SESSION_FILE.exists():
            try:
                client = Client()
                client.login(
                    session_string=config.BLUESKY_SESSION_FILE.read_text(encoding="utf-8")
                )
                return client
            except Exception as error:
                print("Bluesky session unusable (%s), logging in again." % error)

        client = Client()
        client.login(auth.handle, auth.app_password)
        return client

    def publish(self, post, prepared):
        from atproto import models
        from PIL import Image

        auth = self.credentials()
        client = self._connect(auth)

        with Image.open(prepared.image) as image:
            width, height = image.size

        response = client.send_image(
            text=rich_text(prepared.text),
            image=prepared.image.read_bytes(),
            # Alt text is not optional on Bluesky; fall back to the legend.
            image_alt=post.alt or post.description or post.title or "",
            image_aspect_ratio=models.AppBskyEmbedDefs.AspectRatio(
                width=width, height=height
            ),
            # Without this the SDK declares English, and a French caption gets
            # filtered out or offered for translation.
            langs=config.POST_LANGS,
        )

        config.SESSION_DIR.mkdir(parents=True, exist_ok=True)
        config.BLUESKY_SESSION_FILE.write_text(
            client.export_session_string(), encoding="utf-8"
        )
        return "https://bsky.app/profile/%s/post/%s" % (
            auth.handle,
            response.uri.rsplit("/", 1)[-1],
        )
