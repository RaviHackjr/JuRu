# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — one `juru` executable, no Python installation needed.

Build:  python3 -m PyInstaller juru.spec
Result: dist/juru          (Linux / macOS)
        dist/juru.exe      (Windows)

Two details that matter:
  - the entry script lives in packaging/ so the repo-root launcher
    `juru.py` can never shadow the real `juru` package during analysis;
  - the templates for `--new` are collected into the bundle root, where
    cli.py finds them via sys._MEIPASS.
"""

import os

SPECDIR = SPECPATH   # PyInstaller injects the spec file's directory

a = Analysis(
    [os.path.join(SPECDIR, "packaging", "juru_entry.py")],
    pathex=[os.path.join(SPECDIR, "src")],
    binaries=[],
    datas=[(os.path.join(SPECDIR, "src", "juru", "templates"), "templates")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="juru",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
