from libs import config
from libs.publishers.base import Publisher


class FlickrPublisher(Publisher):
    name = "flickr"
    image_label = "original"
    limit = None

    def credentials(self):
        return config.FlickrAuth.load()

    def prepare_image(self, post):
        # Flickr is the archive: it gets the original file, untouched.
        return post.filepath

    def publish(self, post, prepared):
        import flickrapi

        auth = self.credentials()
        flickr = flickrapi.FlickrAPI(auth.api_key, auth.api_secret)
        # The OAuth token is cached, so the browser only opens the first time.
        if not flickr.token_valid(perms="delete"):
            flickr.authenticate_via_browser(perms="delete")

        result = flickr.upload(
            filename=str(prepared.image),
            title=post.title,
            description=prepared.text,
            tags=post.tags,
        )
        photo_id = result.find("photoid").text
        return "https://www.flickr.com/photo.gne?id=%s" % photo_id
