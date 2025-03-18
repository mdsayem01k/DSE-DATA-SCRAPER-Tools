from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all submodules for each package
hiddenimports = []
for pkg in ['PE_scraper', 'sector_scraper', 'sector_wise_company', 'share_ratio_scraper']:
    hiddenimports.extend(collect_submodules(pkg))

# Collect all data files
datas = []
for pkg in ['PE_scraper', 'sector_scraper', 'sector_wise_company', 'share_ratio_scraper', 'config', 'handler', 'log', 'scheduler']:
    datas.extend(collect_data_files(pkg, include_py_files=True))