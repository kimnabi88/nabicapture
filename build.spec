# PyInstaller spec for NabiCapture (one-file, windowed).
# Usage: pyinstaller build.spec --clean

block_cipher = None

# Qt modules we don't use — each DLL is 5-20 MB
_QT_EXCLUDE = [
    'PyQt6.Qt3DAnimation', 'PyQt6.Qt3DCore', 'PyQt6.Qt3DExtras',
    'PyQt6.Qt3DInput', 'PyQt6.Qt3DLogic', 'PyQt6.Qt3DRender',
    'PyQt6.QtBluetooth', 'PyQt6.QtCharts', 'PyQt6.QtDataVisualization',
    'PyQt6.QtDBus', 'PyQt6.QtDesigner', 'PyQt6.QtHelp',
    'PyQt6.QtLocation', 'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets',
    'PyQt6.QtNfc', 'PyQt6.QtOpenGL', 'PyQt6.QtOpenGLWidgets',
    'PyQt6.QtPdf', 'PyQt6.QtPdfWidgets', 'PyQt6.QtPositioning',
    'PyQt6.QtPrintSupport', 'PyQt6.QtQml', 'PyQt6.QtQuick',
    'PyQt6.QtQuickWidgets', 'PyQt6.QtRemoteObjects', 'PyQt6.QtSensors',
    'PyQt6.QtSerialBus', 'PyQt6.QtSerialPort', 'PyQt6.QtSql',
    'PyQt6.QtSvg', 'PyQt6.QtSvgWidgets', 'PyQt6.QtTest',
    'PyQt6.QtTextToSpeech', 'PyQt6.QtWebChannel', 'PyQt6.QtWebEngineCore',
    'PyQt6.QtWebEngineQuick', 'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebSockets', 'PyQt6.QtXml',
]

_STDLIB_EXCLUDE = [
    'tkinter', '_tkinter', 'turtle', 'idlelib',
    'unittest', 'doctest', 'pdb', 'profile', 'pstats', 'timeit', 'trace',
    'lib2to3', 'distutils', 'ensurepip', 'venv',
    'xml.etree', 'xmlrpc', 'html', 'http.server',
    'mailbox', 'mimetypes', 'multiprocessing',
    'curses', 'readline', 'rlcompleter',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/default_config.json', 'config'),
        ('resources/styles/main.qss', 'resources/styles'),
        ('resources/icons/icon.ico', 'resources/icons'),
    ],
    hiddenimports=[
        'keyboard', 'mss', 'mss.windows',
        'PIL', 'PIL.Image', 'PIL.PngImagePlugin', 'PIL.JpegImagePlugin',
        'win32gui', 'win32clipboard', 'win32con', 'win32api',
        'pywintypes',
        'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=_QT_EXCLUDE + _STDLIB_EXCLUDE,
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
    upx_exclude=['Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/icon.ico',
)
