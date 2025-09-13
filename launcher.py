import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import requests
import json
import socket
import webbrowser
from datetime import datetime
import os
import sys

class SenatrackLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Senatrack Local Server Launcher")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Server process
        self.server_process = None
        self.server_running = False
        self.server_port = 8000
        self.server_host = "0.0.0.0"  # Allow external connections
        
        # Network info
        self.local_ip = self.get_local_ip()
        
        self.setup_ui()
        self.check_server_status()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Senatrack Local Server", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Server Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Server Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Stopped", foreground="red")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.status_indicator = ttk.Label(status_frame, text="●", foreground="red", font=("Arial", 16))
        self.status_indicator.grid(row=0, column=1, sticky=tk.E)
        
        # Server Controls Section
        controls_frame = ttk.LabelFrame(main_frame, text="Server Controls", padding="10")
        controls_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_frame.columnconfigure(1, weight=1)
        
        ttk.Label(controls_frame, text="Port:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.port_var = tk.StringVar(value=str(self.server_port))
        port_entry = ttk.Entry(controls_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=0, column=1, sticky=tk.W)
        
        self.start_button = ttk.Button(controls_frame, text="Start Server", 
                                      command=self.start_server)
        self.start_button.grid(row=0, column=2, padx=(10, 0))
        
        self.stop_button = ttk.Button(controls_frame, text="Stop Server", 
                                     command=self.stop_server, state="disabled")
        self.stop_button.grid(row=0, column=3, padx=(5, 0))
        
        # Network Access Section
        network_frame = ttk.LabelFrame(main_frame, text="Network Access", padding="10")
        network_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        network_frame.columnconfigure(1, weight=1)
        
        ttk.Label(network_frame, text="Local IP:").grid(row=0, column=0, sticky=tk.W)
        self.ip_label = ttk.Label(network_frame, text=self.local_ip, font=("Arial", 10, "bold"))
        self.ip_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(network_frame, text="Local URL:").grid(row=1, column=0, sticky=tk.W)
        self.url_label = ttk.Label(network_frame, text=f"http://{self.local_ip}:{self.server_port}", 
                                  font=("Arial", 10, "bold"), foreground="blue")
        self.url_label.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        
        # Copy URL button
        copy_button = ttk.Button(network_frame, text="Copy URL", 
                                command=self.copy_url)
        copy_button.grid(row=1, column=2, padx=(10, 0))
        
        # Open in browser button
        browser_button = ttk.Button(network_frame, text="Open in Browser", 
                                   command=self.open_in_browser)
        browser_button.grid(row=1, column=3, padx=(5, 0))
        
        # Sync Controls Section
        sync_frame = ttk.LabelFrame(main_frame, text="Data Synchronization", padding="10")
        sync_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(sync_frame, text="Sync to Online", 
                  command=self.sync_to_online).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(sync_frame, text="Sync from Online", 
                  command=self.sync_from_online).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(sync_frame, text="Bidirectional Sync", 
                  command=self.bidirectional_sync).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(sync_frame, text="Check Status", 
                  command=self.check_sync_status).grid(row=0, column=3)
        
        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Server Log", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        clear_log_button = ttk.Button(log_frame, text="Clear Log", 
                                     command=self.clear_log)
        clear_log_button.grid(row=1, column=0, pady=(5, 0))
        
        # Start status checking
        self.check_status_periodically()
    
    def get_local_ip(self):
        """Get the local IP address"""
        try:
            # Connect to a remote server to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def log_message(self, message):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear the log text"""
        self.log_text.delete(1.0, tk.END)
    
    def start_server(self):
        """Start the local server"""
        try:
            port = int(self.port_var.get())
            if port < 1024 or port > 65535:
                messagebox.showerror("Error", "Port must be between 1024 and 65535")
                return
            
            self.server_port = port
            self.log_message(f"Starting server on {self.server_host}:{self.server_port}")
            
            # Start server in a separate thread
            server_thread = threading.Thread(target=self._run_server, daemon=True)
            server_thread.start()
            
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.server_running = True
            
            # Update URL label
            self.url_label.config(text=f"http://{self.local_ip}:{self.server_port}")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
            self.log_message(f"Error starting server: {str(e)}")
    
    def _run_server(self):
        """Run the server process"""
        try:
            # Change to the app directory
            app_dir = os.path.join(os.path.dirname(__file__), "app")
            
            # Start the server
            self.server_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "app.main:app", 
                "--host", self.server_host, 
                "--port", str(self.server_port),
                "--reload"
            ], cwd=os.path.dirname(__file__), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
               universal_newlines=True, bufsize=1)
            
            self.log_message("Server started successfully")
            
            # Read server output
            for line in iter(self.server_process.stdout.readline, ''):
                if line:
                    self.log_message(f"SERVER: {line.strip()}")
            
        except Exception as e:
            self.log_message(f"Server error: {str(e)}")
            self.server_running = False
            self.root.after(0, self._server_stopped)
    
    def stop_server(self):
        """Stop the local server"""
        if self.server_process:
            self.log_message("Stopping server...")
            self.server_process.terminate()
            self.server_process = None
        
        self.server_running = False
        self._server_stopped()
    
    def _server_stopped(self):
        """Handle server stopped event"""
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Stopped", foreground="red")
        self.status_indicator.config(foreground="red")
        self.log_message("Server stopped")
    
    def check_server_status(self):
        """Check if the server is running"""
        try:
            response = requests.get(f"http://localhost:{self.server_port}/", timeout=2)
            if response.status_code == 200:
                self.status_label.config(text="Running", foreground="green")
                self.status_indicator.config(foreground="green")
                return True
        except:
            pass
        
        self.status_label.config(text="Stopped", foreground="red")
        self.status_indicator.config(foreground="red")
        return False
    
    def check_status_periodically(self):
        """Check server status periodically"""
        if self.server_running:
            self.check_server_status()
        
        # Schedule next check
        self.root.after(5000, self.check_status_periodically)
    
    def copy_url(self):
        """Copy the server URL to clipboard"""
        url = f"http://{self.local_ip}:{self.server_port}"
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.log_message(f"URL copied to clipboard: {url}")
    
    def open_in_browser(self):
        """Open the server URL in the default browser"""
        url = f"http://{self.local_ip}:{self.server_port}"
        webbrowser.open(url)
        self.log_message(f"Opened {url} in browser")
    
    def sync_to_online(self):
        """Sync local data to online"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server must be running to sync data")
            return
        
        def sync_thread():
            try:
                self.log_message("Starting sync to online...")
                response = requests.post(f"http://localhost:{self.server_port}/api/sync/to-online")
                if response.status_code == 200:
                    result = response.json()
                    self.log_message(f"Sync to online completed: {result.get('message', 'Success')}")
                else:
                    self.log_message(f"Sync to online failed: {response.text}")
            except Exception as e:
                self.log_message(f"Sync to online error: {str(e)}")
        
        threading.Thread(target=sync_thread, daemon=True).start()
    
    def sync_from_online(self):
        """Sync online data to local"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server must be running to sync data")
            return
        
        def sync_thread():
            try:
                self.log_message("Starting sync from online...")
                response = requests.post(f"http://localhost:{self.server_port}/api/sync/from-online")
                if response.status_code == 200:
                    result = response.json()
                    self.log_message(f"Sync from online completed: {result.get('message', 'Success')}")
                else:
                    self.log_message(f"Sync from online failed: {response.text}")
            except Exception as e:
                self.log_message(f"Sync from online error: {str(e)}")
        
        threading.Thread(target=sync_thread, daemon=True).start()
    
    def bidirectional_sync(self):
        """Perform bidirectional sync"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server must be running to sync data")
            return
        
        def sync_thread():
            try:
                self.log_message("Starting bidirectional sync...")
                response = requests.post(f"http://localhost:{self.server_port}/api/sync/bidirectional")
                if response.status_code == 200:
                    result = response.json()
                    self.log_message(f"Bidirectional sync completed: {result.get('message', 'Success')}")
                else:
                    self.log_message(f"Bidirectional sync failed: {response.text}")
            except Exception as e:
                self.log_message(f"Bidirectional sync error: {str(e)}")
        
        threading.Thread(target=sync_thread, daemon=True).start()
    
    def check_sync_status(self):
        """Check sync status"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server must be running to check sync status")
            return
        
        def status_thread():
            try:
                response = requests.get(f"http://localhost:{self.server_port}/api/sync/status")
                if response.status_code == 200:
                    result = response.json()
                    status_msg = (f"Local records: {result.get('local_records', 0)}, "
                                f"Online records: {result.get('online_records', 0)}, "
                                f"Unsynced changes: {result.get('unsynced_changes', 0)}")
                    self.log_message(f"Sync status: {status_msg}")
                else:
                    self.log_message(f"Failed to get sync status: {response.text}")
            except Exception as e:
                self.log_message(f"Sync status error: {str(e)}")
        
        threading.Thread(target=status_thread, daemon=True).start()
    
    def on_closing(self):
        """Handle application closing"""
        if self.server_process:
            self.stop_server()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = SenatrackLauncher(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
