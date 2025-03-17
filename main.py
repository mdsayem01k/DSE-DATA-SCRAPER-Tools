import os
import sys
import tkinter as tk
from tkinter import ttk
import importlib

# Make sure we add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

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
        self.sector_company_scraper_frame = ttk.Frame(self.notebook)
        self.sector_scraper_frame = ttk.Frame(self.notebook)
        self.pe_scraper_frame = ttk.Frame(self.notebook)
        
        # Add the frames to the notebook with tab names
        self.notebook.add(self.share_scraper_frame, text="Share Scraper")
        self.notebook.add(self.sector_company_scraper_frame, text="Sector-Company Scraper")
        self.notebook.add(self.sector_scraper_frame, text="Sector Scraper")
        self.notebook.add(self.pe_scraper_frame, text="PE Ration Scraper")
        
        # Initialize each project's contents
        self.initialize_project(self.share_scraper_frame, 'share_ratio_scraper')
        self.initialize_project(self.sector_company_scraper_frame, 'sector_wise_company')
        self.initialize_project(self.sector_scraper_frame, 'sector_scraper')
        self.initialize_project(self.pe_scraper_frame, 'PE_scraper')
        
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
            # Make sure the module directory exists
            module_path = os.path.join(current_dir, folder_name)
            if not os.path.exists(module_path):
                raise ImportError(f"Module directory {module_path} does not exist")
                
            # Check if the module has an __init__.py file
            init_file = os.path.join(module_path, "__init__.py")
            if not os.path.exists(init_file):
                # Create an empty __init__.py file
                with open(init_file, 'w') as f:
                    pass
                    
            # Add the project directory to the path so we can import the module
            if module_path not in sys.path:
                sys.path.insert(0, module_path)
                
            # Import the module
            try:
                # First try to import the module by name
                scraper_module = importlib.import_module(folder_name)
            except ImportError:
                # If that fails, try to import directly from the module path
                module_name = os.path.basename(module_path)
                spec = importlib.util.spec_from_file_location(
                    module_name, 
                    os.path.join(module_path, f"{module_name}.py")
                )
                if spec:
                    scraper_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(scraper_module)
                else:
                    raise ImportError(f"Cannot find module {folder_name}")
                    
            # Get the ScraperApp class from the module
            if hasattr(scraper_module, "ScraperApp"):
                ScraperApp = getattr(scraper_module, "ScraperApp")
                self.scraper_app = ScraperApp(scraper_frame)
            else:
                raise ImportError(f"Module {folder_name} does not have a ScraperApp class")
                
        except ImportError as e:
            # Show error if module couldn't be imported
            print(f"Error importing {folder_name} module: {str(e)}")
            error_label = tk.Label(
                scraper_frame,
                text=f"Error importing {folder_name} module:\n{str(e)}\n\nMake sure project folder exists and ScraperApp is defined.",
                fg="red"
            )
            error_label.pack(pady=100)
        except Exception as e:
            # Show any other errors
            print(f"Error initializing {folder_name} module: {str(e)}")
            error_label = tk.Label(
                scraper_frame,
                text=f"Error initializing {folder_name} module:\n{str(e)}",
                fg="red"
            )
            error_label.pack(pady=100)

if __name__ == "__main__":
    app = TabbedApplication()
    app.mainloop()