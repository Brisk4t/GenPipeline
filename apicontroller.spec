# -*- mode: python ; coding: utf-8 -*-

added_files = [
         ( 'frontend/build/static/css', 'frontend/build/static/css' ),
         ( 'frontend/build/static/js', 'frontend/build/static/js' ),
         ( 'frontend/build/static/media', 'frontend/build/static/media' ),
         ( 'frontend/build/*.json', 'frontend/build/build' ),
         ( 'frontend/build/*.html', 'frontend/build/build' ),
         ( 'frontend/build/*.txt', 'frontend/build/build' ),
         ( 'frontend/build/*.ico', 'frontend/build/build' ),
         ( 'frontend/build/*.png', 'frontend/build/build' ),
         ( 'backend/*.yaml', '.' ),

         ]

a = Analysis(
    ['backend/apicontroller.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
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
    [],
    exclude_binaries=True,
    name='apicontroller',
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='apicontroller',
)
