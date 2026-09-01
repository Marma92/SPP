"""Text formatting and the per-platform posting functions.

Platform clients are imported lazily, inside the function that needs them, so
that importing this module (or running the image pipeline) does not require
every library to be installed.
"""

import re
import unicodedata

from libs import config
from libs.images import prepare_for_instagram, prepare_for_twitter

TWEET_MAX_WEIGHT = 280
ELLIPSIS = "…"


def hashtagify(tags):
    """Turn a loose list of words into hashtags, leaving existing ones alone."""
    return re.sub(r"#?(\w+)", r"#\1", tags)


def _weighted_length(text):
    """Approximate Twitter's own count: CJK and emoji weigh 2, the rest 1.

    The previous version counted UTF-8 bytes, which charges 7 for a single
    emoji -- captions like ours got truncated at roughly half their real length.
    """
    return sum(1 if ord(char) < 0x1100 else 2 for char in text)


def tweetable(tweet):
    tweet = unicodedata.normalize("NFC", tweet)
    if _weighted_length(tweet) <= TWEET_MAX_WEIGHT:
        return tweet

    print("This tweet weighs %d units. Shortening..." % _weighted_length(tweet))
    budget = TWEET_MAX_WEIGHT - _weighted_length(ELLIPSIS)
    cut = 0
    used = 0
    for index, char in enumerate(tweet):
        used += 1 if ord(char) < 0x1100 else 2
        if used > budget:
            break
        cut = index + 1
    return tweet[:cut].rstrip() + ELLIPSIS


def text_formation(title, description, tags, camera, lens, film, lab, scan, date):
    if film:
        film = "🎞️ " + film + ".\n"
    if lab:
        lab = "🧪 " + lab + ".\n"
    if scan:
        scan = "💿 " + scan + ".\n"
    if date:
        date = "🗓️ " + date + ".\n"

    return (
        title + ".\n.\n📷 " + camera + ".\n👁️ " + lens + ".\n"
        + film + lab + scan + date
        + ".\n.\n" + description + ".\n.\n" + hashtagify(tags)
    )


def tweet_a_pic(filepath, text):
    """Post to Twitter/X.

    NOTE: this still goes through Twython and `update_status`, i.e. API v1.1,
    which was shut down in 2023. It will fail until it is ported to the v2 API.
    """
    from twython import Twython

    auth = config.TwitterAuth.load()
    twitter = Twython(
        auth.consumer_key,
        auth.consumer_secret,
        auth.access_token,
        auth.access_token_secret,
    )

    tweet = tweetable(text)
    with open(prepare_for_twitter(filepath), "rb") as image:
        response = twitter.upload_media(media=image)
    twitter.update_status(status=tweet, media_ids=[response["media_id"]])
    print("Tweeted: %s" % tweet)


def flick_a_pic(filepath, title, description, tags):
    import flickrapi

    auth = config.FlickrAuth.load()
    flickr = flickrapi.FlickrAPI(auth.api_key, auth.api_secret)
    # flickrapi caches the OAuth token, so the browser only opens the first time.
    if not flickr.token_valid(perms="delete"):
        flickr.authenticate_via_browser(perms="delete")

    result = flickr.upload(
        filename=str(filepath), title=title, description=description, tags=tags
    )
    print("Flickered: %s" % result.find("photoid").text)


def insta_post(filepath, text, location_name="", lat=None, lng=None, tag=""):
    from instagrapi import Client
    from instagrapi.types import Location, Usertag

    auth = config.InstagramAuth.load()

    # instagrapi's own JSON settings, instead of pickling the whole client:
    # a pickle breaks on every library upgrade.
    client = Client()
    if config.INSTAGRAM_SESSION_FILE.exists():
        client.load_settings(config.INSTAGRAM_SESSION_FILE)
    client.login(auth.username, auth.password)

    location = None
    if location_name:
        location = Location(
            name=location_name,
            lat=float(lat) if lat else None,
            lng=float(lng) if lng else None,
        )

    usertags = []
    if tag:
        # photo_upload wants a user object, not a username string.
        usertags = [Usertag(user=client.user_info_by_username(tag.lstrip("@")), x=0.5, y=0.5)]

    try:
        client.photo_upload(
            prepare_for_instagram(filepath), text, usertags=usertags, location=location
        )
        print("Instagrammed: %s" % text.splitlines()[0])
    finally:
        config.SESSION_DIR.mkdir(parents=True, exist_ok=True)
        client.dump_settings(config.INSTAGRAM_SESSION_FILE)
