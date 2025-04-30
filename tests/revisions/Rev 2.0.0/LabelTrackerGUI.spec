# -*- mode: python ; coding: utf-8 -*-
import os

# Set the name for the application executable and output folder
app_name = 'LabelTrackerGUI'

# Get the directory containing this spec file (project root)
project_root = os.path.dirname(SPECPATH)
# --- Add Debug Print ---
print(f"DEBUG - Spec file location (project_root): {project_root}") 

# --- Files to bundle with the application --- 
data_files = [
    # Use paths relative to the spec file location
    ('gui/images', 'gui/images'),
    ('gui_config.ini', '.'),
]
print(f"DEBUG - Datas to add: {data_files}")

# --- Hidden imports PyInstaller might miss ---
hidden_imports = [
    'sqlalchemy.dialects.postgresql', # If using PostgreSQL
    'psycopg2',                     # PostgreSQL driver
    # Add other potential hidden imports if errors occur during build/run
    # e.g., 'pkg_resources.py2_warn' if you see related warnings
]

block_cipher = None

a = Analysis(
    # Use relative path since spec file and script are in the same dir
    ['run_gui.py'], 
    pathex=[project_root],        # Keep project root for imports
    binaries=[],
    datas=data_files,             # Include data files specified above
    hiddenimports=hidden_imports, # Include hidden imports specified above
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
    name=app_name,              # Name of the executable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,               # Use console=False for a GUI-only app (no cmd window)
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
    name=app_name,              # Name of the output folder
) 