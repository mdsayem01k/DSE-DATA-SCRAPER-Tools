import os
import logging
import sys
from dotenv import load_dotenv, dotenv_values

# Get application path for executable support
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle
    application_path = os.path.dirname(sys.executable)
else:
    # If run as a normal Python script
    application_path = os.path.dirname(os.path.abspath(__file__))

# Set the working directory to the application path
os.chdir(application_path)


class EnvConfig:
    """Handles environment configuration"""
    
    def __init__(self, logger):
        self.logger = logger
        self.env_path = os.path.join(application_path, '.env')
        self.ensure_env_file_exists()
        self.load_env()
    
    def ensure_env_file_exists(self):
        """Create a sample .env file if it doesn't exist"""
        if not os.path.exists(self.env_path):
            with open(self.env_path, 'w') as f:
                f.write("""# Database Configuration
DB_SERVER=your_server_name
DB_NAME=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
""")
            self.logger.info("Created sample .env file. Please edit with your database details.")
            return False
        return True
    
    def load_env(self):
        """Load environment variables"""
        load_dotenv(self.env_path)
    
    def get_config_content(self):
        """Read current config content"""
        if os.path.exists(self.env_path):
            with open(self.env_path, 'r') as f:
                return f.read()
        else:
            return """# Database Configuration
DB_SERVER=your_server_name
DB_NAME=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password"""
    
    def save_config(self, config_content):
        """Save config content to file"""
        with open(self.env_path, 'w') as f:
            f.write(config_content)
        
        # Reload environment variables
        self.load_env()
        self.logger.info("Database configuration updated")
    
    def create_temp_config(self, config_content):
        """Create temporary config file for testing"""
        temp_env = os.path.join(application_path, '.env.temp')
        with open(temp_env, 'w') as f:
            f.write(config_content)
        return temp_env
    
    def remove_temp_config(self):
        """Remove temporary config file"""
        temp_env = os.path.join(application_path, '.env.temp')
        if os.path.exists(temp_env):
            os.remove(temp_env)
