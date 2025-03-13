import os
import sys
import requests
import concurrent.futures
import logging
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import pyodbc
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import schedule

# Get application path for executable support
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle
    application_path = os.path.dirname(sys.executable)
else:
    # If run as a normal Python script
    application_path = os.path.dirname(os.path.abspath(__file__))

# Set the working directory to the application path
os.chdir(application_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.join(application_path, 'scraper.log')
)
logger = logging.getLogger(__name__)

def ensure_env_file_exists():
    """Create a sample .env file if it doesn't exist"""
    env_path = os.path.join(application_path, '.env')
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write("""# Database Configuration
DB_SERVER=your_server_name
DB_NAME=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
""")
        logger.info("Created sample .env file. Please edit with your database details.")
        return False
    return True

# Create .env file if it doesn't exist
env_exists = ensure_env_file_exists()

# Load environment variables
load_dotenv(os.path.join(application_path, '.env'))

class CustomHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        
    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        self.text_widget.after(0, append)

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Company Share Holding  Data Scrapper")
        self.root.geometry("800x600")
    
        self.create_widgets()
        self.scraping_in_progress = False
        self.scheduler_active = False
        self.start_time = None
        self.elapsed_time_var = tk.StringVar(value="Elapsed Time: 0:00:00")
        
        # Create a custom logger for the GUI
        self.setup_logger()
        
        # Initialize scheduler
        self.schedule_thread = None
        
        # Check if environment variables are set
        if not env_exists:
            messagebox.showinfo("Configuration Needed", 
                "A sample .env file has been created. Please edit it with your database details before using the application.")

    def setup_logger(self):
        # Create a handler for the text widget
        text_handler = CustomHandler(self.log_text)
        text_handler.setLevel(logging.INFO)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Add the handler to the logger
        logger.addHandler(text_handler)

    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 12))
        status_label.pack(side=tk.LEFT, padx=5)
        
        self.elapsed_time_var = tk.StringVar(value="Elapsed Time: 0:00:00")
        time_label = ttk.Label(status_frame, textvariable=self.elapsed_time_var, font=("Arial", 12))
        time_label.pack(side=tk.RIGHT, padx=5)
        
        # Control section
        control_frame = ttk.Frame(main_frame, padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        self.fetch_button = ttk.Button(control_frame, text="Manual Fetch", command=self.start_manual_fetch)
        self.fetch_button.pack(side=tk.LEFT, padx=5)
        
        self.schedule_button = ttk.Button(control_frame, text="Start Scheduler", command=self.toggle_scheduler)
        self.schedule_button.pack(side=tk.LEFT, padx=5)
        
        # Schedule time entry
        time_frame = ttk.Frame(control_frame)
        time_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(time_frame, text="Schedule Time (HH:MM):").pack(side=tk.LEFT)
        self.schedule_time = ttk.Entry(time_frame, width=10)
        self.schedule_time.pack(side=tk.LEFT, padx=5)
        self.schedule_time.insert(0, "15:00")
        
        # DB Config button
        self.config_button = ttk.Button(control_frame, text="Edit DB Config", command=self.edit_config)
        self.config_button.pack(side=tk.RIGHT, padx=5)
        
        # Progress section
        progress_frame = ttk.Frame(main_frame, padding="10")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X)
        
        self.progress_text = tk.StringVar(value="0/0 companies processed")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_text)
        progress_label.pack(pady=5)
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def edit_config(self):
        """Open the .env file in a simple editor"""
        env_path = os.path.join(application_path, '.env')
        
        # Create a new window
        config_window = tk.Toplevel(self.root)
        config_window.title("Database Configuration")
        config_window.geometry("500x300")
        config_window.grab_set()  # Make it modal
        
        # Read current config
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                config_content = f.read()
        else:
            config_content = """# Database Configuration
DB_SERVER=your_server_name
DB_NAME=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password"""
        
        # Create editor
        ttk.Label(config_window, text="Edit your database configuration:").pack(pady=5)
        
        editor = tk.Text(config_window, height=10)
        editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        editor.insert(tk.END, config_content)
        
        def save_config():
            """Save the configuration and reload environment variables"""
            new_config = editor.get("1.0", tk.END)
            with open(env_path, 'w') as f:
                f.write(new_config)
            
            # Reload environment variables
            load_dotenv(env_path)
            
            logger.info("Database configuration updated")
            messagebox.showinfo("Success", "Configuration saved successfully!")
            config_window.destroy()
            
        def test_connection():
            """Test the database connection with the current editor values"""
            # Save current values to a temporary file
            temp_env = os.path.join(application_path, '.env.temp')
            with open(temp_env, 'w') as f:
                f.write(editor.get("1.0", tk.END))
                
            # Load temporary environment
            from dotenv import dotenv_values
            config = dotenv_values(temp_env)
            
            # Test connection
            try:
                db_server = config.get('DB_SERVER')
                db_name = config.get('DB_NAME')
                db_username = config.get('DB_USERNAME')
                db_password = config.get('DB_PASSWORD')
                
                if not all([db_server, db_name, db_username, db_password]):
                    raise ValueError("Missing required database parameters")
                
                # Try different drivers
                drivers = [
                    "{ODBC Driver 17 for SQL Server}",
                    "{ODBC Driver 13 for SQL Server}",
                    "{SQL Server Native Client 11.0}",
                    "{SQL Server}"
                ]
                
                conn = None
                conn_err = None
                used_driver = None
                
                for driver in drivers:
                    try:
                        conn_str = f"DRIVER={driver};SERVER={db_server};DATABASE={db_name};UID={db_username};PWD={db_password}"
                        conn = pyodbc.connect(conn_str)
                        used_driver = driver
                        break
                    except pyodbc.Error as e:
                        conn_err = e
                        continue
                        
                if conn is None:
                    if conn_err:
                        raise conn_err
                    else:
                        raise Exception("No suitable SQL Server driver found")
                
                # Close connection
                conn.close()
                
                messagebox.showinfo("Success", f"Connection successful using {used_driver}!")
            except Exception as e:
                messagebox.showerror("Connection Failed", f"Error: {str(e)}")
            finally:
                # Remove temp file
                if os.path.exists(temp_env):
                    os.remove(temp_env)
        
        # Button frame
        btn_frame = ttk.Frame(config_window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Test Connection", command=test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save", command=save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=config_window.destroy).pack(side=tk.LEFT, padx=5)

    def toggle_scheduler(self):
        if not self.scheduler_active:
            self.start_scheduler()
        else:
            self.stop_scheduler()

    def start_scheduler(self):
        scheduled_time = self.schedule_time.get()
        try:
            # Validate time format
            hour, minute = map(int, scheduled_time.split(':'))
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError
            
            self.scheduler_active = True
            self.schedule_button.config(text="Stop Scheduler")
            
            logger.info(f"Scheduler activated - will run every day at {scheduled_time}")
            self.status_var.set(f"Scheduler active - next run at {scheduled_time}")
            
            # Clear existing schedule
            schedule.clear()
            
            # Schedule the job
            schedule.every().day.at(scheduled_time).do(self.start_scraping)
            
            # Start the scheduler in a background thread
            self.schedule_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.schedule_thread.start()
            
        except ValueError:
            logger.error("Invalid time format. Please use HH:MM format (e.g., 15:00)")
            self.status_var.set("Invalid time format")

    def stop_scheduler(self):
        self.scheduler_active = False
        self.schedule_button.config(text="Start Scheduler")
        schedule.clear()
        logger.info("Scheduler stopped")
        self.status_var.set("Scheduler stopped")

    def run_scheduler(self):
        while self.scheduler_active:
            schedule.run_pending()
            time.sleep(1)

    def start_manual_fetch(self):
        if not self.scraping_in_progress:
            threading.Thread(target=self.start_scraping, daemon=True).start()

    def start_scraping(self):
        if self.scraping_in_progress:
            logger.warning("Scraping already in progress")
            return
            
        self.scraping_in_progress = True
        self.fetch_button.config(state="disabled")
        self.status_var.set("Scraping in progress...")
        self.progress_var.set(0)
        self.start_time = time.time()
        
        # Start the elapsed time updater
        self.update_elapsed_time()
        
        threading.Thread(target=self.scrape_all_sector, daemon=True).start()

    def update_elapsed_time(self):
        if not self.start_time or not self.scraping_in_progress:
            return
            
        elapsed = time.time() - self.start_time
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"Elapsed Time: {hours}:{minutes:02d}:{seconds:02d}"
        self.elapsed_time_var.set(time_str)
        
        # Schedule the next update
        if self.scraping_in_progress:
            self.root.after(1000, self.update_elapsed_time)

    def get_db_connection(self):
        """Create and return a database connection with graceful error handling"""
        try:
            # Check for required environment variables
            DB_SERVER = os.getenv("DB_SERVER")
            DB_NAME = os.getenv("DB_NAME")
            DB_USERNAME = os.getenv("DB_USERNAME")
            DB_PASSWORD = os.getenv("DB_PASSWORD")
            
            # Validate environment variables
            if not all([DB_SERVER, DB_NAME, DB_USERNAME, DB_PASSWORD]):
                missing = []
                if not DB_SERVER: missing.append("DB_SERVER")
                if not DB_NAME: missing.append("DB_NAME")
                if not DB_USERNAME: missing.append("DB_USERNAME")
                if not DB_PASSWORD: missing.append("DB_PASSWORD")
                
                error_msg = f"Missing environment variables: {', '.join(missing)}"
                logger.error(error_msg)
                messagebox.showerror("Configuration Error", 
                                f"Please check your .env file. {error_msg}")
                return None
            
            # Try different drivers in order of preference
            drivers = [
                "{ODBC Driver 17 for SQL Server}",
                "{ODBC Driver 13 for SQL Server}",
                "{SQL Server Native Client 11.0}",
                "{SQL Server}"
            ]
            
            conn = None
            conn_err = None
            
            for driver in drivers:
                try:
                    conn_str = f"DRIVER={driver};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USERNAME};PWD={DB_PASSWORD}"
                    conn = pyodbc.connect(conn_str)
                    logger.info(f"Connected using {driver}")
                    break
                except pyodbc.Error as e:
                    conn_err = e
                    continue
                    
            if conn is None:
                if conn_err:
                    raise conn_err
                else:
                    raise Exception("No suitable SQL Server driver found")
                    
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            messagebox.showerror("Database Connection Error", str(e))
            return None

    def fetch_company_list(self):
        """Fetch all company names from the database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return []
                    
            cursor = conn.cursor()
            cursor.execute("SELECT sector_code, MAX(last_updated) AS last_updated FROM sector_info GROUP BY sector_code ORDER BY last_updated;")
            sector_code = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return sector_code
        except Exception as e:
            logger.error(f"Error fetching company list: {str(e)}")
            return []

    def scrape_sector_wise_company_data(self, industryno):
        """Scrape data for a single company and return the parsed data"""
        try:
            url = f"https://www.dsebd.org/companylistbyindustry.php?industryno={industryno}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch data for {industryno}: HTTP {response.status_code}")
                return None
                    
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find all company links
            industry_links = soup.select('a.ab1')
            
            sectors = []
            
            # Extract industry number and name from each link
            for link in industry_links:
                href = link.get('href', '')
                
                # Extract the industry number from the href attribute
                company = None
                if 'name=' in href:
                    company = href.split('name=')[1].split('&')[0]
                
                # Get the industry name from the link text
                sector_name = link.text.strip()
                
                if company and sector_name:
                    sectors.append({
                        'sector_code': industryno,
                        'company': company,
                        'last_updated': datetime.now()
                    })
            return sectors 
        except Exception as e:
            logger.error(f"Error scraping data for {industryno}: {str(e)}")
            return None

    def store_data(self, company_data):
        """Store scraped data in the database"""
        if not company_data:
            logger.warning("No data to store")
            return
        
        # Flatten the company_data list if it's a list of lists
        flattened_data = [company for sublist in company_data for company in sublist]
        try:
            conn = self.get_db_connection()
            if not conn:
                return
                        
            cursor = conn.cursor()
            
            # Ensure company_data is now a list of dictionaries
            if isinstance(flattened_data, list) and isinstance(flattened_data[0], dict):
                # Extract the data from the dictionaries
                data_to_insert = [(entry['sector_code'], entry['company'], entry['last_updated']) for entry in flattened_data]
            else:
                raise ValueError("company_data is not in the expected format (list of dictionaries)")
            
            # Insert data into Sector_Symbol table
            logger.info(f"Starting insert")
            insert_query = """
                INSERT INTO Sector_Symbol 
                (sector_code, company, last_updated)
                VALUES (?, ?, ?)
            """
            cursor.executemany(insert_query, data_to_insert)
            
            logger.info(f"Data inserted successfully")
            conn.commit()
            logger.info(f"Successfully stored data for {len(flattened_data)} companies")
            
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing data: {str(e)}")
            
    def update_progress(self, completed, total):
        """Update the progress bar and text"""
        if total > 0:
            progress_pct = (completed / total) * 100
            self.progress_var.set(progress_pct)
            self.progress_text.set(f"{completed}/{total} companies processed")
        else:
            self.progress_var.set(0)
            self.progress_text.set("No companies to process")

    def scrape_all_sector(self):
        """Main function to scrape and store data for all companies"""
        logger.info("Starting scraping process")
        
        try:
            # Fetch company list
            sectors_code = self.fetch_company_list()
            if not sectors_code:
                logger.error("No companies found to scrape")
                self.finish_scraping()
                return
            
            total_sectors = len(sectors_code)
            logger.info(f"Found {total_sectors} companies to scrape")
            
            # Use ThreadPoolExecutor for parallel processing
            company_shares = []
            completed = 0
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit scraping tasks
                future_to_company = {executor.submit(self.scrape_sector_wise_company_data, sector_code): sector_code for sector_code in sectors_code}
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_company):
                    result = future.result()
                    if result:
                        company_shares.append(result)
                    
                    completed += 1
                    self.update_progress(completed, total_sectors)
            
            # Store the scraped data
            self.store_data(company_shares)
            
            logger.info("Scraping process completed successfully")
        except Exception as e:
            logger.error(f"Error in scraping process: {str(e)}")
        finally:
            self.finish_scraping()


    def finish_scraping(self):
        """Reset the UI after scraping is complete"""
        self.scraping_in_progress = False
        self.fetch_button.config(state="normal")
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"Completed in {hours}:{minutes:02d}:{seconds:02d}"
        
        self.status_var.set("Ready")
        self.elapsed_time_var.set(time_str)
        logger.info(f"Scraping completed in {time_str}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()