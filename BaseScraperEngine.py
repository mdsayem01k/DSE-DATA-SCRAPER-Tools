import threading

class BaseScraperEngine:
    """Base class for scraper engines with common functionality"""
    
    def __init__(self, logger, db_manager, scraper):
        self.logger = logger
        self.db_manager = db_manager
        self.scraper = scraper
        self.scraping_in_progress = False
        self.progress_callback = None
        self.completion_callback = None
        
    def set_callbacks(self, progress_callback, completion_callback):
        """Set callbacks for progress updates and completion"""
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
    
    def is_scraping(self):
        """Check if scraping is in progress"""
        return self.scraping_in_progress
    
    def start_scraping(self):
        """Start the scraping process"""
        if self.scraping_in_progress:
            self.logger.warning("Scraping already in progress")
            return False
            
        self.scraping_in_progress = True
        threading.Thread(target=self.scrape_data, daemon=True).start()
        return True
    
    def scrape_data(self):
        """Template method to be overridden by subclasses"""
        try:
            self.logger.info("Starting scraping process")
            self._execute_scraping()
            self.logger.info("Scraping process completed successfully")
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}", exc_info=True)
        finally:
            self.finish_scraping()
    
    def _execute_scraping(self):
        """Abstract method that must be implemented by subclasses to perform actual scraping"""
        raise NotImplementedError("Subclasses must implement _execute_scraping method")
    
    def update_progress(self, completed, total):
        """Update progress through the callback if available"""
        if self.progress_callback:
            self.progress_callback(completed, total)
    
    def finish_scraping(self):
        """Reset state after scraping is complete"""
        self.scraping_in_progress = False
        if self.completion_callback:
            self.completion_callback()
    
    def stop_scraping(self):
        """Request to stop the scraping process"""
        if self.scraping_in_progress:
            self.logger.info("Stop requested for scraping process")
            # Implementing classes should check this flag periodically
            self.scraping_in_progress = False
            return True
        return False
    
    def safe_float(self, value):
        """Convert string to float safely, handling empty values and formatting."""
        if not value or value.lower() in ['n/a', '']:
            return None
            
        try:
            return float(value.replace(',', '').replace(' ', ''))
        except (ValueError, TypeError):
            return None