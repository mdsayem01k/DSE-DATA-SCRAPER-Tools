import schedule
import threading
import time


class ScraperScheduler:
    """Handles scheduling scraping tasks"""
    
    def __init__(self, logger, scrape_callback):
        self.logger = logger
        self.scrape_callback = scrape_callback
        self.is_active = False
        self.schedule_thread = None
    
    def start(self, scheduled_time):
        """Start the scheduler"""
        try:
            # Validate time format
            hour, minute = map(int, scheduled_time.split(':'))
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError("Invalid time format")
            
            self.is_active = True
            
            # Clear existing schedule
            schedule.clear()
            
            # Schedule the job
            schedule.every().day.at(scheduled_time).do(self.scrape_callback)
            
            # Start the scheduler in a background thread
            self.schedule_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.schedule_thread.start()
            
            self.logger.info(f"Scheduler activated - will run every day at {scheduled_time}")
            return True
            
        except ValueError as e:
            self.logger.error(f"Scheduler error: {str(e)}")
            return False
    
    def stop(self):
        """Stop the scheduler"""
        self.is_active = False
        schedule.clear()
        self.logger.info("Scheduler stopped")
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_active:
            schedule.run_pending()
            time.sleep(1)

