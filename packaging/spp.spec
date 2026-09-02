# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build for the SPP window.

Built as one folder rather than one file: the bundled Chromium would otherwise
be unpacked into a temporary directory on every single launch.

Run it from the project root:

    pyinstaller packaging/spp.spec
"""

from pathlib import Path

PROJECT = Path(SPECPATH).parent

# The platform clients are imported inside publish(), and the Instagram login
# inside its button handler, so that the app starts without them and says so
# when one is missing. PyInstaller reads imports statically and finds none of
# them: naming them here is the price of that deliberate laziness.
HIDDEN = [
    "flickrapi",
    "instagrapi",
    "atproto",
    "libs.gui.instagramlogin",
]

analysis = Analysis(
    [str(PROJECT / "spp_gui.py")],
    pathex=[str(PROJECT)],
    binaries=[],
    datas=[],
    hiddenimports=HIDDEN,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)

# Chromium ships its devtools resources twice, once with debug symbols. The
# debug copies are 75 MB that a released build never opens.
analysis.datas = [
    entry for entry in analysis.datas if not entry[0].endswith(".debug.pak")
]
analysis.binaries = [
    entry for entry in analysis.binaries if not entry[0].endswith(".debug.pak")
]

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="SPP",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(PROJECT / "packaging" / "spp.ico"),
)

COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="SPP",
)
