import json
import os

class Settings:
    def __init__(self):
        self.SETTINGS_FILE = "app_settings.json"
        self.default_settings = {
            'theme': 'default',
            'font_size': 12,
            'auto_save': True,
            'recent_files': []
        }
        self.current = self.load_settings()
        
    def load_settings(self):
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r') as f:
                    return {**self.default_settings, **json.load(f)}
            except json.JSONDecodeError:
                return self.default_settings
        return self.default_settings
    
    def save_settings(self):
        with open(self.SETTINGS_FILE, 'w') as f:
            json.dump(self.current, f, indent=2)