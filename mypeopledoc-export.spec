# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller script to build the standalone
# MyPeopleDoc export executable.
#
# Prerequisite (done by build_exe.py):
#   PLAYWRIGHT_BROWSERS_PATH=0 python -m playwright install firefox
#
# This downloads Firefox into .local-browsers inside the playwright
# package. collect_all("playwright") will then bundle that browser
# into the executable, so it can be used without any additional
# installation.

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("playwright")

a = Analysis(
    ["export_mypeopledoc.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="mypeopledoc-export",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
