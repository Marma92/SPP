"""Twitter/X.

WARNING: still on Twython and `update_status`, i.e. API v1.1, shut down in
2023. Kept wired up so the port to the v2 API is a one-file change, but it
will fail against the live API.
"""

import unicodedata

from libs import config
from libs.images import prepare_for_twitter
from libs.publishers.base import Prepared, Publisher

TWEET_MAX_WEIGHT = 280
ELLIPSIS = "\u2026"


def weighted_length(text):
    """Approximate Twitter's own count: CJK and emoji weigh 2, the rest 1.

    Counting UTF-8 bytes instead charges 7 for a single emoji, which truncated
    our captions at roughly half their real length.
    """
    return sum(1 if ord(char) < 0x1100 else 2 for char in text)


def tweetable(tweet):
    tweet = unicodedata.normalize("NFC", tweet)
    if weighted_length(tweet) <= TWEET_MAX_WEIGHT:
        return tweet

    budget = TWEET_MAX_WEIGHT - weighted_length(ELLIPSIS)
    cut = 0
    used = 0
    for index, char in enumerate(tweet):
        used += 1 if ord(char) < 0x1100 else 2
        if used > budget:
            break
        cut = index + 1
    return tweet[:cut].rstrip() + ELLIPSIS


class TwitterPublisher(Publisher):
    name = "twitter"

    def credentials(self):
        return config.TwitterAuth.load()

    def prepare(self, post):
        return Prepared(
            image=prepare_for_twitter(post.filepath),
            text=tweetable(post.caption),
        )

    def publish(self, post, prepared):
        from twython import Twython

        auth = self.credentials()
        twitter = Twython(
            auth.consumer_key,
            auth.consumer_secret,
            auth.access_token,
            auth.access_token_secret,
        )

        with open(prepared.image, "rb") as image:
            media = twitter.upload_media(media=image)
        status = twitter.update_status(
            status=prepared.text, media_ids=[media["media_id"]]
        )
        return "https://x.com/i/status/%s" % status["id_str"]
