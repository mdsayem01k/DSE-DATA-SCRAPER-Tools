import os
import sys
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from BaseScraperApp import BaseScraperApp
from BaseScraperEngine import BaseScraperEngine
from log.scraper_log import LoggerSetup

# Module name for logging
MODULE_NAME = "sector_scraper"


class ShareScraper:
    """Handles scraping company share data"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def scrape_sector_data(self):
        """Scrape data for a single company and return the parsed data"""
        try:
            url = f"https://www.dsebd.org/by_industrylisting.php"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)        
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all industry links
            industry_links = soup.select('a.ab1')
            
            sectors = []
            
            # Extract industry number and name from each link
            for link in industry_links:
                href = link.get('href', '')
                
                # Extract the industry number from the href attribute
                sector_code = None
                if 'industryno=' in href:
                    sector_code = href.split('industryno=')[1].split('&')[0]
                
                # Get the industry name from the link text
                sector_name = link.text.strip()
                
                if sector_code and sector_name:
                    sectors.append({
                        'sector_code': sector_code,
                        'sector_name': sector_name,
                        'isActive': 1,  # Default to active
                        'last_updated': datetime.now()
                    })
            
            success_message = f"Successfully scraped {len(sectors)} sectors"
            self.logger.info(success_message)
            return sectors
        except Exception as e:
            self.logger.error(f"Error scraping data: {str(e)}")
            return None


class SectorCodeScraperEngine(BaseScraperEngine):  
    """Manages the core scraping process"""   

    def _execute_scraping(self):
        """Main function to scrape and store data for all sectors"""
        self.logger.info("Starting sector scraping process")
        
        try:
            # Fetch sector list
            sectors = self.scraper.scrape_sector_data()
            
            if sectors is None or len(sectors) == 0:
                self.logger.warning("No sectors found to scrape")
                return
                
            # Format data for database insertion
            sector_data = [
                (sector.get("sector_code"), sector.get("sector_name"), sector.get("isActive"), sector.get("last_updated"))
                for sector in sectors
            ]
            
            # Update progress if callback is set
            self.update_progress(len(sectors), len(sectors))
                
            # Store the scraped data
            insert_query = """
                INSERT INTO Sector_Information (sector_code, sector_name, isActive, last_updated) 
                VALUES (?, ?, ?, ?)
            """
            self.db_manager.store_data(sector_data, insert_query)
            
            self.logger.info(f"Scraping process completed successfully. Stored {len(sector_data)} sectors.")
        except Exception as e:
            self.logger.error(f"Error in scraping process: {str(e)}")


class ScraperApp(BaseScraperApp):
    """Main application class with the UI"""
    def __init__(self, parent):
        # Call the parent constructor with module-specific name
        super().__init__(parent, title="Sector Scraper Module", module_name=MODULE_NAME)
        
        # Set up the scraper components
        self.setup_scraper()
        
        # Complete initialization
        self.complete_initialization()
        
    def setup_scraper(self):
        """Set up specific scraper components"""
        self.scraper = ShareScraper(self.logger)
        self.scraper_engine = SectorCodeScraperEngine(self.logger, self.db_manager, self.scraper)
        
    def create_scraper(self):
        """Create and return the scraper instance"""
        return ShareScraper(self.logger)