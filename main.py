import os
import sys
import tkinter as tk
from tkinter import ttk
import importlib

class TabbedApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DSE DATA SCRAPER")
        self.geometry("800x600")
        
        # Set the window background to match your application
        self.configure(bg="#f0f0f0")
        
        style = ttk.Style()
        
        # Use the 'clam' theme which allows more customization
        style.theme_use("clam")
        
        # Remove the extra space above tabs by setting the borderwidth and padding to 0
        style.configure("TNotebook", 
                        borderwidth=0,
                        tabmargins=[0, 0, 0, 0],
                        background="#f0f0f0")  # Match window background
        
        # Configure tab appearance
        style.configure("TNotebook.Tab", 
                        background="#00ffff",   # Cyan for inactive tabs
                        foreground="black",
                        font=("Arial", 16),
                        borderwidth=0)
        
        # Configure selected tab
        style.map("TNotebook.Tab", 
                  background=[("selected", "#f0f0f0")],
                  foreground=[("selected", "black")])
        
        # Create a frame for the tabs to ensure they start at the very top
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True)
        
        # Create the notebook widget
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Create frames for each project
        self.share_scraper_frame = ttk.Frame(self.notebook)
        self.sector_scraper_frame = ttk.Frame(self.notebook)
        self.project3_frame = ttk.Frame(self.notebook)
        self.project4_frame = ttk.Frame(self.notebook)
        
        # Add the frames to the notebook with tab names
        self.notebook.add(self.share_scraper_frame, text="Share Scraper")
        self.notebook.add(self.sector_scraper_frame, text="Sector Scraper")
        self.notebook.add(self.project3_frame, text="Project 3")
        self.notebook.add(self.project4_frame, text="Project 4")
        
        # Initialize each project's contents
        self.initialize_project(self.share_scraper_frame, 'share_ratio_scraper')
        self.initialize_project(self.sector_scraper_frame, 'sector_scraper')
        
        # Override the tab appearance after creation
        # This helps eliminate any extra space above tabs
        self.update_idletasks()
        self.after(10, self.fix_tab_header)
        
    def fix_tab_header(self):
        """Attempt to fix any remaining header issues"""
        style = ttk.Style()
        style.layout("TNotebook", [
            ("TNotebook.client", {"sticky": "nswe"})
        ])
        self.update_idletasks()
    
    def initialize_project(self, scraper_frame, folder_name):
        """Initialize Scraper project"""
        try:
            # Add the project directory to the path so we can import the module
            module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder_name)
            sys.path.insert(0, module_path)
            
            # Dynamically import the module and access the ScraperApp class
            scraper_module = importlib.import_module(folder_name)
            ScraperApp = getattr(scraper_module, "ScraperApp")
            
            # Initialize the scraper app with the passed frame as the parent
            self.scraper_app = ScraperApp(scraper_frame)
            
        except ImportError as e:
            # Show error if module couldn't be imported
            print(f"Error importing Scraper module: {str(e)}\n\nMake sure project folder exists and ScraperApp is defined.")
            error_label = tk.Label(
                scraper_frame,  # Fixed this to use the passed scraper_frame
                text=f"Error importing Scraper module: {str(e)}\n\nMake sure project folder exists and ScraperApp is defined.",
                fg="red"
            )
            error_label.pack(pady=100)

if __name__ == "__main__":
    app = TabbedApplication()
    app.mainloop()
