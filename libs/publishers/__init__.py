"""Registry of the available platforms."""

from libs.publishers.base import Prepared, Publisher, Result
from libs.publishers.bluesky import BlueskyPublisher
from libs.publishers.flickr import FlickrPublisher
from libs.publishers.instagram import InstagramPublisher

ALL = (FlickrPublisher, InstagramPublisher, BlueskyPublisher)
NAMES = tuple(cls.name for cls in ALL)


def parse_names(value):
    """Read a 'flickr,instagram' selection into a list of names."""
    return [name.strip().lower() for name in value.split(",") if name.strip()]


def resolve(names=None):
    """Instantiate the requested platforms, or every configured one."""
    by_name = {cls.name: cls for cls in ALL}
    if names:
        unknown = [name for name in names if name not in by_name]
        if unknown:
            raise ValueError(
                "Unknown platform(s): %s (available: %s)"
                % (", ".join(unknown), ", ".join(NAMES))
            )
        return [by_name[name]() for name in names]
    return [publisher for publisher in (cls() for cls in ALL) if publisher.is_configured()]
