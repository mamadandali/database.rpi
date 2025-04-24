from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import socket
import threading
import json
from models.calb import calibrate_sensors
from models.food import recommend_food
from models.prob import model as prob_model, scaler as prob_scaler
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ESP32 Configuration
ESP32_HOST = '0.0.0.0'  # Listen on all interfaces
ESP32_PORT = 8080       # Port for ESP32 data
ESP32_BUFFER_SIZE = 1024

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/mousetrap.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    stations = db.relationship('Station', backref='group', lazy=True)

class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    sensor_data = db.relationship('SensorData', backref='station', lazy=True)
    last_triggered = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    external_id = db.Column(db.String(100))  # ID from external system

class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)
    mouse_present = db.Column(db.Integer)
    mouse_weight = db.Column(db.Float)
    bait1_touched = db.Column(db.Integer)
    bait2_touched = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    trap_triggered = db.Column(db.Boolean, default=False)
    external_timestamp = db.Column(db.DateTime)  # Timestamp from external system

# Store active notifications
active_notifications = {}

def esp32_listener():
    """Continuously listen for data from ESP32 devices"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((ESP32_HOST, ESP32_PORT))
        sock.listen(5)
        print(f"ESP32 listener started on {ESP32_HOST}:{ESP32_PORT}")
        
        while True:
            try:
                client_socket, address = sock.accept()
                print(f"ESP32 connected from {address}")
                
                # Start a new thread for each ESP32 connection
                threading.Thread(
                    target=handle_esp32_connection,
                    args=(client_socket, address),
                    daemon=True
                ).start()
                
            except Exception as e:
                print(f"Error accepting ESP32 connection: {str(e)}")
                continue
                
    except Exception as e:
        print(f"ESP32 listener error: {str(e)}")
    finally:
        sock.close()

def handle_esp32_connection(client_socket, address):
    """Handle data from a single ESP32 connection"""
    try:
        while True:
            data = client_socket.recv(ESP32_BUFFER_SIZE)
            if not data:
                break
                
            try:
                # Parse JSON data from ESP32
                esp_data = json.loads(data.decode('utf-8'))
                
                # Process the data
                with app.app_context():
                    process_esp32_data(esp_data)
                    
            except json.JSONDecodeError:
                print(f"Invalid JSON data from {address}")
            except Exception as e:
                print(f"Error processing ESP32 data: {str(e)}")
                
    except Exception as e:
        print(f"Error handling ESP32 connection: {str(e)}")
    finally:
        client_socket.close()
        print(f"ESP32 disconnected from {address}")

def process_esp32_data(data):
    """Process data received from ESP32"""
    try:
        # Get or create group and station
        group = Group.query.filter_by(name=data['group_name']).first()
        if not group:
            group = Group(name=data['group_name'])
            db.session.add(group)
            db.session.commit()
        
        station = Station.query.filter_by(external_id=data['station_id']).first()
        if not station:
            station = Station(
                name=data['station_name'],
                group_id=group.id,
                external_id=data['station_id']
            )
            db.session.add(station)
            db.session.commit()
        
        # Create sensor data entry
        sensor_data = SensorData(
            station_id=station.id,
            mouse_present=data['mouse_present'],
            mouse_weight=data['mouse_weight'],
            bait1_touched=data['bait1_touched'],
            bait2_touched=data['bait2_touched'],
            temperature=data['temperature'],
            humidity=data['humidity'],
            trap_triggered=data['mouse_present'] == 1 or data['bait1_touched'] == 1 or data['bait2_touched'] == 1,
            external_timestamp=datetime.utcnow()  # ESP32 data is real-time
        )
        db.session.add(sensor_data)
        
        # Update station's last triggered time if trap was triggered
        if sensor_data.trap_triggered:
            station.last_triggered = datetime.utcnow()
            # Store notification
            notification_key = f"{group.name}_{station.name}"
            active_notifications[notification_key] = {
                "group": group.name,
                "station": station.name,
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "mouse_present": data['mouse_present'],
                    "bait1_touched": data['bait1_touched'],
                    "bait2_touched": data['bait2_touched']
                }
            }
        
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error processing ESP32 data: {str(e)}")
        return False

@app.route('/external_data', methods=['POST'])
def receive_external_data():
    """Endpoint to receive data from external system"""
    data = request.json
    
    # Validate required fields
    required_fields = ['group_name', 'station_id', 'station_name', 'mouse_present', 
                      'mouse_weight', 'bait1_touched', 'bait2_touched', 
                      'temperature', 'humidity', 'timestamp']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    if process_external_data(data):
        return jsonify({"status": "success", "message": "Data processed successfully"})
    else:
        return jsonify({"error": "Failed to process data"}), 500

@app.route('/upload', methods=['POST'])
def upload_data():
    data = request.json
    
    # Validate required fields
    required_fields = ['group_name', 'station_name', 'mouse_present', 'mouse_weight', 
                      'bait1_touched', 'bait2_touched', 'temperature', 'humidity']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Get or create group and station
    group = Group.query.filter_by(name=data['group_name']).first()
    if not group:
        group = Group(name=data['group_name'])
        db.session.add(group)
        db.session.commit()
    
    station = Station.query.filter_by(name=data['station_name'], group_id=group.id).first()
    if not station:
        station = Station(name=data['station_name'], group_id=group.id)
        db.session.add(station)
        db.session.commit()
    
    # Check if trap was triggered
    trap_triggered = data['mouse_present'] == 1 or data['bait1_touched'] == 1 or data['bait2_touched'] == 1
    
    # Store sensor data
    sensor_data = SensorData(
        station_id=station.id,
        mouse_present=data['mouse_present'],
        mouse_weight=data['mouse_weight'],
        bait1_touched=data['bait1_touched'],
        bait2_touched=data['bait2_touched'],
        temperature=data['temperature'],
        humidity=data['humidity'],
        trap_triggered=trap_triggered
    )
    db.session.add(sensor_data)
    
    # Update station's last triggered time if trap was triggered
    if trap_triggered:
        station.last_triggered = datetime.utcnow()
        # Store notification
        notification_key = f"{group.name}_{station.name}"
        active_notifications[notification_key] = {
            "group": group.name,
            "station": station.name,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "mouse_present": data['mouse_present'],
                "bait1_touched": data['bait1_touched'],
                "bait2_touched": data['bait2_touched']
            }
        }
    
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Data uploaded successfully"
    })

@app.route('/calibrate', methods=['POST'])
def calibrate():
    data = request.json
    temperatures = data.get('temperatures', [])
    threshold = data.get('threshold', 5.0)
    
    def calibration_callback(sensor_id):
        print(f"Calibrating sensor {sensor_id}")
    
    calibrate_sensors(temperatures, threshold, calibration_callback)
    return jsonify({"status": "calibration_complete"})

@app.route('/recommend_food', methods=['POST'])
def get_food_recommendation():
    data = request.json
    recommended_food = recommend_food(
        weight=data['weight'],
        damage=data['damage'],
        temperature=data['temperature'],
        humidity=data['humidity']
    )
    return jsonify({"recommended_food": recommended_food})

@app.route('/group_probability/<group_name>', methods=['GET'])
def get_group_probability(group_name):
    group = Group.query.filter_by(name=group_name).first()
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    # Get latest temperature and humidity for the group
    latest_data = SensorData.query.join(Station).filter(
        Station.group_id == group.id
    ).order_by(SensorData.timestamp.desc()).first()
    
    if not latest_data:
        return jsonify({"error": "No data available"}), 404
    
    # Prepare data for probability model
    new_data = np.array([[latest_data.temperature, latest_data.humidity]])
    new_data_scaled = prob_scaler.transform(new_data)
    probability = prob_model.predict_proba(new_data_scaled)[0][1]
    
    return jsonify({
        "group": group_name,
        "probability": float(probability),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/groups', methods=['GET'])
def get_groups():
    groups = Group.query.all()
    return jsonify([{
        "id": group.id,
        "name": group.name,
        "stations": [{
            "id": station.id,
            "name": station.name,
            "last_triggered": station.last_triggered.isoformat() if station.last_triggered else None,
            "is_active": station.is_active
        } for station in group.stations]
    } for group in groups])

@app.route('/notifications', methods=['GET'])
def get_notifications():
    return jsonify(list(active_notifications.values()))

@app.route('/notifications/<group_name>/<station_name>', methods=['DELETE'])
def clear_notification(group_name, station_name):
    notification_key = f"{group_name}_{station_name}"
    if notification_key in active_notifications:
        del active_notifications[notification_key]
        return jsonify({"status": "success"})
    return jsonify({"error": "Notification not found"}), 404

if __name__ == '__main__':
    os.makedirs('database', exist_ok=True)
    
    # Start ESP32 listener in a separate thread
    esp32_thread = threading.Thread(target=esp32_listener, daemon=True)
    esp32_thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=True) 