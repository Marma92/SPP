"""Post one picture to every configured platform at once."""

import argparse
import sys
from pathlib import Path

from libs import config, exif, lastpost, publishers, runner
from libs.post import Post


def ask(prompt, default=""):
    """Ask one question; an empty answer keeps the proposed default."""
    answer = input("%s%s: " % (prompt, " [%s]" % default if default else "")).strip()
    return answer or default


def collect(picture=None):
    """Prompt for the picture and its metadata, pre-filled where we can."""
    filepath = picture or ask("Enter a path for your picture to post")
    post = Post(filepath=Path(filepath).expanduser())
    if not post.filepath.is_file():
        raise SystemExit("No such picture: %s" % post.filepath)

    hints = exif.read(post.filepath)
    remembered = lastpost.load()
    if hints.filled():
        print("Read from the EXIF: %s -- press enter to keep what is proposed."
              % ", ".join(hints.filled()))
    if any(remembered.values()):
        print("Carried over from your last post: %s."
              % ", ".join(field for field, value in remembered.items() if value))

    post.title = ask("Give a title to your picture")
    post.description = ask("Give a legend to your picture")
    post.alt = ask("Describe the picture for screen readers? (blank = reuse the legend)")
    post.tags = ask("Give it now some tags")

    post.camera = ask("Which camera did you use ?", hints.camera)
    post.lens = ask("And which lens ?", hints.lens)
    post.film = ask("Which film did you use ? (leave blank if not)", remembered["film"])
    post.lab = ask("Any special lab ? (leave blank if not)", remembered["lab"])
    post.scan = ask("Who scanned it ? (leave blank if not)", remembered["scan"])
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
    print("\nAnd here ya go!")

    results = []
    for event in runner.run(selected, post, args.dry_run):
        if event.kind == runner.PREPARED:
            print("\n--- %s ---" % event.platform)
            print("image: %s" % event.prepared.image)
            print(event.prepared.text)
        elif event.kind in (runner.DONE, runner.FAILED):
            results.append((event.platform, event.kind == runner.DONE, event.detail))

    print("\n=== summary ===")
    for platform, ok, detail in results:
        print("%-10s %s  %s" % (platform, "ok " if ok else "FAIL", detail))

    if not args.dry_run and any(ok for _, ok, _ in results):
        lastpost.save(post)
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
