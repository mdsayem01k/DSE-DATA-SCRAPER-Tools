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
MODULE_NAME = "company_scraper"


class CompanyScraper:
    """Handles scraping company list data"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def scrape_company_data(self):
        """Scrape company list data and return the parsed data"""
        try:
            url = "https://www.dsebd.org/company_listing.php"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)        
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all company links - they have class "ab1"
            company_links = soup.select('a.ab1')
            
            companies = []
            
            # Extract company symbols from each link
            for link in company_links:
                href = link.get('href', '')
                
                # Extract the company symbol from the href attribute
                company_symbol = None
                if 'name=' in href:
                    company_symbol = href.split('name=')[1].split('&')[0] if '&' in href else href.split('name=')[1]
                
                # Get the company symbol from the link text as a backup
                company_name = link.text.strip()
                
                if company_symbol and company_name:
                    companies.append({
                        'company_symbol': company_symbol,
                        'company_name': company_name,
                        'isActive': 1,  # Default to active
                        'last_updated': datetime.now()
                    })
            
            success_message = f"Successfully scraped {len(companies)} companies"
            self.logger.info(success_message)
            return companies
        except Exception as e:
            self.logger.error(f"Error scraping company data: {str(e)}")
            return None


class CompanyScraperEngine(BaseScraperEngine):  
    """Manages the core scraping process for companies"""   

    def _execute_scraping(self):
        """Main function to scrape and store data for all companies"""
        self.logger.info("Starting company scraping process")
        
        try:
            # Fetch company list
            companies = self.scraper.scrape_company_data()
            
            if companies is None or len(companies) == 0:
                self.logger.warning("No companies found to scrape")
                return
                
            # Format data for database insertion
            company_data = [
                (company.get("company_symbol"), company.get("company_name"), company.get("isActive"), company.get("last_updated"))
                for company in companies
            ]
            
            # Update progress if callback is set
            self.update_progress(len(companies), len(companies))
                
            # Store the scraped data
            insert_query = """
                INSERT INTO Company_Information (company_symbol, company_name, isActive, last_updated) 
                VALUES (?, ?, ?, ?)
            """
            self.db_manager.store_data(company_data, insert_query,table_name="Company_Information")
            
            self.logger.info(f"Company scraping process completed successfully. Stored {len(company_data)} companies.")
        except Exception as e:
            self.logger.error(f"Error in company scraping process: {str(e)}")


class ScraperApp(BaseScraperApp):
    """Main application class with the UI for company scraping"""
    def __init__(self, parent):
        # Call the parent constructor with module-specific name
        super().__init__(parent, title="Company Scraper Module", module_name=MODULE_NAME)
        
        # Set up the scraper components
        self.setup_scraper()
        
        # Complete initialization
        self.complete_initialization()
        
    def setup_scraper(self):
        """Set up specific scraper components"""
        self.scraper = CompanyScraper(self.logger)
        self.scraper_engine = CompanyScraperEngine(self.logger, self.db_manager, self.scraper)
        
    def create_scraper(self):
        """Create and return the scraper instance"""
        return CompanyScraper(self.logger)


# Example usage when running the script directly
if __name__ == "__main__":
    # Set up a simple logger for standalone use
    logger = LoggerSetup.get_logger(MODULE_NAME)
    
    # Create the scraper
    scraper = CompanyScraper(logger)
    
    # Scrape company data
    companies = scraper.scrape_company_data()
    
    if companies:
        print(f"Scraped {len(companies)} companies:")
        for company in companies[:5]:  # Print just the first 5 for demonstration
            print(f"Symbol: {company['company_symbol']}, Name: {company['company_name']}")
        print("...")
    else:
        print("Failed to scrape company data.")