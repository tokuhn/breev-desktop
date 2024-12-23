# Breev for Desktop

Breev is a comprehensive 360° knowledge management platform designed to ensure that critical information is never lost within your organization. Whether it's documenting meetings, sharing knowledge with customers, or empowering employees and stakeholders, Breev offers the perfect software solution to streamline and enhance your business operations.

## Table of Contents
- [Technologies](#technologies)
- [Build Instructions](#build-instructions)
- [Authors](#authors)

## Technologies
- FFmpeg
- PyQt5

## Build Instructions

### MacOS
1. Install FFmpeg using Homebrew: `brew install ffmpeg`
2. Create a `.spec` file and add FFmpeg as a binary.
3. Build the project using PyInstaller: `pyinstaller your_spec_file.spec`

### Windows
1. Download FFmpeg from the official website and place it in the Windows directory of this project.
2. Create a `.spec` file and add FFmpeg as a binary.
3. Build the project using PyInstaller: `pyinstaller your_spec_file.spec`

### Example .spec File
```
# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[('/opt/homebrew/bin/ffmpeg', 'ffmpeg')], 
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Breev',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='Breev.app',
    icon='icon.png',
    bundle_identifier=None,
    info_plist={
        'NSMicrophoneUsageDescription': 'This app requires access to the microphone to capture audio.'
    }
)
```

## Authors
- Tom Kuhn ([GitHub](https://github.com/tokuhn/), [LinkedIn](https://www.linkedin.com/in/tokuhn/))