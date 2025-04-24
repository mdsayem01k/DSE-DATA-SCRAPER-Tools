
# It also provides a convenient way to import from the module

from .company_scraper import CompanyScraper, CompanyScraperEngine, ScraperApp

# Define what gets imported when using "from sector_scraper import *"
__all__ = ['CompanyScraper', 'CompanyScraperEngine', 'ScraperApp']