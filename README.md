# SPP

Simple Photo Poster : how to post photos to many places at the same time.

### Requirements ###

Python 3.9+ and the libraries listed in `requirements.txt` (Pillow, flickrapi,
instagrapi, twython, python-dotenv).

```
python -m venv .venv
.venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration ###

Credentials live in a git-ignored `.env` file at the root of the project:

```
cp .env.example .env
```

Then fill in the platforms you actually use. A platform left blank is skipped
with a clear message instead of crashing the run.

### To use it ###

```
python photopost.py                          # asks for the picture, posts everywhere
python photopost.py shot.jpg --dry-run       # prepares and shows, posts nothing
python photopost.py shot.jpg -p flickr,instagram
```

By default it posts to every platform configured in `.env`; `SPP_PLATFORMS`
sets a narrower default, and `--platforms` overrides both. A platform that
fails is reported in the summary without stopping the others, and the exit
code is non-zero if any of them failed.

### Metadata ###

Camera, lens, capture date and GPS coordinates are read from the picture's
EXIF and proposed as defaults: press enter to keep one, type over it to
replace it. A film scan usually carries none of this, in which case the
questions are simply asked empty, as before.

### Adding a platform ###

One module in `libs/publishers/` implementing `credentials`, `prepare` and
`publish`, listed in `libs/publishers/__init__.py`. Nothing else changes.

### Platform status ###

| Platform  | Credentials | Notes |
|-----------|-------------|-------|
| Flickr    | API key + secret | OAuth token is cached, the browser only opens the first time |
| Instagram | handle + password | via `instagrapi`, i.e. the private mobile API (no official key for personal accounts) |
| Bluesky   | handle + app password | full-frame picture, clickable hashtags, alt text |

Twitter/X was dropped: it sat on API v1.1, shut down in 2023. The publisher is
still in the history (`git log -- libs/publishers/twitter.py`) if it ever needs
reviving on the v2 API.

### TODO ###

_(paste from todo.txt)_

- More platforms: Mastodon, Pixelfed.
- GUI (`libs/sppgui.py` is a skeleton, not wired to anything yet).
