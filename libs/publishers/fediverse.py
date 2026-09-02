"""Mastodon, and Pixelfed — which speaks Mastodon's API.

The two differ by their address and their token and by nothing else this
application cares about, so they share an implementation and appear as two
platforms. Adding another Mastodon-compatible server is three lines.
"""

from libs import config
from libs.images import prepare_for_fediverse
from libs.publishers.base import Publisher


class FediversePublisher(Publisher):
    # The prefix of the environment variables this platform reads.
    prefix = ""
    requires = ("mastodon",)
    image_label = "2048 px"

    def credentials(self):
        return config.FediverseAuth.load(self.name.capitalize(), self.prefix)

    @property
    def limit(self):
        """Instance-configurable, so it is read every time rather than fixed.

        Asking the server would mean a network call in the preview, which is
        the one thing the preview must never do.
        """
        return config.fediverse_limit(self.prefix)

    def prepare_image(self, post):
        return prepare_for_fediverse(post.filepath)

    def publish(self, post, prepared):
        from mastodon import Mastodon

        auth = self.credentials()
        client = Mastodon(access_token=auth.token, api_base_url=auth.instance)

        media = client.media_post(
            str(prepared.image),
            mime_type="image/jpeg",
            description=post.alt or post.description or post.title or None,
            # The server processes an upload after accepting it, and a status
            # posted before that finishes is refused. This waits.
            synchronous=True,
        )
        status = client.status_post(
            prepared.text,
            media_ids=[media],
            language=config.POST_LANGS[0] if config.POST_LANGS else None,
        )
        return status["url"] or "%s/@me" % auth.instance


class MastodonPublisher(FediversePublisher):
    name = "mastodon"
    prefix = "MASTODON"


class PixelfedPublisher(FediversePublisher):
    name = "pixelfed"
    prefix = "PIXELFED"
