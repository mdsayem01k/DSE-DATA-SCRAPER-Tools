import time
import tkinter as tk
from tkinter import ttk, scrolledtext

from log.scraper_log import LoggerSetup
from scheduler.sheduler import ScraperScheduler
from config.dbConfig import DatabaseManager
from config.envConfig import EnvConfig
from config.dbEdit import ConfigEditorWindow


class BaseScraperApp:
    def __init__(self, parent, title="Scraper Module", engine_class=None, module_name="main"):
        self.parent = parent
        self.title = title
        self.engine_class = engine_class 
        self.module_name = module_name
        
        # Initialize module-specific logger
        self.logger = LoggerSetup.setup_file_logger(self.module_name)
        
        # Initialize common managers
        self.env_manager = EnvConfig(self.logger)
        self.db_manager = DatabaseManager(self.logger)
        
        # Initialize UI variables
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text = tk.StringVar(value="0/0 sectors processed")
        self.elapsed_time_var = tk.StringVar(value="Elapsed Time: 0:00:00")
        self.log_text = None
        self.manual_scrape_button = None
        self.schedule_button = None
        self.schedule_time = None
        
        # Initialize state variables
        self.start_time = None
        
        # These will be initialized by subclasses
        self.scraper = None
        self.scraper_engine = None
        self.scheduler = None
        
        # DO NOT call initialize_ui() here - it will be called after setup_scraper()
        
    def setup_scraper(self):
        """Set up the scraper components"""
        if self.engine_class:
            self.scraper = self.create_scraper()
            self.scraper_engine = self.engine_class(self.logger, self.db_manager, self.scraper)
    
    def create_scraper(self):
        """Create and return appropriate scraper instance - can be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement create_scraper method")
        
    def complete_initialization(self):
        """Complete initialization after scraper is set up"""
        self.scheduler = ScraperScheduler(self.logger, self.start_scraping)
        self.initialize_ui()  # Now it's safe to call this
        # Add GUI handler to the module-specific logger
        self.logger = LoggerSetup.setup_gui_logger(self.logger, self.log_text)
        
    def initialize_ui(self):
        # Make sure scraper_engine exists before trying to use it
        if self.scraper_engine is None:
            raise ValueError("scraper_engine must be initialized before calling initialize_ui")
            
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title - uses the instance variable self.title
        self.title_label = tk.Label(main_frame, text=self.title, font=("Arial", 16))
        self.title_label.pack(pady=5)

        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.pack(fill=tk.X, pady=5)

        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 12))
        status_label.pack(side=tk.LEFT, padx=5)
        
        time_label = ttk.Label(status_frame, textvariable=self.elapsed_time_var, font=("Arial", 12))
        time_label.pack(side=tk.RIGHT, padx=5)
        
        # Control section
        control_frame = ttk.Frame(main_frame, padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        # Manual scrape button
        self.manual_scrape_button = tk.Button(
            control_frame, 
            text="Scrape Now", 
            command=self.start_manual_fetch,
            bg="#3498db",
            fg="white",
            cursor="hand2",
            padx=20,
            pady=5,
            font=("Segoe UI", 10, "bold")
        )
        self.manual_scrape_button.pack(side=tk.LEFT, padx=5)
        
        self.schedule_button = tk.Button(
            control_frame,
            text="Start Scheduler",
            command=self.toggle_scheduler,
            bg="#059862",
            fg="white",
            cursor="hand2",
            padx=20,
            pady=5,         
            font=("Segoe UI", 10, "bold"),
        )
        self.schedule_button.pack(side=tk.LEFT, padx=5)
        
        # Schedule time entry
        time_frame = ttk.Frame(control_frame)
        time_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(time_frame, text="Schedule Time (HH:MM):", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.schedule_time = ttk.Entry(time_frame, width=10)
        self.schedule_time.pack(side=tk.LEFT, padx=5, ipady=4)
        self.schedule_time.insert(0, "15:00")
        
        # DB Config button
        self.config_button = tk.Button(
            control_frame, 
            text="Edit DB Config", 
            command=self.edit_config, 
            cursor="hand2", 
            bg="#28adab",
            fg="white", 
            padx=20,
            pady=5,         
            font=("Segoe UI", 10, "bold")
        )
        self.config_button.pack(side=tk.RIGHT, padx=5)
        
        # Progress section
        progress_frame = ttk.Frame(main_frame, padding="10")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X)
        
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_text)
        progress_label.pack(pady=5)
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Set callbacks for the scraper engine
        self.scraper_engine.set_callbacks(
            progress_callback=self.update_progress,
            completion_callback=self.finish_scraping
        )

    def start_manual_fetch(self):
        """Start manual scraping"""
        if not self.scraper_engine.is_scraping():
            self.start_scraping()
    
    def start_scraping(self):
        """Start the scraping process"""
        if self.scraper_engine.is_scraping():
            return
        
        self.manual_scrape_button.config(state="disabled")
        self.status_var.set("Scraping in progress...")
        self.progress_var.set(0)
        self.start_time = time.time()
        
        # Start the elapsed time updater
        self.update_elapsed_time()
        
        # Start the scraping process
        self.scraper_engine.start_scraping()
    
    def update_elapsed_time(self):
        """Update the elapsed time display"""
        if not self.start_time or not self.scraper_engine.is_scraping():
            return
            
        elapsed = time.time() - self.start_time
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"Elapsed Time: {hours}:{minutes:02d}:{seconds:02d}"
        self.elapsed_time_var.set(time_str)
        
        # Schedule the next update
        if self.scraper_engine.is_scraping():
            self.parent.after(1000, self.update_elapsed_time)
    
    def update_progress(self, completed, total):
        """Update the progress bar and text"""
        if total > 0:
            progress_pct = (completed / total) * 100
            self.progress_var.set(progress_pct)
            self.progress_text.set(f"{completed}/{total} sectors processed")
        else:
            self.progress_var.set(0)
            self.progress_text.set("No sectors to process")
    
    def finish_scraping(self):
        """Reset the UI after scraping is complete"""
        self.manual_scrape_button.config(state="normal")
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"Completed in {hours}:{minutes:02d}:{seconds:02d}"
        
        self.status_var.set("Ready")
        self.elapsed_time_var.set(time_str)
    
    def toggle_scheduler(self):
        """Toggle the scheduler on/off"""
        if not self.scheduler.is_active:
            self.start_scheduler()
        else:
            self.stop_scheduler()
    
    def start_scheduler(self):
        """Start the scheduler"""
        scheduled_time = self.schedule_time.get()
        if self.scheduler.start(scheduled_time):
            self.schedule_button.config(text="Stop Scheduler", bg="#E74C3C", fg="white")
            self.status_var.set(f"Scheduler active - next run at {scheduled_time}")
        else:
            self.status_var.set("Invalid time format")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler.stop()
        self.schedule_button.config(text="Start Scheduler", bg="#059862", fg="white")
        self.status_var.set("Scheduler stopped")
    
    def edit_config(self):
        """Open the configuration editor"""
        config_editor = ConfigEditorWindow(
            self.parent,
            self.env_manager,
            self.db_manager,
            self.logger
        )
        config_editor.show()