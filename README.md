# Sensor Data Database Server

A Flask-based server and client system for managing sensor data from multiple stations.

## Features

- SQLite database storage
- REST API endpoints for data access
- Real-time data display
- Data export to JSON
- Multi-device support

## Server Setup (Raspberry Pi)

1. Install dependencies:
```bash
pip install flask
```

2. Update the database path in `pi_data_server.py`:
```python
DB_PATH = '/path/to/your/test.db'
```

3. Run the server:
```bash
python pi_data_server.py
```

## Client Setup (Laptop)

1. Install dependencies:
```bash
pip install requests
```

2. Update the Raspberry Pi IP in `pi_data_client.py`:
```python
PI_IP = '192.168.1.100'  # Replace with your Raspberry Pi's IP
```

3. Run the client:
```bash
python pi_data_client.py
```

## API Endpoints

- `GET /api/data` - Get all data
- `GET /api/data/latest` - Get latest data from each device
- `GET /api/data/device/<device_id>` - Get data for a specific device

## Data Structure

Each data record contains:
- Device ID
- Device Name
- Timestamp
- Temperature (°C)
- Humidity (%)
- Pressure (hPa)
- Battery Level (%)
- Signal Strength 