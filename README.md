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
python photopost.py
```

### Platform status ###

| Platform  | State | Notes |
|-----------|-------|-------|
| Flickr    | works | OAuth token is cached, the browser only opens the first time |
| Instagram | works | via `instagrapi`, i.e. the private mobile API (no official key for personal accounts) |
| Twitter/X | **broken** | still on Twython / API v1.1, shut down in 2023; needs a port to the v2 API |

### TODO ###

_(paste from todo.txt)_

- Port Twitter to the v2 API, or replace it (Bluesky, Mastodon, Pixelfed).
- Per-platform selection instead of all-or-nothing.
- Read EXIF to prefill camera, lens and date.
- GUI (`libs/sppgui.py` is a skeleton, not wired to anything yet).
