"""Running a post across platforms, as a stream of events.

The CLI prints the events, the GUI turns them into signals -- neither owns the
control flow, so the two cannot drift apart.
"""

from dataclasses import dataclass

# Event kinds, in the order they occur for one platform.
START = "start"
PREPARED = "prepared"
DONE = "done"
FAILED = "failed"


@dataclass
class Event:
    kind: str
    platform: str
    detail: str = ""
    prepared: object = None


def run(publishers, post, dry_run=False):
    """Yield the events of one publishing run; never raises for a platform."""
    for publisher in publishers:
        yield Event(START, publisher.name)

        try:
            prepared = publisher.prepare(post)
        except Exception as error:
            yield Event(FAILED, publisher.name, "preparation failed: %s" % error)
            continue

        yield Event(PREPARED, publisher.name, prepared=prepared)

        if dry_run:
            yield Event(DONE, publisher.name, "dry run, nothing posted")
            continue

        try:
            yield Event(DONE, publisher.name, publisher.publish(post, prepared))
        except Exception as error:
            yield Event(
                FAILED, publisher.name, "%s: %s" % (type(error).__name__, error)
            )
