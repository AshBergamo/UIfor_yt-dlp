# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

project_dir = Path(SPECPATH).resolve()
sys.path.insert(0, str(project_dir.parent / "scripts"))
from packaging_support import build_inputs
binaries, datas = build_inputs(project_dir)

a = Analysis(
    [str(project_dir / "baixar_musica_qt.py")],
    pathex=[str(project_dir), str(project_dir.parent)],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtNetwork",
        "yt_dlp_ejs",
        "yt_dlp",
        "yt_dlp.extractor.youtube",
        "yt_dlp.extractor.extractors",
        "yt_dlp.downloader",
        "yt_dlp.postprocessor",
        "mutagen",
        "websockets",
        "certifi",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "tkinter.*",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PIL",
        "cv2",
        "torch",
        "tensorflow",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="baixar_musica_qt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
