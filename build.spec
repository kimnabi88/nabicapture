# PyInstaller spec for NabiCapture (one-file, windowed).
# Usage: pyinstaller build.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/default_config.json', 'config'),
        ('resources/styles/main.qss', 'resources/styles'),
        # add ('resources/icons/*.png', 'resources/icons') once icons exist
    ],
    hiddenimports=[
        'keyboard', 'mss', 'PIL.Image', 'win32gui', 'win32clipboard',
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NabiCapture',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # windowed (no cmd popup)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='resources/icons/app.ico',
)
