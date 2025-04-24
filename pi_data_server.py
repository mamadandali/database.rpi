from flask import Flask, jsonify, request
import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database path - adjust this to match your Raspberry Pi's database location
DB_PATH = '/home/amin/Desktop/test.db'  # Updated to the correct path on Raspberry Pi

def get_db_connection():
    """Get a connection to SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize the database with contacts table"""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to initialize database")
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        conn.close()

@app.route('/contacts', methods=['GET'])
def get_all_contacts():
    """Get all contacts from the database"""
    logger.debug("Received GET request for all contacts")
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM contacts
        ORDER BY name ASC
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
        logger.error(f"Error retrieving contacts: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/contacts', methods=['POST'])
def add_contact():
    """Add a new contact"""
    logger.debug("Received POST request to add contact")
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({"status": "error", "message": "Name is required"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO contacts (name, email, phone)
        VALUES (?, ?, ?)
        """, (data['name'], data.get('email'), data.get('phone')))
        
        conn.commit()
        
        return jsonify({
            "status": "success",
            "message": "Contact added successfully",
            "id": cursor.lastrowid
        })
        
    except Exception as e:
        logger.error(f"Error adding contact: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/contacts/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Get a specific contact by ID"""
    logger.debug(f"Received GET request for contact ID: {contact_id}")
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM contacts
        WHERE id = ?
        """, (contact_id,))
        
        row = cursor.fetchone()
        if row:
            return jsonify({
                "status": "success",
                "data": dict(row)
            })
        else:
            return jsonify({"status": "error", "message": "Contact not found"}), 404
            
    except Exception as e:
        logger.error(f"Error retrieving contact: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Update a specific contact"""
    logger.debug(f"Received PUT request for contact ID: {contact_id}")
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE contacts
        SET name = ?, email = ?, phone = ?
        WHERE id = ?
        """, (data.get('name'), data.get('email'), data.get('phone'), contact_id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"status": "error", "message": "Contact not found"}), 404
            
        return jsonify({
            "status": "success",
            "message": "Contact updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating contact: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete a specific contact"""
    logger.debug(f"Received DELETE request for contact ID: {contact_id}")
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
    try:
        cursor = conn.cursor()
        cursor.execute("""
        DELETE FROM contacts
        WHERE id = ?
        """, (contact_id,))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"status": "error", "message": "Contact not found"}), 404
            
        return jsonify({
            "status": "success",
            "message": "Contact deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting contact: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Use the Raspberry Pi's IP address directly
    ip_address = '172.21.235.32'
    
    logger.info(f"Starting server on {ip_address}:5000")
    logger.info(f"Database path: {DB_PATH}")
    
    # Run the Flask app with debug mode
    app.run(host=ip_address, port=5000, debug=True) 