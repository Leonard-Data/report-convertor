# -*- mode: python ; coding: utf-8 -*-
# macOS build — produces a .app bundle (run on macOS only)

import boto3
import botocore
from pathlib import Path

boto3_data    = str(Path(boto3.__file__).parent   / "data")
botocore_data = str(Path(botocore.__file__).parent / "data")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # boto3/botocore endpoint + service data (required at runtime)
        (boto3_data,    'boto3/data'),
        (botocore_data, 'botocore/data'),
    ],
    hiddenimports=[
        # boto3 / botocore dynamic loaders
        'boto3.session',
        'boto3.s3.inject',
        'botocore.loaders',
        'botocore.regions',
        'botocore.configprovider',
        'botocore.handlers',
        'botocore.auth',
        'botocore.awsrequest',
        'botocore.endpoint',
        'botocore.parsers',
        'botocore.serialize',
        'botocore.signers',
        'botocore.translate',
        'botocore.utils',
        'botocore.session',
        'botocore.credentials',
        'botocore.config',
        'botocore.exceptions',
        # pydantic v2 core (Rust extension, not auto-detected)
        'pydantic',
        'pydantic_core',
        # openpyxl styles (loaded dynamically)
        'openpyxl.styles',
        'openpyxl.styles.fills',
        'openpyxl.reader.excel',
        # dotenv — submodules needed for frozen exe
        'dotenv',
        'dotenv.main',
        'dotenv.variables',
        'dotenv.parser',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # dev / test tools — not needed at runtime
        'pytest',
        'pytest_qt',
        '_pytest',
        'setuptools',
        'wheel',
        'pip',
        # unused heavy packages
        'matplotlib',
        'scipy',
        'tkinter',
        'IPython',
        'notebook',
        'jupyter',
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

# macOS: exclude_binaries=True so COLLECT gathers them into the .app bundle
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='report-convertor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX is not available / recommended on macOS
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,  # must be False with PyQt6 — causes crash on macOS
    target_arch=None,     # None = native arch; use 'universal2' for fat binary
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='report-convertor',
)

app = BUNDLE(
    coll,
    name='report-convertor.app',
    # Provide a .icns file here to set a custom dock / Finder icon, e.g.:
    # icon='report_convertor/resources/icon.icns',
    icon=None,
    bundle_identifier='com.leonarddata.reportconvertor',
    info_plist={
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
        'CFBundleShortVersionString': '1.0.0',
    },
)
