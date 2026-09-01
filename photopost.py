"""Post one picture to every configured platform at once."""

import argparse
import sys
from pathlib import Path

from libs import config, exif, publishers
from libs.post import Post
from libs.publishers.base import Result


def ask(prompt, default=""):
    """Ask one question; an empty answer keeps the proposed default."""
    answer = input("%s%s: " % (prompt, " [%s]" % default if default else "")).strip()
    return answer or default


def collect(picture=None):
    """Prompt for the picture and its metadata, pre-filled from the EXIF."""
    filepath = picture or ask("Enter a path for your picture to post")
    post = Post(filepath=Path(filepath).expanduser())
    if not post.filepath.is_file():
        raise SystemExit("No such picture: %s" % post.filepath)

    hints = exif.read(post.filepath)
    if hints.filled():
        print("Read from the EXIF: %s -- press enter to keep what is proposed."
              % ", ".join(hints.filled()))

    post.title = ask("Give a title to your picture")
    post.description = ask("Give a legend to your picture")
    post.alt = ask("Describe the picture for screen readers? (blank = reuse the legend)")
    post.tags = ask("Give it now some tags")

    post.camera = ask("Which camera did you use ?", hints.camera)
    post.lens = ask("And which lens ?", hints.lens)
    post.film = ask("Which film did you use ? (leave blank if not)")
    post.lab = ask("Any special lab ? (leave blank if not)")
    post.scan = ask("Who scanned it ? (leave blank if not)")
    post.date = ask("Date of capture? (leave blank if not)", hints.date)

    post.location = ask(
        "Place of capture? (GPS found, name it to use it)" if hints.lat
        else "Place of capture? (leave blank if not)"
    )
    if post.location:
        post.lat = ask("Latitude ?", hints.lat)
        post.lng = ask("Longitude ?", hints.lng)
    post.usertag = ask("Someone to tag? (leave blank if not)")
    return post


def run(publisher, post, dry_run):
    """Prepare then publish on one platform, never raising into the caller."""
    try:
        prepared = publisher.prepare(post)
    except Exception as error:
        return Result(publisher.name, False, "preparation failed: %s" % error)

    print("\n--- %s ---" % publisher.name)
    print("image: %s" % prepared.image)
    print(prepared.text)

    if dry_run:
        return Result(publisher.name, True, "dry run, nothing posted")
    try:
        return Result(publisher.name, True, publisher.publish(post, prepared))
    except Exception as error:
        return Result(publisher.name, False, "%s: %s" % (type(error).__name__, error))


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "picture", nargs="?", help="path to the picture; asked for if omitted"
    )
    parser.add_argument(
        "-p",
        "--platforms",
        help="comma-separated list among %s; defaults to SPP_PLATFORMS, "
        "or to every platform configured in .env" % ", ".join(publishers.NAMES),
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="prepare the images and show the captions, post nothing",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    selection = args.platforms or config.DEFAULT_PLATFORMS
    try:
        selected = publishers.resolve(publishers.parse_names(selection))
    except ValueError as error:
        raise SystemExit(str(error))

    if not selected:
        raise SystemExit(
            "No platform configured. Copy .env.example to .env and fill it in, "
            "or pass --platforms."
        )

    print("Welcome to the simplephotoposter!")
    print("Posting to: %s%s" % (", ".join(p.name for p in selected),
                                " (dry run)" if args.dry_run else ""))

    post = collect(args.picture)
    results = [run(publisher, post, args.dry_run) for publisher in selected]

    print("\n=== summary ===")
    for result in results:
        print("%-10s %s  %s" % (result.platform, "ok " if result.ok else "FAIL", result.detail))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
