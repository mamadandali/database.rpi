from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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

# API Endpoints
def cleanup_old_data():
    """Delete sensor data older than 3 months"""
    three_months_ago = datetime.utcnow() - timedelta(days=90)
    try:
        # Delete old sensor data
        old_data = SensorData.query.filter(SensorData.timestamp < three_months_ago).all()
        for data in old_data:
            db.session.delete(data)
        db.session.commit()
        print(f"Cleaned up {len(old_data)} old records")
    except Exception as e:
        print(f"Error cleaning up old data: {str(e)}")
        db.session.rollback()

@app.route('/api/data', methods=['POST'])
def receive_data():
    """Endpoint to receive data from external systems"""
    data = request.json
    
    # Validate required fields
    required_fields = ['group_name', 'station_name', 'mouse_present', 'mouse_weight', 
                      'bait1_touched', 'bait2_touched', 'temperature', 'humidity']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Clean up old data before processing new data
        cleanup_old_data()
        
        # Get or create group
        group = Group.query.filter_by(name=data['group_name']).first()
        if not group:
            group = Group(name=data['group_name'])
            db.session.add(group)
            db.session.commit()
        
        # Get or create station
        station = Station.query.filter_by(
            name=data['station_name'], 
            group_id=group.id
        ).first()
        
        if not station:
            station = Station(
                name=data['station_name'],
                group_id=group.id,
                external_id=data.get('station_id')
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
            external_timestamp=datetime.utcnow()
        )
        db.session.add(sensor_data)
        
        # Update station's last triggered time if trap was triggered
        if sensor_data.trap_triggered:
            station.last_triggered = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Data stored successfully",
            "data": {
                "group_id": group.id,
                "station_id": station.id,
                "sensor_data_id": sensor_data.id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/groups', methods=['GET'])
def get_groups():
    """Get all groups with their stations"""
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

@app.route('/api/stations/<int:station_id>/data', methods=['GET'])
def get_station_data(station_id):
    """Get sensor data for a specific station"""
    station = Station.query.get_or_404(station_id)
    data = SensorData.query.filter_by(station_id=station_id).order_by(SensorData.timestamp.desc()).all()
    
    return jsonify([{
        "timestamp": d.timestamp.isoformat(),
        "mouse_present": d.mouse_present,
        "mouse_weight": d.mouse_weight,
        "bait1_touched": d.bait1_touched,
        "bait2_touched": d.bait2_touched,
        "temperature": d.temperature,
        "humidity": d.humidity,
        "trap_triggered": d.trap_triggered
    } for d in data])

def init_db():
    """Initialize the database"""
    os.makedirs('database', exist_ok=True)
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    # Clean up old data on startup
    cleanup_old_data()
    app.run(host='0.0.0.0', port=5000, debug=True) 