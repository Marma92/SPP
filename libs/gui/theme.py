"""One palette, one stylesheet.

A photo is judged on the photo, so the window stays dark and warm-neutral and
keeps its own colour out of the way.
"""

BG = "#1e1c1a"
CHROME = "#26231f"
PANEL = "#221f1c"
FIELD = "#211e1b"
SUNKEN = "#191715"
BORDER = "#332e28"
BORDER_HI = "#4a443c"
TEXT = "#ece7e0"
TEXT_DIM = "#ded7cd"
MUTED = "#8b8278"
FAINT = "#6f675e"
GHOST = "#5a544c"
ACCENT = "#e3a24a"
INFO = "#6fb0b2"
DANGER = "#e08b76"
OK = "#7fae6f"

SANS = "'IBM Plex Sans', 'Segoe UI', sans-serif"
MONO = "'IBM Plex Mono', Consolas, monospace"

QSS = """
/* No background on the generic rule: a plain container must stay transparent,
   otherwise every helper QWidget paints a pale rectangle over its panel. */
QWidget {{ color: {text}; font-family: {sans}; font-size: 13px; }}
QMainWindow, QDialog {{ background: {bg}; }}
QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{ background: transparent; }}

QFrame#chrome {{ background: {chrome}; border-bottom: 1px solid {border}; }}
QFrame#footer {{ background: {panel}; border-top: 1px solid {border}; }}
QFrame#formPane {{ border-left: 1px solid {border}; }}
QFrame#preview {{ background: {sunken}; border: 1px solid {border}; border-radius: 8px; }}
QFrame#drop {{ background: #232019; border: 2px dashed {border_hi}; border-radius: 12px; }}
QFrame#card {{ background: #272320; border: 1px solid {border_hi}; border-radius: 10px; }}
QFrame#rule {{ background: #302b26; max-height: 1px; border: none; }}

QLabel {{ background: transparent; }}
QLabel[role="wordmark"] {{ font-family: {mono}; font-size: 15px; font-weight: 600;
    letter-spacing: 1px; color: {accent}; }}
QLabel[role="label"] {{ font-size: 10px; letter-spacing: 1px; color: {faint}; }}
QLabel[role="section"] {{ font-size: 10px; letter-spacing: 1px; color: {muted}; }}
QLabel[role="mono"] {{ font-family: {mono}; font-size: 11px; color: {faint}; }}
QLabel[role="hint"] {{ font-size: 12px; color: {muted}; }}
QLabel[role="title"] {{ font-size: 21px; color: {text}; }}
QLabel[role="badge"] {{ font-size: 9px; letter-spacing: 1px; padding: 2px 5px;
    border-radius: 3px; color: {info}; background: rgba(111,176,178,0.13); }}
QLabel[role="badge"][kind="last"] {{ color: #9a8f82; background: rgba(154,143,130,0.13); }}
QLabel[role="badge"][kind="preset"] {{ color: {accent}; background: rgba(227,162,74,0.14); }}
QLabel[role="counter"] {{ font-family: {mono}; font-size: 11px; color: {muted};
    background: #241f1c; border: 1px solid {border}; border-radius: 4px; padding: 2px 7px; }}
QLabel[role="counter"][over="true"] {{ color: {danger}; background: rgba(224,139,118,0.12);
    border-color: rgba(224,139,118,0.32); }}
QLabel[role="warn"] {{ font-size: 12px; color: {danger}; }}

QLineEdit, QPlainTextEdit {{ background: {field}; border: 1px solid {border};
    border-radius: 5px; padding: 4px 9px; color: {text_dim}; selection-background-color: {accent};
    selection-color: #241f18; }}
QLineEdit:focus, QPlainTextEdit:focus {{ border-color: {border_hi}; }}
QTextEdit#caption {{ background: {field}; border: 1px solid #302b26; border-radius: 7px;
    padding: 10px 12px; }}

QPushButton {{ background: #2f2a24; border: 1px solid {border_hi}; border-radius: 6px;
    padding: 8px 16px; color: {text_dim}; }}
QPushButton:hover {{ background: #38322b; }}
QPushButton#primary {{ background: {accent}; border: none; color: #241f18; font-weight: 600;
    padding: 9px 18px; }}
QPushButton#primary:hover {{ background: #f0b25c; }}
QPushButton#primary:disabled {{ background: #332c25; color: #736b62; }}
QPushButton[role="tab"] {{ background: transparent; border: 1px solid transparent;
    border-radius: 5px; padding: 6px 12px; color: {muted}; font-size: 12px; }}
QPushButton[role="tab"]:checked {{ background: #37312a; border-color: {border_hi}; color: {text}; }}

QCheckBox {{ spacing: 8px; color: {text_dim}; }}
QCheckBox::indicator {{ width: 15px; height: 15px; border-radius: 3px;
    border: 1px solid {border_hi}; background: transparent; }}
QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; }}
QCheckBox:disabled {{ color: {ghost}; }}

QProgressBar {{ background: #322d27; border: none; border-radius: 2px; max-height: 4px; }}
QProgressBar::chunk {{ background: {accent}; border-radius: 2px; }}

/* The completion popup, so a suggestion list does not arrive looking foreign. */
QAbstractItemView {{ background: #2a2622; color: {text_dim}; border: 1px solid {border_hi};
    border-radius: 5px; outline: none; padding: 2px;
    selection-background-color: #37312a; selection-color: {text}; }}

QComboBox {{ background: {field}; border: 1px solid {border}; border-radius: 5px;
    padding: 4px 9px; color: {text_dim}; }}
QComboBox:hover {{ border-color: {border_hi}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}

QScrollArea {{ border: none; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #3a352f; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
""".format(
    bg=BG, chrome=CHROME, panel=PANEL, field=FIELD, sunken=SUNKEN, border=BORDER,
    border_hi=BORDER_HI, text=TEXT, text_dim=TEXT_DIM, muted=MUTED, faint=FAINT,
    ghost=GHOST, accent=ACCENT, info=INFO, danger=DANGER, sans=SANS, mono=MONO,
)
