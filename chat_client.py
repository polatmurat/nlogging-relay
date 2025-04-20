import socket
import threading
import argparse
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

# Default settings
HOST = '127.0.0.1'
PORT = 8888
BUFSIZE = 4096

class ChatClient:
    def __init__(self, host, port, use_relay=False, relay_host=None, relay_port=None):
        """Initialize the chat client"""
        self.host = host
        self.port = port
        self.use_relay = use_relay
        self.relay_host = relay_host if relay_host else host
        self.relay_port = relay_port if relay_port else port + 1
        self.socket = None
        self.nickname = None
        self.private_windows = {}
        self.running = False
        self.receive_thread = None
        
    def connect(self):
        """Connect to the chat server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Connect to either the relay or directly to the server
            if self.use_relay:
                self.socket.connect((self.relay_host, self.relay_port))
                print(f"Connected to relay at {self.relay_host}:{self.relay_port}")
            else:
                self.socket.connect((self.host, self.port))
                print(f"Connected directly to server at {self.host}:{self.port}")
            
            self.socket.send(self.nickname.encode('utf-8'))
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from the server"""
        self.running = False
        if self.socket:
            try:
                self.socket.send("/exit".encode('utf-8'))
                self.socket.close()
            except:
                pass
        
    def send_message(self, message):
        """Send a message to the server"""
        if not message:
            return
            
        try:
            self.socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message: {e}")
            messagebox.showerror("Error", f"Failed to send message: {e}")
            self.disconnect()
            
    def receive_messages(self):
        """Receive messages from the server"""
        self.running = True
        while self.running:
            try:
                message = self.socket.recv(BUFSIZE).decode('utf-8')
                
                if not message:
                    # Server disconnected
                    break
                
                # user list updates
                if message.startswith("/users "):
                    users = message[7:].split(",")
                    self.update_user_list(users)
                
                # private messages
                elif "[Private]" in message:
                    # Extract sender from private message format: [time] [Private] sender: message
                    try:
                        parts = message.split(" ")
                        timestamp = parts[0][1:-1]  # Remove brackets
                        sender = parts[3][:-1]      # Remove colon
                        
                        # Check if it's a message TO someone
                        if "[Private to" in message:
                            recipient = parts[4][:-1]  # Remove bracket and colon
                            self.handle_private_message(recipient, message)
                        else:
                            # This is a message FROM someone
                            self.handle_private_message(sender, message)
                    except IndexError:
                        # If parsing fails, just display in main chat
                        self.display_message(message)
                
                else:
                    self.display_message(message)
                    
            except Exception as e:
                if self.running:
                    print(f"Error receiving message: {e}")
                    self.running = False
                    messagebox.showerror("Connection Lost", f"Lost connection to server: {e}")
                break
        
        # if exit, notify the user
        if self.running:
            messagebox.showinfo("Disconnected", "You have been disconnected from the server.")
            self.running = False
            
    def handle_private_message(self, user, message):
        """Handle incoming private messages by opening or using a private chat window"""
        if user not in self.private_windows:
            self.open_private_window(user)
        
        # Display the message in the private window
        self.private_windows[user].display_message(message)
        
    def update_user_list(self, users):
        """Update the user list in the GUI"""
        self.users_listbox.delete(0, tk.END)
        for user in users:
            self.users_listbox.insert(tk.END, user)
            
    def send_private_message(self, recipient, message):
        """Send a private message to a specific user"""
        private_cmd = f"/private {recipient} {message}"
        self.send_message(private_cmd)
        
    def start_gui(self):
        """Start the GUI interface"""
        self.root = tk.Tk()
        self.root.title(f"Chat Client - {self.nickname}")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.geometry("800x600")
        
        # Main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Split the main area into left and right panels
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = tk.Frame(main_frame, width=200)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        right_frame.pack_propagate(False)  # Prevent from shrinking
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Message entry
        self.message_entry = tk.Entry(left_frame)
        self.message_entry.pack(fill=tk.X, padx=5, pady=5)
        self.message_entry.bind("<Return>", self.on_send)
        
        # Send button
        send_button = tk.Button(left_frame, text="Send", command=self.on_send)
        send_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # User list label
        users_label = tk.Label(right_frame, text="Online Users:")
        users_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # User list with double-click binding
        self.users_listbox = tk.Listbox(right_frame)
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.users_listbox.bind("<Double-1>", self.on_user_double_click)
        
        # Exit button
        exit_button = tk.Button(right_frame, text="Exit", command=self.on_closing)
        exit_button.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=10)
        
        # Start receiving messages
        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()
        
        # Set the focus to the message entry
        self.message_entry.focus_set()
        
        # Start the GUI main loop
        self.root.mainloop()
        
    def display_message(self, message):
        """Display a message in the chat area"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.see(tk.END)  # Autoscroll to bottom
        self.chat_display.config(state=tk.DISABLED)
        
    def open_private_window(self, user):
        """Open a private chat window"""
        private_window = PrivateChatWindow(self, user)
        self.private_windows[user] = private_window
        
    def on_send(self, event=None):
        """Send the message when the Send button is clicked or Enter is pressed"""
        message = self.message_entry.get().strip()
        if message:
            self.send_message(message)
            self.message_entry.delete(0, tk.END)
        return "break"  # Prevent default Enter behavior
        
    def on_user_double_click(self, event=None):
        """Handle double click on a user to open private chat"""
        selection = self.users_listbox.curselection()
        if selection:
            user = self.users_listbox.get(selection[0])
            if user != self.nickname:  # Don't open chat with yourself
                self.open_private_window(user)
                
    def on_closing(self):
        """Handle window closing event"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.disconnect()
            self.root.destroy()
            
