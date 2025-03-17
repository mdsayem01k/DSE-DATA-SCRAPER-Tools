import tkinter as tk
from tkinter import ttk, messagebox
from dotenv import dotenv_values



class ConfigEditorWindow:
    """Handles the configuration editor window"""
    
    def __init__(self, parent, env_manager, db_manager, logger):
        self.parent = parent
        self.env_manager = env_manager
        self.db_manager = db_manager
        self.logger = logger
        self.window = None
        self.editor = None
        
    def show(self):
        """Show the config editor window"""
        # Create a new window
        self.window = tk.Toplevel(self.parent)
        self.window.title("Database Configuration")
        self.window.geometry("500x300")
        self.window.grab_set()  # Make it modal
        
        # Read current config
        config_content = self.env_manager.get_config_content()
        
        # Create editor
        ttk.Label(self.window, text="Edit your database configuration:").pack(pady=5)
        
        self.editor = tk.Text(self.window, height=10)
        self.editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.editor.insert(tk.END, config_content)
        
        # Button frame
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Test Connection", command=self.test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
    
    def test_connection(self):
        """Test the database connection with current editor values"""
        # Save current values to a temporary file
        temp_env = self.env_manager.create_temp_config(self.editor.get("1.0", tk.END))
        
        # Load temporary environment
        config = dotenv_values(temp_env)
        
        # Test connection
        success, message = self.db_manager.test_connection(config)
        
        if success:
            messagebox.showinfo("Success", f"Connection successful using {message}!")
        else:
            messagebox.showerror("Connection Failed", f"Error: {message}")
        
        # Remove temp file
        self.env_manager.remove_temp_config()
    
    def save_config(self):
        """Save the configuration and reload environment variables"""
        new_config = self.editor.get("1.0", tk.END)
        self.env_manager.save_config(new_config)
        
        messagebox.showinfo("Success", "Configuration saved successfully!")
        self.window.destroy()
