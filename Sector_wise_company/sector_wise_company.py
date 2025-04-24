import os
import sys
import requests
import concurrent.futures

from datetime import datetime
from bs4 import BeautifulSoup

# Import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from BaseScraperApp import BaseScraperApp
from BaseScraperEngine import BaseScraperEngine
# Module name for logging
MODULE_NAME = "sector_wise_company_scraper"

class ShareScraper:
    """Handles scraping company share data"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def scrape_sector_company_data(self, industryno):
        """Scrape data for a single company and return the parsed data"""
        try:
            url = f"https://www.dsebd.org/companylistbyindustry.php?industryno={industryno}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch data for {industryno}: HTTP {response.status_code}")
                return None
                    
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find all company links
            industry_links = soup.select('a.ab1')
            
            companies_list = []
            
            # Extract company data from each link
            for link in industry_links:
                href = link.get('href', '')
                
                # Extract the company name from the href attribute
                company = None
                if 'name=' in href:
                    company = href.split('name=')[1].split('&')[0]
                
                # Get the company name from the link text
                company_name = link.text.strip()
                
                if company and company_name:
                    company_data = {
                        "sector_code": industryno,
                        "company": company,
                        "last_updated": datetime.now()
                    }
                    companies_list.append(company_data)
            
            return companies_list

        except Exception as e:
            self.logger.error(f"Error scraping data for {industryno}: {str(e)}")
            return None



class SectorCompanyScraperEngine(BaseScraperEngine):
    """Scraper engine for sector code data"""
    
    def _execute_scraping(self):
        """Scrape and store data for all sectors"""
        self.logger.info("Starting sector code scraping process")
        
        try:
            # Fetch sector list
            sectors = self.db_manager.fetch_sector_code_list()
            if not sectors:
                self.logger.error("No sectors found to scrape")
                self.finish_scraping()
                return
            
            total_sectors = len(sectors)
            self.logger.info(f"Found {total_sectors} sectors to scrape")
            
            sector_wise_company = []
            completed = 0
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit scraping tasks
                future_to_company = {
                    executor.submit(self.scraper.scrape_sector_company_data, sector_code): sector_code 
                    for sector_code in sectors
                }
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_company):
                    companies = future.result()
                    if companies:
                        for company in companies:
                            # Convert each dictionary to a tuple in the correct order
                            company_tuple = (company["sector_code"], company["company"], company["last_updated"])
                            sector_wise_company.append(company_tuple)
                    
                    completed += 1
                    if self.progress_callback:
                        self.progress_callback(completed, total_sectors)
            
            # Store the scraped data
            insert_query = """
                INSERT INTO Sector_Symbol 
                (sector_code, company, last_updated)
                VALUES (?, ?, ?)
            """
            self.db_manager.store_data(sector_wise_company, insert_query,table_name="Sector_Symbol")
            
            self.logger.info("Scraping process completed successfully")
        except Exception as e:
            self.logger.error(f"Error in scraping process: {str(e)}")


class ScraperApp(BaseScraperApp):
    """Main application class with the UI"""
    def __init__(self, parent):
        # Call the parent constructor
        super().__init__(parent, title="Sector wise Company Scraper Module",module_name=MODULE_NAME)
        
        # Set up the scraper components
        self.setup_scraper()
        
        # Complete initialization
        self.complete_initialization()
        
    def setup_scraper(self):
        """Set up specific scraper components"""
        self.scraper = ShareScraper(self.logger)
        self.scraper_engine = SectorCompanyScraperEngine(self.logger, self.db_manager, self.scraper)
        
    def create_scraper(self):
        """Create and return the scraper instance"""
        return ShareScraper(self.logger)


# Create an initialization file for the module
if not os.path.exists('__init__.py'):
    with open('__init__.py', 'w') as f:
        f.write('# Make this directory a Python package\n')