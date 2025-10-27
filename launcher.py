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
import shutil
from pathlib import Path

class SenatrackLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Senatrack Local Server")
        self.root.geometry("950x750")
        self.root.resizable(True, True)
        
        # Configure colors
        self.colors = {
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6',
            'bg': '#f8fafc',
            'card': '#ffffff'
        }
        
        # Server process
        self.server_process = None
        self.server_running = False
        self.server_port = 0
        self.server_host = "0.0.0.0"
        
        # Network info
        self.local_ip = self.get_local_ip()
        
        # Sync status
        self.sync_in_progress = False
        
        self.setup_ui()
        self.check_server_status()
        self.update_status_periodically()
    
    def setup_ui(self):
        """Setup the modern user interface"""
        # Configure root
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.configure(bg=self.colors['bg'])
        
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="15")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # ===== HEADER =====
        header_frame = ttk.Frame(main_container)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(header_frame, text="Senatrack Local Server", 
                               font=("Segoe UI", 20, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Status indicator
        status_container = ttk.Frame(header_frame)
        status_container.grid(row=0, column=1, sticky=tk.E)
        
        self.status_canvas = tk.Canvas(status_container, width=20, height=20, 
                                       highlightthickness=0, bg=self.colors['bg'])
        self.status_canvas.grid(row=0, column=0, padx=(0, 8))
        self.status_circle = self.status_canvas.create_oval(4, 4, 16, 16, 
                                                            fill=self.colors['error'], outline="")
        
        self.status_label = ttk.Label(status_container, text="Server Stopped", 
                                      font=("Segoe UI", 11, "bold"))
        self.status_label.grid(row=0, column=1)
        
        # ===== TABBED INTERFACE =====
        notebook = ttk.Notebook(main_container)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab 1: Server Control
        server_tab = ttk.Frame(notebook, padding="15")
        notebook.add(server_tab, text="⚙️ Server Control")
        
        # Server info card
        info_card = ttk.LabelFrame(server_tab, text="Server Information", padding="15")
        info_card.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        info_card.columnconfigure(1, weight=1)
        
        ttk.Label(info_card, text="Local IP:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ip_value = ttk.Label(info_card, text=self.local_ip, font=("Segoe UI", 10))
        self.ip_value.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(info_card, text="Port:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.port_value = ttk.Label(info_card, text="Auto", font=("Segoe UI", 10))
        self.port_value.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(info_card, text="Server URL:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.url_label = ttk.Label(info_card, text=f"http://{self.local_ip}:<auto>",
                                   font=("Segoe UI", 10), foreground=self.colors['info'])
        self.url_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(server_tab)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)
        
        self.toggle_button = ttk.Button(control_frame, text="▶️ Start Server",
                                        command=self.toggle_server, width=24)
        self.toggle_button.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        open_button = ttk.Button(control_frame, text="🌐 Open Website", 
                                command=self.open_in_browser, width=24)
        open_button.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Quick actions
        actions_card = ttk.LabelFrame(server_tab, text="Quick Actions", padding="15")
        actions_card.grid(row=2, column=0, sticky=(tk.W, tk.E))
        actions_card.columnconfigure(0, weight=1)
        actions_card.columnconfigure(1, weight=1)
        
        ttk.Button(actions_card, text="📋 Copy URL", command=self.copy_url).grid(
            row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(actions_card, text="🔄 Refresh Frontend", command=self.copy_frontend_dist).grid(
            row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Tab 2: Sync Operations
        sync_tab = ttk.Frame(notebook, padding="15")
        notebook.add(sync_tab, text="🔄 Sync Operations")
        
        # Sync status
        sync_status_card = ttk.LabelFrame(sync_tab, text="Sync Status", padding="15")
        sync_status_card.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        sync_status_card.columnconfigure(1, weight=1)
        
        ttk.Label(sync_status_card, text="Last Sync:", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        self.last_sync_label = ttk.Label(sync_status_card, text="Never", font=("Segoe UI", 10))
        self.last_sync_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(sync_status_card, text="Sync Status:", font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.sync_status_label = ttk.Label(sync_status_card, text="Ready", font=("Segoe UI", 10))
        self.sync_status_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Progress bar for sync
        self.sync_progress = ttk.Progressbar(sync_status_card, mode='indeterminate')
        self.sync_progress.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Sync operations
        sync_ops_card = ttk.LabelFrame(sync_tab, text="Sync Operations", padding="15")
        sync_ops_card.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        sync_ops_card.columnconfigure(0, weight=1)
        sync_ops_card.columnconfigure(1, weight=1)
        
        ttk.Button(sync_ops_card, text="⬆️ Push to Online", 
                  command=self.sync_to_online).grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(sync_ops_card, text="⬇️ Pull from Online", 
                  command=self.sync_from_online).grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(sync_ops_card, text="🔄 Bidirectional Sync", 
                  command=self.bidirectional_sync).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(sync_ops_card, text="📊 Check Sync Status", 
                  command=self.check_sync_status).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Sync info
        info_text = ("ℹ️ Sync allows you to push local changes to the online database "
                    "or pull updates from online to your local database.")
        info_label = ttk.Label(sync_tab, text=info_text, wraplength=800, 
                              font=("Segoe UI", 9), foreground="gray")
        info_label.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Tab 3: Logs
        log_tab = ttk.Frame(notebook, padding="15")
        notebook.add(log_tab, text="📋 Logs")
        
        log_frame = ttk.Frame(log_tab)
        log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Configure log_tab grid weights
        log_tab.columnconfigure(0, weight=1)
        log_tab.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=100, 
                                                  font=("Consolas", 9), wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log controls
        log_controls = ttk.Frame(log_tab)
        log_controls.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(log_controls, text="🗑️ Clear Logs", command=self.clear_log).grid(
            row=0, column=0, padx=5)
        ttk.Button(log_controls, text="💾 Save Logs", command=self.save_logs).grid(
            row=0, column=1, padx=5)
        
        # Initial log message
        self.log_message("Senatrack Local Server initialized")
        self.log_message(f"Local IP: {self.local_ip}")
        self.log_message("Server URL will be shown after start")
    
    def get_local_ip(self):
        """Get the local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def log_message(self, message, level="INFO"):
        """Add a message to the log with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        
        # Color code based on level
        if level == "ERROR":
            start_idx = self.log_text.index("end-2c linestart")
            end_idx = self.log_text.index("end-1c")
            self.log_text.tag_add("error", start_idx, end_idx)
            self.log_text.tag_config("error", foreground=self.colors['error'])
        elif level == "SUCCESS":
            start_idx = self.log_text.index("end-2c linestart")
            end_idx = self.log_text.index("end-1c")
            self.log_text.tag_add("success", start_idx, end_idx)
            self.log_text.tag_config("success", foreground=self.colors['success'])
        elif level == "WARNING":
            start_idx = self.log_text.index("end-2c linestart")
            end_idx = self.log_text.index("end-1c")
            self.log_text.tag_add("warning", start_idx, end_idx)
            self.log_text.tag_config("warning", foreground=self.colors['warning'])
        
        self.log_text.see(tk.END)
    
    def find_free_port(self, start_port: int = 8000, end_port: int = 8100) -> int:
        """Find a free TCP port to bind the server to."""
        for port in range(start_port, end_port + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.bind(("", port))
                    return port
                except OSError:
                    continue
        return 8000

    def get_server_url(self) -> str:
        port = self.server_port if self.server_port else 8000
        return f"http://{self.local_ip}:{port}"

    def copy_frontend_dist(self):
        """Copy frontend dist folder to backend/dist for serving."""
        try:
            backend_dir = Path(__file__).parent
            frontend_dist = backend_dir.parent / "frontend-app" / "dist"
            backend_dist = backend_dir / "web"
            if not frontend_dist.exists():
                self.log_message("Frontend dist not found", "WARNING")
                return False
            if backend_dist.exists():
                shutil.rmtree(backend_dist)
            shutil.copytree(frontend_dist, backend_dist)
            self.log_message(f"Frontend dist copied to {backend_dist}", "SUCCESS")
            return True
        except Exception as e:
            self.log_message(f"Failed to copy frontend dist: {e}", "ERROR")
            return False
    
    def clear_log(self):
        """Clear the log text"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Logs cleared")
    
    def save_logs(self):
        """Save logs to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"senatrack_logs_{timestamp}.txt"
            with open(filename, 'w') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log_message(f"Logs saved to {filename}", "SUCCESS")
            messagebox.showinfo("Success", f"Logs saved to {filename}")
        except Exception as e:
            self.log_message(f"Failed to save logs: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to save logs: {str(e)}")
    
    def start_server(self):
        """Start the local server"""
        if self.server_running:
            self.log_message("Server already running", "WARNING")
            return
        try:
            # Pick a free port
            self.server_port = self.find_free_port()
            self.port_value.config(text=str(self.server_port))
            self.url_label.config(text=self.get_server_url())
            # Do not auto-copy dist on every start; rely on build script to place files in backend/web
            backend_web = Path(__file__).parent / "web"
            if not backend_web.exists():
                self.log_message("frontend not found in backend/web. Use the build script to publish dist.", "WARNING")
            self.log_message(f"Starting server on {self.server_host}:{self.server_port}")
            # Start server in a separate thread
            server_thread = threading.Thread(target=self._run_server, daemon=True)
            server_thread.start()
            self.server_running = True
            self.update_status_ui(False)
            self.toggle_button.config(text="⏹️ Stop Server")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
            self.log_message(f"Error starting server: {str(e)}", "ERROR")
    
    def _run_server(self):
        """Run the server process"""
        try:
            self.server_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "app.main:app", 
                "--host", self.server_host, 
                "--port", str(self.server_port),
                "--reload"
            ], cwd=os.path.dirname(__file__), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
               universal_newlines=True, bufsize=1)
            
            self.log_message("Server process started", "INFO")
            
            # Read server output
            for line in iter(self.server_process.stdout.readline, ''):
                if line:
                    text = line.strip()
                    self.log_message(text, "DEBUG")
                    if "Application startup complete." in text or "Uvicorn running on" in text:
                        self.root.after(0, lambda: self.update_status_ui(True))
            
        except Exception as e:
            self.log_message(f"Server error: {str(e)}", "ERROR")
            self.server_running = False
            self.root.after(0, self._server_stopped)
    
    def stop_server(self):
        """Stop the local server"""
        if self.server_process:
            self.log_message("Stopping server...")
            try:
            self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except Exception:
                try:
                    self.server_process.kill()
                except Exception:
                    pass
            self.server_process = None
        self.server_running = False
        self._server_stopped()

    def toggle_server(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()
    
    def _server_stopped(self):
        """Handle server stopped event"""
        self.toggle_button.config(text="▶️ Start Server")
        self.update_status_ui(False)
        self.log_message("Server stopped", "WARNING")
    
    def check_server_status(self):
        """Check if the server is running"""
        try:
            if not self.server_port:
                return False
            response = requests.get(f"http://localhost:{self.server_port}/api/health", timeout=2)
            if response.status_code == 200:
                self.update_status_ui(True)
                self.server_running = True
                return True
        except Exception:
            self.server_running = False
        self.update_status_ui(False)
        return False
    
    def update_status_ui(self, running):
        """Update the status UI elements"""
        if running:
            self.status_canvas.itemconfig(self.status_circle, fill=self.colors['success'])
            self.status_label.config(text="Server Running", foreground=self.colors['success'])
        else:
            self.status_canvas.itemconfig(self.status_circle, fill=self.colors['error'])
            self.status_label.config(text="Server Stopped", foreground=self.colors['error'])
    
    def update_status_periodically(self):
        """Update status periodically"""
            self.check_server_status()
        self.root.after(2000, self.update_status_periodically)
    
    def copy_url(self):
        """Copy the server URL to clipboard"""
        url = self.get_server_url()
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.log_message(f"URL copied to clipboard: {url}", "SUCCESS")
        messagebox.showinfo("Copied", f"URL copied to clipboard:\n{url}")
    
    def open_in_browser(self):
        """Open the server URL in the default browser"""
        url = self.get_server_url()
        webbrowser.open(url)
        self.log_message(f"Opened {url} in browser")
    
    def sync_to_online(self):
        """Sync local data to online"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server must be running to sync data")
            return
        
        if self.sync_in_progress:
            messagebox.showwarning("Warning", "Sync operation already in progress")
            return
        
        def sync_thread():
            try:
                self.sync_in_progress = True
                self.sync_progress.start()
                self.sync_status_label.config(text="Pushing to online...")
                self.log_message("Starting sync to online...")
                
                response = requests.post(f"http://localhost:{self.server_port}/api/sync/to-online", timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    self.log_message(f"Sync to online completed: {result.get('message', 'Success')}", "SUCCESS")
                    self.last_sync_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    messagebox.showinfo("Success", "Data successfully pushed to online database!")
                else:
                    self.log_message(f"Sync to online failed: {response.text}", "ERROR")
                    messagebox.showerror("Error", f"Sync failed: {response.text}")
            except Exception as e:
                self.log_message(f"Sync to online error: {str(e)}", "ERROR")
                messagebox.showerror("Error", f"Sync error: {str(e)}")
            finally:
                self.sync_in_progress = False
                self.sync_progress.stop()
                self.sync_status_label.config(text="Ready")
        
        threading.Thread(target=sync_thread, daemon=True).start()
    
    def sync_from_online(self):
        """Sync online data to local"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server must be running to sync data")
            return
        
        if self.sync_in_progress:
            messagebox.showwarning("Warning", "Sync operation already in progress")
            return
        
        def sync_thread():
            try:
                self.sync_in_progress = True
                self.sync_progress.start()
                self.sync_status_label.config(text="Pulling from online...")
                self.log_message("Starting sync from online...")
                
                response = requests.post(f"http://localhost:{self.server_port}/api/sync/from-online", timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    self.log_message(f"Sync from online completed: {result.get('message', 'Success')}", "SUCCESS")
                    self.last_sync_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    messagebox.showinfo("Success", "Data successfully pulled from online database!")
                else:
                    self.log_message(f"Sync from online failed: {response.text}", "ERROR")
                    messagebox.showerror("Error", f"Sync failed: {response.text}")
            except Exception as e:
                self.log_message(f"Sync from online error: {str(e)}", "ERROR")
                messagebox.showerror("Error", f"Sync error: {str(e)}")
            finally:
                self.sync_in_progress = False
                self.sync_progress.stop()
                self.sync_status_label.config(text="Ready")
        
        threading.Thread(target=sync_thread, daemon=True).start()
    
    def bidirectional_sync(self):
        """Perform bidirectional sync"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server must be running to sync data")
            return
        
        if self.sync_in_progress:
            messagebox.showwarning("Warning", "Sync operation already in progress")
            return
        
        def sync_thread():
            try:
                self.sync_in_progress = True
                self.sync_progress.start()
                self.sync_status_label.config(text="Bidirectional sync in progress...")
                self.log_message("Starting bidirectional sync...")
                
                response = requests.post(f"http://localhost:{self.server_port}/api/sync/bidirectional", timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    self.log_message(f"Bidirectional sync completed: {result.get('message', 'Success')}", "SUCCESS")
                    self.last_sync_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    messagebox.showinfo("Success", "Bidirectional sync completed successfully!")
                else:
                    self.log_message(f"Bidirectional sync failed: {response.text}", "ERROR")
                    messagebox.showerror("Error", f"Sync failed: {response.text}")
            except Exception as e:
                self.log_message(f"Bidirectional sync error: {str(e)}", "ERROR")
                messagebox.showerror("Error", f"Sync error: {str(e)}")
            finally:
                self.sync_in_progress = False
                self.sync_progress.stop()
                self.sync_status_label.config(text="Ready")
        
        threading.Thread(target=sync_thread, daemon=True).start()
    
    def check_sync_status(self):
        """Check sync status"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server must be running to check sync status")
            return
        
        def status_thread():
            try:
                self.log_message("Checking sync status...")
                response = requests.get(f"http://localhost:{self.server_port}/api/sync/status", timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    status_msg = (f"Local records: {result.get('local_records', 0)}\n"
                                f"Unsynced changes: {result.get('unsynced_changes', 0)}")
                    self.log_message(f"Sync status: {status_msg}")
                    messagebox.showinfo("Sync Status", status_msg)
                else:
                    self.log_message(f"Failed to get sync status: {response.text}", "ERROR")
            except Exception as e:
                self.log_message(f"Sync status error: {str(e)}", "ERROR")
        
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
