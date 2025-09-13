# Senatrack Backend - SQLite Database System

A FastAPI-based backend system with SQLite database support and synchronization capabilities between local and server instances.

## Features

### 🚀 Core Features
- **SQLite Database**: Fast and reliable local database storage
- **Server Sync**: Synchronize data between local and server SQLite databases
- **Local Server Launcher**: GUI application for easy local server management
- **Network Sharing**: Share local API over WiFi for team access
- **Executable Distribution**: Create standalone executables for easy deployment

### 🗄️ Database Architecture
- **Local SQLite**: Primary database for local operations
- **Server SQLite**: Server-side database for centralized data
- **Sync Capabilities**: Bidirectional synchronization between instances

### 🔄 Synchronization
- **Sync to Server**: Push local changes to server database
- **Sync from Server**: Pull server data to local database
- **Bidirectional Sync**: Two-way synchronization
- **Force Sync**: Overwrite local with server data
- **Sync Status**: Monitor sync progress and conflicts

## Installation

### Prerequisites
- Python 3.8+
- SQLite (included with Python)

### Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. The SQLite database will be created automatically on first run

## Usage

### 1. Local Server Launcher (GUI)
Run the GUI launcher for easy server management:
```bash
python launcher.py
```

**Features:**
- Start/stop local server
- Configure server port
- Network access information
- Sync controls
- Real-time server logs

### 2. Command Line Server

#### Activate Virtual Environment and Start Server
```bash
# Activate virtual environment
& ".venv/Scripts/Activate.ps1"

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start the FastAPI server directly from backend root
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Alternative: Navigate to App Directory
```bash
# From the backend root directory
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. API Endpoints

#### User Management
- `GET /users` - Get all users
- `GET /users/{user_id}` - Get user by ID
- `GET /users/count` - Get user count

#### Synchronization
- `GET /api/sync/status` - Get sync status
- `POST /api/sync/to-server` - Sync local to server
- `POST /api/sync/from-server` - Sync server to local
- `POST /api/sync/bidirectional` - Bidirectional sync
- `POST /api/sync/force` - Force sync all data

## Network Sharing

The local server runs on `0.0.0.0` by default, allowing access from other devices on the same network:

- **Local Access**: `http://localhost:8000`
- **Network Access**: `http://[YOUR_IP]:8000`
- **API Documentation**: `http://[YOUR_IP]:8000/docs`

## Building Executable

Create a standalone executable for easy distribution:

```bash
python build_executable.py
```

This will create:
- `dist/SenatrackLauncher.exe` - Standalone executable
- `install.bat` - Installation script
- `SenatrackPortable/` - Portable package

## Architecture

### Database Layer
```
Database (SQLite)
├── User Model (SQLAlchemy)
├── SyncLog Model (SQLAlchemy)
└── Database Operations (CRUD + Sync)
```

### Sync Service
- Tracks changes in local database
- Handles conflict resolution
- Provides sync status monitoring
- Supports bidirectional synchronization between SQLite instances

### Local Server Launcher
- GUI built with tkinter
- Server process management
- Network configuration
- Sync controls
- Real-time logging

## Configuration

### Environment Variables
Create a `.env` file:
```env
LOCAL_DB_PATH=local_data.db
SERVER_DB_PATH=server_data.db
RESEND_API_KEY=your-resend-key
```

### Settings
Key settings in `app/core/settings.py`:
- `LOCAL_DB_PATH`: Path to local SQLite database
- `SERVER_DB_PATH`: Path to server SQLite database
- `DEFAULT_HOST`: Server host (0.0.0.0 for network access)
- `DEFAULT_PORT`: Server port

## Use Cases

### 1. Development
- Use local SQLite for development
- Sync with server for testing

### 2. Offline Operations
- Field work without internet
- Local data collection
- Sync when connection available

### 3. Team Collaboration
- Local server for team access
- Shared network database
- Centralized sync management

### 4. Production Deployment
- Server SQLite for production
- Local SQLite for backup/disaster recovery

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check SQLite database file permissions
   - Verify database file path in settings
   - Ensure database directory exists

2. **Port Already in Use**
   - Change port in launcher
   - Kill existing processes

3. **Sync Failures**
   - Check server connectivity
   - Verify server database permissions
   - Review sync logs

4. **Network Access Issues**
   - Check firewall settings
   - Verify IP address
   - Ensure server is running on 0.0.0.0

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue on GitHub
- Visit: https://api.senatrack.app
- Check the documentation at `/docs` endpoint

