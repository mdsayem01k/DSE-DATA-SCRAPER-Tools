import logging
import os
import sys
from handler.customhandler import CustomHandler

# Get application path for executable support
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle
    application_path = os.path.dirname(sys.executable)
else:
    # If run as a normal Python script
    application_path = os.path.dirname(os.path.abspath(__file__))

# Set the working directory to the application path
os.chdir(application_path)

class LoggerSetup:
    """Handles setting up and configuring loggers for different modules"""
    
    @staticmethod
    def setup_file_logger(module_name="main"):
        """Configure logging to a module-specific file
        
        Args:
            module_name (str): Name of the module to create logger for
            
        Returns:
            logging.Logger: Configured logger instance
        """
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(application_path, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        # Create a logger with the module name
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.INFO)
        
        # Prevent log propagation to avoid duplicate logs
        logger.propagate = False
        
        # Check if the logger already has handlers to avoid duplicates
        has_file_handler = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        
        if not has_file_handler:
            # Create file handler for this module
            file_handler = logging.FileHandler(
                os.path.join(logs_dir, f'{module_name}.log')
            )
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            
            # Add the handler to logger
            logger.addHandler(file_handler)
        
        return logger
    
    @staticmethod
    def setup_gui_logger(logger, log_widget):
        """Add GUI handler to a module's logger
        
        Args:
            logger (logging.Logger): Logger to add GUI handler to
            log_widget: Tkinter text widget to display logs
            
        Returns:
            logging.Logger: Logger with GUI handler added
        """
        if not log_widget:
            return logger
            
        # Check if a GUI handler already exists to avoid duplicates
        has_text_handler = any(isinstance(h, CustomHandler) for h in logger.handlers)
        
        if not has_text_handler:
            # Create and add GUI handler
            text_handler = CustomHandler(log_widget)
            text_handler.setLevel(logging.INFO)
            text_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            text_handler.setFormatter(text_formatter)
            logger.addHandler(text_handler)
        
        return logger