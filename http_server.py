from flask import Flask, request, jsonify
import json
import socket
import platform
from datetime import datetime
import threading
import time
import sqlite3
import logging
from queue import Queue
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Rich console for pretty printing
console = Console()

app = Flask(__name__)

# Fixed port for the server
SERVER_PORT = 8080  # Using a common port that's usually open

# SQLite database file
DB_FILE = 'sensor_data.db'

# Create a queue for batch processing
data_queue = Queue()

def print_incoming_data(data):
    """Print incoming data in a formatted way"""
    # Create a table for sensor data
    sensor_table = Table(show_header=True, header_style="bold magenta")
    sensor_table.add_column("Sensor", style="cyan")
    sensor_table.add_column("Value", style="green")
    sensor_table.add_column("Unit", style="yellow")
    
    # Add sensor readings to the table
    for sensor, value in data['sensor_data'].items():
        unit = "°C" if sensor == "temperature" else "%" if sensor == "humidity" else "hPa"
        sensor_table.add_row(sensor.capitalize(), str(value), unit)
    
    # Create a table for device info
    device_table = Table(show_header=True, header_style="bold blue")
    device_table.add_column("Property", style="cyan")
    device_table.add_column("Value", style="green")
    
    # Add device information
    device_table.add_row("Device ID", data['device_id'])
    device_table.add_row("Device Name", data['device_name'])
    device_table.add_row("Location", data.get('location', 'N/A'))
    device_table.add_row("Battery Level", f"{data['battery_level']}%")
    device_table.add_row("Signal Strength", data['signal_strength'])
    device_table.add_row("Timestamp", data['timestamp'])
    
    # Print the data in panels
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold green]New Data Received[/bold green]\n"
        f"From: [bold cyan]{data['device_name']}[/bold cyan] "
        f"([bold yellow]{data['device_id']}[/bold yellow])",
        border_style="green"
    ))
    
    console.print(Panel.fit(device_table, title="[bold]Device Information[/bold]", border_style="blue"))
    console.print(Panel.fit(sensor_table, title="[bold]Sensor Readings[/bold]", border_style="magenta"))
    console.print("="*80 + "\n")

def get_db_connection():
    """Get a connection to SQLite database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to initialize database")
        return
        
    try:
        cursor = conn.cursor()
        
        # Create devices table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            device_name TEXT,
            first_seen DATETIME,
            last_seen DATETIME
        )
        """)
        
        # Create sensor_data table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp DATETIME,
            temperature REAL,
            humidity REAL,
            pressure REAL,
            battery_level INTEGER,
            signal_strength TEXT,
            FOREIGN KEY (device_id) REFERENCES devices(device_id)
        )
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        conn.close()

def process_data_queue():
    """Process the data queue in batches"""
    batch_size = 10
    batch = []
    
    while True:
        try:
            # Get data from queue with timeout
            data = data_queue.get(timeout=5)
            batch.append(data)
            
            # Process batch when it reaches the desired size
            if len(batch) >= batch_size:
                save_data_batch(batch)
                batch = []
        except:
            # Process remaining data if any
            if batch:
                save_data_batch(batch)
                batch = []
            time.sleep(1)

def save_data_batch(batch):
    """Save a batch of data to SQLite"""
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        for data in batch:
            # Update or insert device info
            cursor.execute("""
            INSERT OR REPLACE INTO devices 
            (device_id, device_name, first_seen, last_seen)
            VALUES (?, ?, COALESCE((SELECT first_seen FROM devices WHERE device_id = ?), ?), ?)
            """, (
                data['device_id'],
                data['device_name'],
                data['device_id'],
                data['timestamp'],
                data['timestamp']
            ))
            
            # Insert sensor data
            cursor.execute("""
            INSERT INTO sensor_data 
            (device_id, timestamp, temperature, humidity, pressure, battery_level, signal_strength)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data['device_id'],
                data['timestamp'],
                data['sensor_data']['temperature'],
                data['sensor_data']['humidity'],
                data['sensor_data']['pressure'],
                data['battery_level'],
                data['signal_strength']
            ))
        
        conn.commit()
        logger.info(f"Successfully saved batch of {len(batch)} records")
    except Exception as e:
        logger.error(f"Error saving batch: {e}")
    finally:
        conn.close()

def broadcast_server_presence():
    """Broadcast server presence on the network"""
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    while True:
        try:
            message = f"SERVER_PRESENCE:{socket.gethostname()}:{SERVER_PORT}"
            broadcast_socket.sendto(message.encode(), ('<broadcast>', 8081))
            time.sleep(5)  # Broadcast every 5 seconds
        except:
            pass

@app.route('/api/data', methods=['POST'])
def receive_data():
    try:
        # Get JSON data from the request
        data = request.get_json()
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        # Print the incoming data
        print_incoming_data(data)
        
        # Add to processing queue
        data_queue.put(data)
        
        # Return immediate response
        return jsonify({
            "status": "success",
            "message": "Data queued for processing"
        }), 202
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route('/api/data', methods=['GET'])
def get_all_data():
    """Endpoint to retrieve all received data"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Get latest data for each device
        cursor.execute("""
        SELECT d.device_id, d.device_name, s.timestamp, s.temperature, 
               s.humidity, s.pressure, s.battery_level, s.signal_strength
        FROM devices d
        JOIN sensor_data s ON d.device_id = s.device_id
        WHERE s.timestamp = (
            SELECT MAX(timestamp) 
            FROM sensor_data 
            WHERE device_id = d.device_id
        )
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
            
        return jsonify({
            "status": "success",
            "count": len(results),
            "data": results
        })
        
    except Exception as e:
        logger.error(f"Error retrieving data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Start data processing thread
    processing_thread = threading.Thread(target=process_data_queue, daemon=True)
    processing_thread.start()
    
    # Start broadcast thread
    broadcast_thread = threading.Thread(target=broadcast_server_presence, daemon=True)
    broadcast_thread.start()
    
    console.print(Panel.fit(
        "[bold green]Sensor Data Server[/bold green]\n"
        f"Running on port [cyan]{SERVER_PORT}[/cyan]\n"
        "Press [red]Ctrl+C[/red] to stop",
        border_style="green"
    ))
    
    # Run the Flask app with optimized settings for Raspberry Pi
    app.run(
        host='0.0.0.0',
        port=SERVER_PORT,
        debug=False,
        threaded=True,
        processes=1
    ) 