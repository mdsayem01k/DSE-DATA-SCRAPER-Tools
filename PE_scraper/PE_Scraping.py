import requests
from bs4 import BeautifulSoup
import pandas as pd
import pyodbc
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, scrolledtext
import schedule
import time
import threading
import queue
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("scraper.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class DseScraper:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.url = os.getenv('DSE_URL', 'https://www.dsebd.org/latest_PE.php')
        self.server = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USERNAME')
        self.password = os.getenv('DB_PASSWORD')
        
        # Read fetch times from environment variable
        self.fetch_time_1 = os.getenv('FETCH_TIME_1', '12:27')
        self.fetch_time_2 = os.getenv('FETCH_TIME_2', '18:26')
        
        # Connection string - create once
        self.connection_string = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={self.username};'
            f'PWD={self.password}'
        )
        
        # Initialize the message queue
        self.message_queue = queue.Queue()

    def safe_float(self, value):
        """Convert string to float safely, handling empty values and formatting."""
        if not value or value.lower() in ['n/a', '']:
            return None
            
        try:
            return float(value.replace(',', '').replace(' ', ''))
        except (ValueError, TypeError):
            return None

    def get_db_connection(self):
        """Establish and return a database connection."""
        try:
            return pyodbc.connect(self.connection_string)
        except pyodbc.Error as e:
            logger.error(f"Database connection error: {e}")
            self.message_queue.put(f"Database connection error: {e}\n")
            raise

    def create_table_if_not_exists(self, cursor):
        """Create the database table if it doesn't exist."""
        create_table_query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='pe_data' AND xtype='U')
        CREATE TABLE pe_data (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            SL INT,
            Trade_Price VARCHAR(255),
            Close_Price FLOAT,
            YCP FLOAT,
            PE_1_Basic FLOAT,
            PE_2_Diluted FLOAT,
            PE_3_Basic FLOAT,
            PE_4_Diluted FLOAT,
            PE_5 FLOAT,
            PE_6 FLOAT,
            DateTime DATETIME  
        )
        """
        cursor.execute(create_table_query)
        cursor.commit()

    def save_to_sql(self, df):
        """Save DataFrame to SQL Server with batch processing."""
        try:
            self.message_queue.put("Saving data to SQL Server...\n")
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                self.create_table_if_not_exists(cursor)
                
                # Prepare batch insert
                insert_query = """
                INSERT INTO pe_data (SL, Trade_Price, Close_Price, YCP, PE_1_Basic, PE_2_Diluted, 
                                    PE_3_Basic, PE_4_Diluted, PE_5, PE_6, DateTime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                # Process in batches for better performance
                current_datetime = datetime.now()
                batch_size = 100
                rows_to_insert = []
                
                for _, row in df.iterrows():
                    rows_to_insert.append((
                        row['SL'], 
                        row['Trade_Price'],
                        self.safe_float(row['Close_Price']),
                        self.safe_float(row['YCP']), 
                        self.safe_float(row['PE_1_Basic']),
                        self.safe_float(row['PE_2_Diluted']), 
                        self.safe_float(row['PE_3_Basic']),
                        self.safe_float(row['PE_4_Diluted']), 
                        self.safe_float(row['PE_5']),
                        self.safe_float(row['PE_6']), 
                        current_datetime
                    ))
                    
                    # Execute in batches
                    if len(rows_to_insert) >= batch_size:
                        cursor.executemany(insert_query, rows_to_insert)
                        rows_to_insert = []
                
                # Insert any remaining rows
                if rows_to_insert:
                    cursor.executemany(insert_query, rows_to_insert)
                
                conn.commit()
                
            self.message_queue.put(f"Successfully saved {len(df)} records to database.\n")
            logger.info(f"Successfully saved {len(df)} records to database.")
            return True
            
        except Exception as e:
            error_msg = f"Database error: {e}"
            self.message_queue.put(f"{error_msg}\n")
            logger.error(error_msg)
            return False

    def scrape_data(self):
        """Scrape data from the DSE website."""
        try:
            self.message_queue.put(f"Fetching data from {self.url}...\n")
            
            # Set timeout to prevent hanging
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            self.message_queue.put("Data extracted from DSE site successfully.\n")
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
            
            self.message_queue.put(f"Successfully scraped {len(df)} rows of data.\n")
            return df
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {e}"
            self.message_queue.put(f"{error_msg}\n")
            logger.error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Scraping error: {e}"
            self.message_queue.put(f"{error_msg}\n")
            logger.error(error_msg)
            return None

    def scrape_and_save(self):
        """Scrape data and save to database."""
        try:
            self.message_queue.put(f"Starting data collection at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...\n")
            
            # Scrape data
            df = self.scrape_data()
            if df is None or df.empty:
                self.message_queue.put("No data retrieved. Aborting.\n")
                return False
                
            # Save to database
            success = self.save_to_sql(df)
            
            if success:
                self.message_queue.put("Data processing completed successfully.\n")
                return True
            else:
                self.message_queue.put("Failed to save data to database.\n")
                return False
                
        except Exception as e:
            error_msg = f"Error in scrape_and_save: {e}"
            self.message_queue.put(f"{error_msg}\n")
            logger.error(error_msg)
            return False

class ScraperGUI:
    def __init__(self, scraper):
        self.scraper = scraper
        self.root = tk.Tk()
        self.root.title("DSE Data Scraper")
        self.root.geometry("800x600")
        
        # Set up the schedule jobs
        self.scheduled_jobs = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the GUI components."""
        # Frame for top controls
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Status label
        status_frame = tk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10)
        
        self.status_label = tk.Label(status_frame, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X)
        
        # Next fetch time label
        self.next_fetch_label = tk.Label(status_frame, text="Next fetch time: --:--")
        self.next_fetch_label.pack(fill=tk.X, pady=5)
        
        # Text widget with scrollbar for logs
        log_frame = tk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Use ScrolledText for better log display
        self.text_widget = scrolledtext.ScrolledText(log_frame, height=20, width=80)
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Manual scrape button
        self.manual_scrape_button = tk.Button(
            control_frame, 
            text="Scrape Now", 
            command=self.manual_scrape,
            bg="#4CAF50",
            fg="white",
            padx=10
        )
        self.manual_scrape_button.pack(side=tk.LEFT, padx=5)
        
        # Clear logs button
        self.clear_logs_button = tk.Button(
            control_frame, 
            text="Clear Logs", 
            command=self.clear_logs,
            bg="#f44336",
            fg="white",
            padx=10
        )
        self.clear_logs_button.pack(side=tk.LEFT, padx=5)
        
        # Exit button
        self.exit_button = tk.Button(
            control_frame, 
            text="Exit", 
            command=self.close_application,
            bg="#607D8B",
            fg="white",
            padx=10
        )
        self.exit_button.pack(side=tk.RIGHT, padx=5)

    def update_gui(self):
        """Update the GUI with messages from the queue."""
        try:
            while not self.scraper.message_queue.empty():
                message = self.scraper.message_queue.get_nowait()
                self.text_widget.insert(tk.END, message)
                self.text_widget.see(tk.END)  # Auto-scroll to the end
                
            self.root.after(100, self.update_gui)  # Check queue every 100ms
        except Exception as e:
            logger.error(f"Error updating GUI: {e}")
            
    def update_next_fetch_time(self):
        """Calculate and display the next scheduled fetch time."""
        now = datetime.now()
        
        # Convert fetch times from strings to datetime objects for today
        fetch_time_1_obj = datetime.strptime(self.scraper.fetch_time_1, '%H:%M').replace(
            year=now.year, month=now.month, day=now.day)
        fetch_time_2_obj = datetime.strptime(self.scraper.fetch_time_2, '%H:%M').replace(
            year=now.year, month=now.month, day=now.day)
        
        # Determine the next fetch time
        if now < fetch_time_1_obj:
            next_run = fetch_time_1_obj
        elif now < fetch_time_2_obj:
            next_run = fetch_time_2_obj
        else:
            # Next day's first fetch
            next_run = fetch_time_1_obj + timedelta(days=1)
        
        # Update the label
        self.next_fetch_label.config(text=f"Next fetch time: {next_run.strftime('%H:%M')}")
        
    def setup_schedule(self):
        """Set up the scheduled jobs."""
        # Clear any existing jobs
        schedule.clear()
        
        # Schedule the two daily jobs
        job1 = schedule.every().day.at(self.scraper.fetch_time_1).do(self.scheduled_scrape)
        job2 = schedule.every().day.at(self.scraper.fetch_time_2).do(self.scheduled_scrape)
        
        self.scheduled_jobs = [job1, job2]
        self.update_next_fetch_time()
        
        self.scraper.message_queue.put(f"Scheduled fetches at {self.scraper.fetch_time_1} and {self.scraper.fetch_time_2}.\n")
        
    def scheduled_scrape(self):
        """Run scraper as scheduled task."""
        try:
            self.status_label.config(text="Running scheduled scrape...")
            success = self.scraper.scrape_and_save()
            
            if success:
                # Show notification
                self.show_notification("Scheduled Scrape", "Data has been saved successfully!")
                
            self.status_label.config(text="Ready")
            self.update_next_fetch_time()
            return success
        except Exception as e:
            logger.error(f"Error in scheduled scrape: {e}")
            self.status_label.config(text="Error occurred")
            return False
            
    def manual_scrape(self):
        """Manually trigger the scraping process."""
        try:
            self.status_label.config(text="Running manual scrape...")
            self.manual_scrape_button.config(state=tk.DISABLED)
            
            success = self.scraper.scrape_and_save()
            
            if success:
                self.show_notification("Manual Scrape", "Data has been saved successfully!")
                
            self.status_label.config(text="Ready")
            self.manual_scrape_button.config(state=tk.NORMAL)
            return success
        except Exception as e:
            logger.error(f"Error in manual scrape: {e}")
            self.status_label.config(text="Error occurred")
            self.manual_scrape_button.config(state=tk.NORMAL)
            return False
            
    def show_notification(self, title, message):
        """Add notification message to the log instead of showing a popup."""
        notification_text = f"[{title}] {message}\n"
        self.scraper.message_queue.put(notification_text)
        logger.info(notification_text.strip())
    def clear_logs(self):
        """Clear the log text widget."""
        self.text_widget.delete(1.0, tk.END)
        
    def close_application(self):
        """Clean up and close the application."""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            logger.info("Application closing")
            schedule.clear()
            self.root.destroy()
        
    def run_scheduler(self):
        """Run the scheduler in a separate thread."""
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(5)  # Wait before retrying
                
    def start(self):
        """Start the application."""
        # Setup scheduled jobs
        self.setup_schedule()
        
        # Start the scheduler in a background thread
        threading.Thread(target=self.run_scheduler, daemon=True).start()
        
        # Start GUI update loop
        self.update_gui()
        
        # Welcome message
        self.scraper.message_queue.put("DSE Data Scraper started.\n")
        self.scraper.message_queue.put(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run the main loop
        self.root.mainloop()

def main():
    """Main entry point for the application."""
    try:
        # Initialize scraper
        scraper = DseScraper()
        
        # Initialize and start GUI
        gui = ScraperGUI(scraper)
        gui.start()
    except Exception as e:
        logger.critical(f"Critical error starting application: {e}")
        messagebox.showerror("Critical Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    main()