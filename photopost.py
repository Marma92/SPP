"""Interactive entry point: collect the picture and its metadata, then post."""

from libs import spplib


def ask(prompt):
    return input(prompt).strip()


def post(platform, func, *args):
    """Run one platform's poster; a failure there must not sink the others."""
    try:
        func(*args)
    except Exception as error:
        print("%s post failed: %s" % (platform, error))


def main():
    print("Welcome to the simplephotoposter!")

    filepath = ask("Enter a path for your picture to post: ")
    title = ask("Give a title to your picture: ")
    description = ask("Give a legend to your picture: ")
    tags = ask("Give it now some tags: ")

    camera = ask("Which camera did you use ? ")
    lens = ask("And which lens ? ")
    film = ask("Which film did you use ? (leave blank if not) ")
    lab = ask("Any special lab ? (leave blank if not) ")
    scan = ask("Who scanned it ? (leave blank if not) ")
    date = ask("Date of capture? (leave blank if not) ")

    location = ask("Place of capture? (leave blank if not) ")
    lat = lng = ""
    if location:
        lat = ask("Latitude ? ")
        lng = ask("Longitude ? ")
    tag = ask("Someone to tag? (leave blank if not) ")

    text = spplib.text_formation(
        title, description, tags, camera, lens, film, lab, scan, date
    )

    print("And here ya go!")
    post("Twitter", spplib.tweet_a_pic, filepath, text)
    post("Flickr", spplib.flick_a_pic, filepath, title, text, tags)
    post("Instagram", spplib.insta_post, filepath, text, location, lat, lng, tag)


if __name__ == "__main__":
    main()
