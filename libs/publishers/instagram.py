from libs import config
from libs.images import prepare_for_instagram
from libs.publishers.base import Prepared, Publisher


class InstagramPublisher(Publisher):
    name = "instagram"

    def credentials(self):
        return config.InstagramAuth.load()

    def prepare(self, post):
        return Prepared(image=prepare_for_instagram(post.filepath), text=post.caption)

    def publish(self, post, prepared):
        from instagrapi import Client
        from instagrapi.types import Location, Usertag

        auth = self.credentials()

        # instagrapi's own JSON settings, rather than pickling the whole
        # client: a pickle breaks on every library upgrade.
        client = Client()
        if config.INSTAGRAM_SESSION_FILE.exists():
            client.load_settings(config.INSTAGRAM_SESSION_FILE)
        client.login(auth.username, auth.password)

        location = None
        if post.location:
            location = Location(
                name=post.location,
                lat=float(post.lat) if post.lat else None,
                lng=float(post.lng) if post.lng else None,
            )

        usertags = []
        if post.usertag:
            # photo_upload wants a user object, not a username string.
            user = client.user_info_by_username(post.usertag.lstrip("@"))
            usertags = [Usertag(user=user, x=0.5, y=0.5)]

        try:
            media = client.photo_upload(
                prepared.image, prepared.text, usertags=usertags, location=location
            )
            return "https://www.instagram.com/p/%s/" % media.code
        finally:
            config.SESSION_DIR.mkdir(parents=True, exist_ok=True)
            client.dump_settings(config.INSTAGRAM_SESSION_FILE)