class PrivateChatWindow:
    def __init__(self, client, recipient):
        """Initialize a private chat window"""
        self.client = client
        self.recipient = recipient
        self.window = tk.Toplevel(client.root)
        self.window.title(f"Private Chat with {recipient}")
        self.window.geometry("500x400")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bottom frame for entry and send button
        bottom_frame = tk.Frame(self.window)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Message entry
        self.message_entry = tk.Entry(bottom_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", self.on_send)
        self.message_entry.focus_set()
        
        # Send button
        send_button = tk.Button(bottom_frame, text="Send", command=self.on_send)
        send_button.pack(side=tk.RIGHT, padx=5)
        
    def display_message(self, message):
        """Display a message in the private chat window"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.see(tk.END)  # Autoscroll to bottom
        self.chat_display.config(state=tk.DISABLED)
        
        # Bring window to front
        self.window.lift()
        
    def on_send(self, event=None):
        """Send a private message"""
        message = self.message_entry.get().strip()
        if message:
            self.client.send_private_message(self.recipient, message)
            self.message_entry.delete(0, tk.END)
        return "break"  # Prevent default Enter behavior
        
    def on_closing(self):
        """Handle window closing"""
        if self.recipient in self.client.private_windows:
            del self.client.private_windows[self.recipient]
        self.window.destroy()

def main():
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('--host', dest="host", default=HOST, help=f'Server host address (default: {HOST})')
    parser.add_argument('--port', dest="port", type=int, default=PORT, help=f'Server port (default: {PORT})')
    parser.add_argument('--relay', dest="use_relay", action='store_true', help='Connect via relay server')
    parser.add_argument('--relay-host', dest="relay_host", help='Relay server host (default: same as server)')
    parser.add_argument('--relay-port', dest="relay_port", type=int, help='Relay server port (default: server port + 1)')
    args = parser.parse_args()
    
    # Use a dialog to get the nickname
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    nickname = simpledialog.askstring("Nickname", "Enter your nickname:", parent=root)
    if not nickname:
        print("Nickname is required. Exiting.")
        return
    
    client = ChatClient(
        args.host, 
        args.port, 
        args.use_relay, 
        args.relay_host, 
        args.relay_port
    )
    client.nickname = nickname
    
    if client.connect():
        # Destroy the temporary root
        root.destroy()
        
        # main GUI
        client.start_gui()
    else:
        messagebox.showerror("Connection Error", "Failed to connect to the server.")
        root.destroy()

if __name__ == "__main__":
    main()