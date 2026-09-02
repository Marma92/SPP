from libs import config
from libs.images import prepare_for_instagram
from libs.publishers.base import Publisher


class InstagramPublisher(Publisher):
    name = "instagram"
    requires = ("instagrapi",)
    image_label = "1440\u00b2"
    limit = 2200

    def credentials(self):
        return config.InstagramAuth.load()

    def prepare_image(self, post):
        return prepare_for_instagram(post.filepath)

    def _save(self, client):
        """instagrapi's own JSON settings, rather than a pickle of the client.

        These carry the device identifiers Instagram fingerprints the login
        with, so they must survive every attempt, successful or not.
        """
        config.SESSION_DIR.mkdir(parents=True, exist_ok=True)
        client.dump_settings(config.INSTAGRAM_SESSION_FILE)

    def _connect(self, auth):
        from instagrapi import Client

        client = Client()
        if config.INSTAGRAM_SESSION_FILE.exists():
            client.load_settings(config.INSTAGRAM_SESSION_FILE)
        else:
            # Freeze the freshly generated device before logging in. A
            # verification challenge aborts login(), and coming back with a
            # different device only earns another challenge -- so the very
            # first attempt has to leave its identifiers on disk.
            self._save(client)

        try:
            if auth.sessionid:
                client.login_by_sessionid(auth.sessionid)
            else:
                client.login(auth.username, auth.password)
        finally:
            self._save(client)
        return client

    def publish(self, post, prepared):
        from instagrapi.types import Location, Usertag

        auth = self.credentials()
        client = self._connect(auth)

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
            self._save(client)
