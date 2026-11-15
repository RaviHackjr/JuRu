# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — one `juru` executable, no Python installation needed.

Build:  python3 -m PyInstaller juru.spec
Result: dist/juru          (Linux / macOS)
        dist/juru.exe      (Windows)

The templates that power `juru --new` ride along as data, placed inside
the bundle next to the frozen cli module — the same relative layout the
package uses on disk.
"""

a = Analysis(
    ["juru_entry.py"],
    pathex=["src"],
    binaries=[],
    datas=[("src/juru/templates", "juru/templates")],
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
