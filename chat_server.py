import socket
import threading
import time
import argparse
import csv
import random
import string
from datetime import datetime

HOST = '127.0.0.1'
PORT = 8888
BUFSIZE = 4096

# Rate limiting 
MAX_MESSAGES = 5
TIME_WINDOW = 3
LOG_FILE = "chat_server_log.csv"

class ChatServer:
    def __init__(self, host, port):
        """Initialize the chat server with the given host and port"""
        self.host = host
        self.port = port
        self.clients = {}
        self.nicknames = {}
        self.message_count = 0
        self.rate_limits = {}
        self.lock = threading.Lock()

    def start(self):
        """Start the chat server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"[Server] Listening on {self.host}:{self.port}")
            
            # monitoring thread
            stats_thread = threading.Thread(target=self.print_stats, daemon=True)
            stats_thread.start()
            
            # log file
            self.init_log_file()
            
            # incoming connections
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"[Server] New connection from {address}")
                
                # Start a new thread to handle this client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            print("[Server] Shutting down...")
        finally:
            self.server_socket.close()
    
    def init_log_file(self):
        """Initialize the log file with headers"""
        with open(LOG_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Sender', 'Recipient', 'Message', 'Type'])
    
    def log_message(self, sender, recipient, message, msg_type="public"):
        """Log messages to the CSV file"""
        """I got help from a LLM to write that definition called logging..."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, sender, recipient, message, msg_type])
    
    def print_stats(self):
        """Periodically print server statistics"""
        while True:
            time.sleep(10)  # Print stats every 10 seconds
            with self.lock:
                connected_clients = len(self.clients)
                total_messages = self.message_count
            
            print(f"[Stats] Connected clients: {connected_clients}, Messages processed: {total_messages}")
    
    def handle_client(self, client_socket, address):
        """Handle communication with a client"""
        #client's nickname
        try:
            nickname_data = client_socket.recv(BUFSIZE).decode('utf-8')
            requested_nickname = nickname_data.strip()
            
            # we should '*' (reserve this for relay)
            if '*' in requested_nickname:
                client_socket.send("Nickname cannot contain '*'. Please try again.".encode('utf-8'))
                client_socket.close()
                return
            
            # unique nickname
            with self.lock:
                if requested_nickname in self.nicknames:
                    # Generate a random nickname
                    random_suffix = ''.join(random.choices(string.digits, k=3))
                    assigned_nickname = f"User{random_suffix}"
                    client_socket.send(f"Nickname '{requested_nickname}' is taken. You've been assigned '{assigned_nickname}'".encode('utf-8'))
                    nickname = assigned_nickname
                else:
                    client_socket.send(f"Welcome, {requested_nickname}!".encode('utf-8'))
                    nickname = requested_nickname
                
                self.clients[client_socket] = nickname
                self.nicknames[nickname] = client_socket
                
                # rate limiting for this client
                self.rate_limits[client_socket] = {"count": 0, "timestamp": time.time()}
            
            # Broadcast that a new client has joined
            join_message = f"[{datetime.now().strftime('%H:%M:%S')}] {nickname} has joined the chat!"
            self.broadcast(join_message, None)
            
            # Update clients
            self.send_user_list()
            
            while True:
                message_data = client_socket.recv(BUFSIZE).decode('utf-8')
                
                if not message_data:
                    break
                
                if message_data.startswith("/private"):
                    # Handle private message: /private nickname message
                    parts = message_data[9:].split(" ", 1)
                    if len(parts) == 2:
                        target_nick, private_msg = parts
                        self.private_message(nickname, target_nick, private_msg)
                elif message_data == "/exit":
                    # Handle client exit
                    break
                else:
                    # rate limiting
                    if self.check_rate_limit(client_socket):
                        # Public message
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        formatted_message = f"[{timestamp}] {nickname}: {message_data}"
                        self.broadcast(formatted_message, client_socket)
                        
                        # Log the message
                        self.log_message(nickname, "ALL", message_data)
                        
                        # Update message count
                        with self.lock:
                            self.message_count += 1
                    else:
                        # Rate limit exceeded
                        warning = f"You're sending messages too quickly. Please slow down."
                        client_socket.send(warning.encode('utf-8'))
                        
        except Exception as e:
            print(f"[Error] {e}")
        finally:
            # Client disconnected, clean up
            with self.lock:
                if client_socket in self.clients:
                    left_nickname = self.clients[client_socket]
                    del self.nicknames[left_nickname]
                    del self.clients[client_socket]
                    del self.rate_limits[client_socket]
                    
                    # Broadcast that the client has left
                    # I got help a LLM to write that exit message again..
                    leave_message = f"[{datetime.now().strftime('%H:%M:%S')}] {left_nickname} has left the chat!"
                    self.broadcast(leave_message, None)
                    
                    self.send_user_list()
            
            client_socket.close()
    
    def check_rate_limit(self, client_socket):
        """Check if a client is sending messages too quickly"""
        with self.lock:
            current_time = time.time()
            client_stats = self.rate_limits[client_socket]
            
            # Reset counter if time window has passed
            if current_time - client_stats["timestamp"] > TIME_WINDOW:
                client_stats["count"] = 1
                client_stats["timestamp"] = current_time
                return True
            else:
                client_stats["count"] += 1
                
                # Check if rate limit is exceeded
                if client_stats["count"] > MAX_MESSAGES:
                    return False
                return True
    
    def broadcast(self, message, sender_socket):
        """Send a message to all connected clients except the sender"""
        with self.lock:
            for client in self.clients:
                # Don't send the message back to the sender
                if client != sender_socket:
                    try:
                        client.send(message.encode('utf-8'))
                    except:
                        # If there's an issue with the client socket, we'll handle it in the client thread
                        pass
    
    def private_message(self, sender, recipient, message):
        """Send a private message to a specific client"""
        with self.lock:
            if recipient in self.nicknames:
                target_socket = self.nicknames[recipient]
                timestamp = datetime.now().strftime('%H:%M:%S')
                formatted_message = f"[{timestamp}] [Private] {sender}: {message}"
                
                try:
                    target_socket.send(formatted_message.encode('utf-8'))
                    
                    # confirmation
                    sender_socket = self.nicknames[sender]
                    confirm_message = f"[{timestamp}] [Private to {recipient}]: {message}"
                    sender_socket.send(confirm_message.encode('utf-8'))
                    
                    # Log the private message
                    self.log_message(sender, recipient, message, "private")
                    
                    # Update message count
                    with self.lock:
                        self.message_count += 1
                except:
                    # If there's an issue with the client socket, we'll handle it in the client thread
                    pass
            else:
                # Recipient not found
                sender_socket = self.nicknames[sender]
                error_message = f"User '{recipient}' not found or offline."
                sender_socket.send(error_message.encode('utf-8'))
    
    def send_user_list(self):
        """Send the updated user list to all clients"""
        with self.lock:
            user_list = "/users " + ",".join(self.nicknames.keys())
            for client in self.clients:
                try:
                    client.send(user_list.encode('utf-8'))
                except:
                    # If there's an issue with the client socket, we'll handle it in the client thread
                    pass

def main():
    parser = argparse.ArgumentParser(description='Chat Server')
    parser.add_argument('--host', dest="host", default=HOST, help=f'Host address (default: {HOST})')
    parser.add_argument('--port', dest="port", type=int, default=PORT, help=f'Port to listen on (default: {PORT})')
    args = parser.parse_args()
    
    server = ChatServer(args.host, args.port)
    server.start()

if __name__ == "__main__":
    main()