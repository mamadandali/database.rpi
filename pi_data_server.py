from flask import Flask, jsonify
import sqlite3
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database path - adjust this to match your Raspberry Pi's database location
DB_PATH = '/path/to/your/test.db'  # You'll need to update this path

def get_db_connection():
    """Get a connection to SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

@app.route('/api/data', methods=['GET'])
def get_all_data():
    """Get all data from the database"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Get all data from contacts table
        cursor.execute("""
        SELECT * FROM contacts
        ORDER BY timestamp DESC
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

@app.route('/api/data/latest', methods=['GET'])
def get_latest_data():
    """Get latest data from each device"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
    try:
        cursor = conn.cursor()
        
        # Get latest data for each device
        cursor.execute("""
        SELECT device_id, MAX(timestamp) as latest_timestamp
        FROM contacts
        GROUP BY device_id
        """)
        
        latest_timestamps = cursor.fetchall()
        results = []
        
        for device in latest_timestamps:
            cursor.execute("""
            SELECT * FROM contacts
            WHERE device_id = ? AND timestamp = ?
            """, (device['device_id'], device['latest_timestamp']))
            
            row = cursor.fetchone()
            if row:
                results.append(dict(row))
            
        return jsonify({
            "status": "success",
            "count": len(results),
            "data": results
        })
        
    except Exception as e:
        logger.error(f"Error retrieving latest data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/data/device/<device_id>', methods=['GET'])
def get_device_data(device_id):
    """Get all data for a specific device"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM contacts
        WHERE device_id = ?
        ORDER BY timestamp DESC
        """, (device_id,))
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
            
        return jsonify({
            "status": "success",
            "count": len(results),
            "data": results
        })
        
    except Exception as e:
        logger.error(f"Error retrieving device data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # Make sure the database exists
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}")
        exit(1)
        
    # Get the Raspberry Pi's IP address
    import socket
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    
    logger.info(f"Starting server on {ip_address}:5000")
    logger.info(f"Database path: {DB_PATH}")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000) 