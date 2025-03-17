import os
import sys
import requests
import concurrent.futures
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from bs4 import BeautifulSoup


from log.scraper_log import LoggerSetup
from scheduler.sheduler import ScraperScheduler
from config.dbConfig import DatabaseManager
from config.envConfig import EnvConfig
from config.dbEdit import ConfigEditorWindow

# Import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from BaseScraperApp import BaseScraperApp
from BaseScraperEngine import BaseScraperEngine

# Module name for logging
MODULE_NAME = "share_ratio_scraper"

class ShareScraper:
    """Handles scraping company share data"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def scrape_company_data(self, company):
        """Scrape data for a single company and return the parsed data"""
        try:
            url = f"https://www.dsebd.org/displayCompany.php?name={company}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch data for {company}: HTTP {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract shareholding details
            share_data = {
                "Sponsor/Director": 0,
                "Govt": 0,
                "Institute": 0,
                "Foreign_share": 0,
                "Public": 0
            }
            
            td_elements = soup.find_all('td', style="border:hidden;")
            
            for td in td_elements:
                text = td.text.strip()
                for key in share_data.keys():
                    if f"{key}:" in text:
                        value_text = text.split("\n")[-1].strip().replace("%", "")
                        try:
                            share_data[key] = float(value_text) if value_text else 0
                        except ValueError:
                            share_data[key] = 0
            
            # Extract total number of outstanding securities
            total_share = 0
            th_elements = soup.find_all('th')
            
            for th in th_elements:
                if "Total No. of Outstanding Securities" in th.text:
                    td = th.find_next_sibling("td")
                    if td:
                        total_share_text = td.text.strip().replace(",", "")
                        try:
                            total_share = int(total_share_text) if total_share_text.isdigit() else 0
                        except ValueError:
                            total_share = 0
            
            # Return data as a tuple
            return (
                company,
                total_share,
                share_data["Sponsor/Director"],
                share_data["Govt"],
                share_data["Institute"],
                share_data["Foreign_share"],
                share_data["Public"],
                datetime.now()
            )
        except Exception as e:
            self.logger.error(f"Error scraping data for {company}: {str(e)}")
            return None



class ShareRatioScraperEngine(BaseScraperEngine):
    """Manages the core scraping process"""
    
    def _execute_scraping(self):
        """Main function to scrape and store data for all companies"""
        self.logger.info("Starting scraping process")
        
        try:
            # Fetch company list
            companies = self.db_manager.fetch_company_list()
            if not companies:
                self.logger.error("No companies found to scrape")
                self.finish_scraping()
                return
            
            total_companies = len(companies)
            self.logger.info(f"Found {total_companies} companies to scrape")
            
            # Use ThreadPoolExecutor for parallel processing
            company_shares = []
            completed = 0
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit scraping tasks
                future_to_company = {
                    executor.submit(self.scraper.scrape_company_data, company): company 
                    for company in companies
                }
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_company):
                    result = future.result()
                    if result:
                        company_shares.append(result)
                    
                    completed += 1
                    if self.progress_callback:
                        self.progress_callback(completed, total_companies)
            
            # Store the scraped data
            insert_query = """
                INSERT INTO Symbol_Share 
                (company, total_share, Sponsor, Govt, Institute, Foreign_share, public_share, scraping_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db_manager.store_data(company_shares,insert_query)
            
            self.logger.info("Scraping process completed successfully")
        except Exception as e:
            self.logger.error(f"Error in scraping process: {str(e)}")

   

class ScraperApp(BaseScraperApp):
    """Main application class with the UI"""
    
    def __init__(self, parent):
        # Call the parent constructor
        super().__init__(parent, title="Share Ratio Scraper Module",module_name=MODULE_NAME)
        
        # Set up the scraper components
        self.setup_scraper()
        
        # Complete initialization
        self.complete_initialization()
        
    def setup_scraper(self):
        """Set up specific scraper components"""
        self.scraper = ShareScraper(self.logger)
        self.scraper_engine = ShareRatioScraperEngine(self.logger, self.db_manager, self.scraper)
        
    def create_scraper(self):
        """Create and return the scraper instance"""
        return ShareScraper(self.logger)


# Create an initialization file for the module
if not os.path.exists('__init__.py'):
    with open('__init__.py', 'w') as f:
        f.write('# Make this directory a Python package\n')