import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

class ChatLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Launcher")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # style
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", font=('Arial', 10))
        style.configure("TLabel", font=('Arial', 11))
        style.configure("Header.TLabel", font=('Arial', 12, 'bold'))
        
        # Main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Multi-user Chat System", style="Header.TLabel")
        title_label.pack(pady=10)
        
        # Server settings frame
        server_frame = ttk.LabelFrame(main_frame, text="Server Settings")
        server_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Server host and port
        ttk.Label(server_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.server_host = tk.StringVar(value="127.0.0.1")
        ttk.Entry(server_frame, textvariable=self.server_host, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(server_frame, text="Port:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.server_port = tk.StringVar(value="8888")
        ttk.Entry(server_frame, textvariable=self.server_port, width=6).grid(row=0, column=3, padx=5, pady=5)
        
        # Relay settings frame
        relay_frame = ttk.LabelFrame(main_frame, text="Relay Settings")
        relay_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Relay host and port
        ttk.Label(relay_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.relay_host = tk.StringVar(value="127.0.0.1")
        ttk.Entry(relay_frame, textvariable=self.relay_host, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(relay_frame, text="Port:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.relay_port = tk.StringVar(value="8889")
        ttk.Entry(relay_frame, textvariable=self.relay_port, width=6).grid(row=0, column=3, padx=5, pady=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Start server button
        server_button = ttk.Button(buttons_frame, text="Start Server", command=self.start_server)
        server_button.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        
        # Start relay button
        relay_button = ttk.Button(buttons_frame, text="Start Relay", command=self.start_relay)
        relay_button.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        
        # Client frame
        client_frame = ttk.Frame(main_frame)
        client_frame.pack(fill=tk.X, pady=10)
        
        # Start client buttons
        direct_client_button = ttk.Button(client_frame, text="Start Direct Client", command=self.start_direct_client)
        direct_client_button.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        
        relay_client_button = ttk.Button(client_frame, text="Start Relay Client", command=self.start_relay_client)
        relay_client_button.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to launch components")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Exit button
        exit_button = ttk.Button(status_frame, text="Exit", command=self.root.destroy)
        exit_button.pack(side=tk.RIGHT, padx=5)
        
        # Processes dictionary to track running processes
        self.processes = {
            "server": None,
            "relay": None
        }
    
    def start_server(self):
        """Start the chat server"""
        server_host = self.server_host.get()
        server_port = self.server_port.get()
        
        try:
            # Kill existing server process if running
            if self.processes["server"] and self.processes["server"].poll() is None:
                self.processes["server"].terminate()
                self.processes["server"] = None
            
            # Start new server process
            cmd = [sys.executable, "chat_server.py", "--host", server_host, "--port", server_port]
            self.processes["server"] = subprocess.Popen(cmd)
            
            self.status_var.set(f"Server started on {server_host}:{server_port}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
    
    def start_relay(self):
        """Start the chat relay server"""
        server_host = self.server_host.get()
        server_port = self.server_port.get()
        relay_host = self.relay_host.get()
        relay_port = self.relay_port.get()
        
        try:
            # Kill existing relay process if running
            if self.processes["relay"] and self.processes["relay"].poll() is None:
                self.processes["relay"].terminate()
                self.processes["relay"] = None
            
            # Start new relay process
            cmd = [sys.executable, "chat_relay.py", 
                   "--relay-host", relay_host, 
                   "--relay-port", relay_port,
                   "--server-host", server_host,
                   "--server-port", server_port]
            self.processes["relay"] = subprocess.Popen(cmd)
            
            self.status_var.set(f"Relay started on {relay_host}:{relay_port}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start relay: {e}")
    
    def start_direct_client(self):
        """Start a client connected directly to the server"""
        server_host = self.server_host.get()
        server_port = self.server_port.get()
        
        try:
            # Start client process (not tracking it)
            cmd = [sys.executable, "chat_client.py", 
                   "--host", server_host, 
                   "--port", server_port]
            subprocess.Popen(cmd)
            
            self.status_var.set(f"Direct client connecting to {server_host}:{server_port}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start client: {e}")
    
    def start_relay_client(self):
        """Start a client connected via the relay"""
        relay_host = self.relay_host.get()
        relay_port = self.relay_port.get()
        
        try:
            # Start client process with relay option (not tracking it)
            cmd = [sys.executable, "chat_client.py", 
                   "--host", relay_host, 
                   "--port", relay_port,
                   "--relay"]
            subprocess.Popen(cmd)
            
            self.status_var.set(f"Relay client connecting to {relay_host}:{relay_port}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start client: {e}")
    
    def on_closing(self):
        """Handle window close event"""
        # Kill all child processes
        for process_name, process in self.processes.items():
            if process and process.poll() is None:
                try:
                    process.terminate()
                except:
                    pass
        
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ChatLauncher(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()