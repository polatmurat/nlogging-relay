import socket
import threading
import argparse
import time

# relay settings
RELAY_HOST = '127.0.0.1'
RELAY_PORT = 8889
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8888
BUFSIZE = 4096

class ChatRelay:
    def __init__(self, relay_host, relay_port, server_host, server_port):
        """Initialize the chat relay server"""
        self.relay_host = relay_host
        self.relay_port = relay_port
        self.server_host = server_host
        self.server_port = server_port
        self.clients = []
        self.relay_socket = None
        
    def start(self):
        """Start the relay server"""
        self.relay_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.relay_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.relay_socket.bind((self.relay_host, self.relay_port))
            self.relay_socket.listen(5)
            print(f"[Relay] Listening on {self.relay_host}:{self.relay_port}")
            print(f"[Relay] Forwarding to server at {self.server_host}:{self.server_port}")
            
            # stat printing thread
            stats_thread = threading.Thread(target=self.print_stats, daemon=True)
            stats_thread.start()
            
            # Accept incoming connections
            while True:
                client_socket, address = self.relay_socket.accept()
                print(f"[Relay] New client connection from {address}")
                
                # Start a new thread to handle this client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            print("[Relay] Shutting down...")
        finally:
            if self.relay_socket:
                self.relay_socket.close()
    
    def print_stats(self):
        """Periodically print relay statistics"""
        while True:
            time.sleep(10)  # Print stats every 10 seconds
            connected_clients = len(self.clients)
            print(f"[Relay Stats] Connected clients: {connected_clients}")
    
    def handle_client(self, client_socket, address):
        """Handle a client connection by relaying to the main server"""
        server_socket = None
        
        try:
            # Connect to the main server
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((self.server_host, self.server_port))
            
            # Add to clients list
            self.clients.append(client_socket)
            
            # handle the nickname exchange
            nickname_data = client_socket.recv(BUFSIZE)
            if not nickname_data:
                return
                
            # Add '*' prefix to the nickname
            nickname = nickname_data.decode('utf-8')
            modified_nickname = f"*{nickname}"
            print(f"[Relay] Modified nickname: {nickname} -> {modified_nickname}")
            
            server_socket.send(modified_nickname.encode('utf-8'))
            
            # server's response --->> client
            response = server_socket.recv(BUFSIZE)
            if response:
                client_socket.send(response)
            
            # bi-directional communication
            client_to_server = threading.Thread(
                target=self.relay_data,
                args=(client_socket, server_socket, "client to server"),
                daemon=True
            )
            
            server_to_client = threading.Thread(
                target=self.relay_data,
                args=(server_socket, client_socket, "server to client"),
                daemon=True
            )
            
            client_to_server.start()
            server_to_client.start()
            
            # Wait for both threads to complete
            client_to_server.join()
            server_to_client.join()
            
        except Exception as e:
            print(f"[Relay Error] {e}")
        finally:
            # Clean up
            if server_socket:
                try:
                    server_socket.close()
                except:
                    pass
                
            if client_socket in self.clients:
                self.clients.remove(client_socket)
                
            try:
                client_socket.close()
            except:
                pass
                
            print(f"[Relay] Client connection from {address} closed")
    
    def relay_data(self, source, destination, direction):
        """Relay data between source and destination sockets"""
        try:
            while True:
                data = source.recv(BUFSIZE)
                if not data:
                    break
                    
                destination.send(data)
        except:
            # socket closed
            pass

def main():
    parser = argparse.ArgumentParser(description='Chat Relay Server')
    parser.add_argument('--relay-host', dest="relay_host", default=RELAY_HOST, 
                        help=f'Relay host address (default: {RELAY_HOST})')
    parser.add_argument('--relay-port', dest="relay_port", type=int, default=RELAY_PORT, 
                        help=f'Relay port to listen on (default: {RELAY_PORT})')
    parser.add_argument('--server-host', dest="server_host", default=SERVER_HOST, 
                        help=f'Chat server host address (default: {SERVER_HOST})')
    parser.add_argument('--server-port', dest="server_port", type=int, default=SERVER_PORT, 
                        help=f'Chat server port (default: {SERVER_PORT})')
    args = parser.parse_args()
    
    relay = ChatRelay(args.relay_host, args.relay_port, args.server_host, args.server_port)
    relay.start()

if __name__ == "__main__":
    main()