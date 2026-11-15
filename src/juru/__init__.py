"""JuRu — the easy, secure programming language.

    .jr files, plain-English keywords, human error messages.

Home: https://github.com/RaviHackjr/JuRu
"""
import sys

from .version import VERSION

# On Windows, a piped or redirected stdout/stderr uses the legacy code
# page (often cp1252), which cannot encode JuRu's Unicode output — a
# program as simple as `juru hello.jr > out.txt` would crash. Pin UTF-8
# for our streams; a real console already uses it, and on other systems
# this block never runs. Kept in __init__ so every entry point (the
# launchers, the pip command, the frozen interpreter) gets it.
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8")
            except (OSError, ValueError):    # stream not reconfigurable
                pass

__all__ = ["VERSION"]
