import os
import sys
import requests

from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

from BaseScraperApp import BaseScraperApp


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from BaseScraperApp import BaseScraperApp
from BaseScraperEngine import BaseScraperEngine
# Module name for logging
MODULE_NAME = "pe_scraper"
class ShareScraper:
    """Handles scraping company share data"""
    
    def __init__(self, logger):
        self.logger = logger
        
    
    def scrape_data(self):
        """Scrape data from the DSE website."""
        try:
            url = f"https://www.dsebd.org/latest_PE.php"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch data for PE Ratio: HTTP {response.status_code}")
                return None           

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Use more specific selector for better reliability
            table = soup.find('table', class_='table table-bordered background-white shares-table fixedHeader')
            
            if not table:
                raise ValueError("Required table not found on the page")
                
            # Extract headers - more robust approach
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [th.text.strip() for th in header_row.find_all('th')]
            
            if not headers:
                raise ValueError("Table headers not found")
                
            # Extract data rows
            data_rows = []
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = [td.text.strip() for td in row.find_all('td')]
                if len(cells) == len(headers):  # Ensure row has correct number of cells
                    data_rows.append(cells)
            
            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=headers)
            
            # Rename columns - use dictionary comprehension for cleaner code
            column_mapping = {
                '#': 'SL',
                'Trade Code': 'Trade_Price',
                'Close Price': 'Close_Price',
                'YCP': 'YCP',
                'P/E 1*(Basic)': 'PE_1_Basic',
                'P/E 2*(Diluted)': 'PE_2_Diluted',
                'P/E 3*(Basic)': 'PE_3_Basic',
                'P/E 4*(Diluted)': 'PE_4_Diluted',
                'P/E 5*': 'PE_5',
                'P/E 6*': 'PE_6'
            }
            
            df.rename(columns=column_mapping, inplace=True)
            
            self.logger.info(f"Successfully scraped {len(df)} rows of data.\n")
            return df
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {e}"
            self.logger.error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Scraping error: {e}"
            self.logger.error(error_msg)
            return None


class PEScraperEngine(BaseScraperEngine):  
    """Manages the core scraping process"""
    

    
    def _execute_scraping(self):
        """Main function to scrape and store data for all sectors"""
        self.logger.info("Starting scraping process")
        try:
            # Get data from scraper
            df = self.scraper.scrape_data()
            
            if df is None or df.empty:
                self.logger.warning("No data scraped")
                return

            # Update progress if callback is set
            if self.progress_callback:
                self.progress_callback(1, 1)  # Simple progress update

            insert_query = """
                INSERT INTO pe_data (SL, Trade_Price, Close_Price, YCP, PE_1_Basic, PE_2_Diluted, 
                                    PE_3_Basic, PE_4_Diluted, PE_5, PE_6, DateTime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Process in batches for better performance
            current_datetime = datetime.now()
            rows_to_insert = []

            try:
                for _, row in df.iterrows():
                    try:
                        rows_to_insert.append((
                            row['SL'],
                            row['Trade_Price'],
                            self.safe_float(row.get('Close_Price', 0)),
                            self.safe_float(row.get('YCP', 0)),
                            self.safe_float(row.get('PE_1_Basic', 0)),
                            self.safe_float(row.get('PE_2_Diluted', 0)),
                            self.safe_float(row.get('PE_3_Basic', 0)),
                            self.safe_float(row.get('PE_4_Diluted', 0)),
                            self.safe_float(row.get('PE_5', 0)),
                            self.safe_float(row.get('PE_6', 0)),
                            current_datetime
                        ))
                    except Exception as row_error:
                        self.logger.error(f"Error processing row {row.to_dict()}: {row_error}")

                # Store data only if there are valid rows
                if rows_to_insert:
                    self.db_manager.store_data(rows_to_insert, insert_query)
                    self.logger.info(f"Scraping process completed successfully. Stored {len(rows_to_insert)} rows of data.")
                else:
                    self.logger.warning("No valid data to store.")
            
            except Exception as batch_error:
                self.logger.error(f"Error processing batch data: {batch_error}")

        except Exception as e:
            self.logger.error(f"Error in scraping process: {str(e)}")


    
class ScraperApp(BaseScraperApp):
    """Main application class with the UI"""
    def __init__(self, parent):
        # Call the parent constructor but don't initialize UI yet
        super().__init__(parent, title="PE Ratio Scraper Module",module_name=MODULE_NAME)
        
        # Now set up the scraper components
        self.setup_scraper()
        
        # Complete initialization (which will call initialize_ui)
        self.complete_initialization()
        
    def setup_scraper(self):
        """Set up specific scraper components"""
        self.scraper = ShareScraper(self.logger)
        self.scraper_engine = PEScraperEngine(self.logger, self.db_manager, self.scraper)
        
    def create_scraper(self):
        """Create and return the scraper instance"""
        return ShareScraper(self.logger)