# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('PE_scraper', 'PE_scraper'),
        ('sector_scraper', 'sector_scraper'),
        ('Sector_wise_company', 'Sector_wise_company'),
        ('share_ratio_scraper', 'share_ratio_scraper'),
        ('company_scraper', 'company_scraper'),
        ('config', 'config'),
        ('handler', 'handler'),
        ('log', 'log'),
        ('scheduler', 'scheduler'),
    ],
    hiddenimports=[
        'PE_scraper',
        'sector_scraper',
        'Sector_wise_company',
        'share_ratio_scraper',
        'company_scraper',
        'config',
        'handler',
        'log',
        'scheduler',
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
    name='DSE_Data_Scraper',
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