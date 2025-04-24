# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include all module directories with their contents
        ('PE_scraper', 'PE_scraper'),
        ('sector_scraper', 'sector_scraper'),
        ('sector_wise_company', 'sector_wise_company'),
        ('share_ratio_scraper', 'share_ratio_scraper'),
        ('company_scraper', 'company_scraper'),
        ('config', 'config'),
        ('handler', 'handler'),
        ('log', 'log'),
        ('scheduler', 'scheduler'),
        # Include any other directories that might be needed
    ],
    hiddenimports=[
        # Explicitly include modules that are dynamically imported
        'PE_scraper',
        'PE_scraper.PE_scraper',
        'sector_scraper',
        'sector_scraper.sector_scraper',
        'sector_wise_company',
        'sector_wise_company.sector_wise_company',
        'share_ratio_scraper',
        'share_ratio_scraper.share_ratio_scraper',
        'company_scraper',
        'company_scraper.company_scraper',
        'importlib',
        'importlib.util',
        'tkinter',
        'tkinter.ttk',
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
    console=True,  # Change to False if you don't want a console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an icon file path here if you have one
)