# Multi-User Chat System

This project implements a multi-user chat system composed of three components:
1. A Chat Server that manages connections and messages
2. A Chat Client with GUI interface for user interaction
3. An optional Chat Relay that prefixes nicknames with '*'

## Components

### 1. Chat Server (`chat_server.py`)

The server component handles:
- Client connections and nickname management
- Public message broadcasting
- Private messaging between users
- Message logging to CSV file
- Rate limiting to prevent spam
- Performance monitoring and statistics

### 2. Chat Client (`chat_client.py`)

The client component provides:
- User-friendly GUI interface
- Public chat messages in main window
- Private messaging in separate windows
- Display of connected users
- Support for direct server connection or relay connection

### 3. Chat Relay (`chat_relay.py`)

The optional relay component:
- Acts as a proxy between clients and the main server
- Automatically prefixes client nicknames with '*'
- Forwards all communication transparently

### 4. Launcher (`runner.py`)

The launcher provides an easy way to start all components:
- Start the server with custom host/port
- Start the relay with custom settings
- Launch clients connected directly or via relay

## Requirements

- Python 3.x
- Standard libraries:
  - `socket`, `threading`, `time`, `datetime`, `csv`
  - `tkinter` for GUI components
  - `argparse` for command-line parsing

No external dependencies are required.

## How to Run

### Using the Launcher

The easiest way to run the system is using the launcher:

```
python runner.py
```

This will open a GUI where you can:
1. Configure server and relay addresses/ports
2. Start the server and/or relay
3. Launch clients (direct or via relay)

### Running Components Individually

You can also run each component separately:

**Start the Server:**
```
python chat_server.py [--host HOST] [--port PORT]
```

**Start the Relay:**
```
python chat_relay.py [--relay-host HOST] [--relay-port PORT] [--server-host HOST] [--server-port PORT]
```

**Start a Client:**
```
python chat_client.py [--host HOST] [--port PORT] [--relay] [--relay-host HOST] [--relay-port PORT]
```

## Features

### Nickname Management
- Each user must have a unique nickname
- If a requested nickname is already in use, a random alternative is assigned
- Nicknames with '*' are reserved for relay clients

### Public and Private Messaging
- All public messages are broadcast to all connected users
- Private messages are sent only to the specified recipient
- Private chat windows open automatically for private conversations

### Relay Functionality
- Clients can connect through a relay server
- The relay prefixes nicknames with '*' for identification
- All traffic is passed through transparently

### Logging and Statistics
- The server logs all messages (public and private) with timestamps
- Statistics are displayed periodically (connected clients, processed messages)

### Rate Limiting
- Prevents message spam by limiting how quickly users can send messages
- Users exceeding the limit receive warnings

### Error Handling
- Graceful handling of connection issues
- Clean disconnection when clients exit

## Implementation Details

### Threading Model
- The server uses threading to handle multiple concurrent clients
- Each client connection runs in its own thread
- The GUI clients use a separate thread for receiving messages

### Socket Programming
- Uses TCP sockets for reliable message delivery
- Custom protocol for nickname registration and messaging

### GUI Interface
- Built with Tkinter for cross-platform compatibility
- Main chat window with message history
- Separate private chat windows
- User list with double-click to open private chats

## Testing

To test the system:
1. Start the server
2. Start multiple clients
3. Test public messaging
4. Test private messaging by double-clicking on usernames
5. Test the relay functionality by connecting clients through it
6. Verify that relay client nicknames are prefixed with '*'
7. Test rate limiting by sending messages very quickly

## License

This project is provided for educational purposes.