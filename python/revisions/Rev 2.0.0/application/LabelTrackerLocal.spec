# -*- mode: python ; coding: utf-8 -*-
import os

# Set the name for the application executable and output folder
app_name = 'LabelTrackerLocal'

# Get the directory containing this spec file (application directory)
app_root = os.path.dirname(SPECPATH)

# --- Files to bundle with the application ---
data_files = [
    # Use paths relative to the spec file location
    ('gui/images', 'gui/images'),
]

# --- Hidden imports PyInstaller might miss ---
hidden_imports = [
    'sqlite3',
    'bcrypt',
]

block_cipher = None

a = Analysis(
    ['run_local.py'],
    pathex=[app_root],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
) 