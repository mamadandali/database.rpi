from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from models.model1 import Model1
from models.model2 import Model2
from models.model3 import Model3

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

class Model1Output(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)
    prediction = db.Column(db.Float)

class Model2Output(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)
    prediction = db.Column(db.Float)

class Model3Output(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'), nullable=False)
    prediction = db.Column(db.Float)

# Initialize models
model1 = Model1()
model2 = Model2()
model3 = Model3()

# Store active notifications
active_notifications = {}

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
    
    # Run models and store predictions
    model1_pred = model1.predict(data)
    model2_pred = model2.predict(data)
    model3_pred = model3.predict(data)
    
    db.session.add(Model1Output(station_id=station.id, prediction=model1_pred['prediction']))
    db.session.add(Model2Output(station_id=station.id, prediction=model2_pred['prediction']))
    db.session.add(Model3Output(station_id=station.id, prediction=model3_pred['prediction']))
    
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "model_predictions": {
            "model1": model1_pred['prediction'],
            "model2": model2_pred['prediction'],
            "model3": model3_pred['prediction']
        }
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

@app.route('/model1', methods=['GET'])
def get_model1():
    latest = Model1Output.query.order_by(Model1Output.timestamp.desc()).first()
    if latest:
        return jsonify({
            "prediction": latest.prediction,
            "timestamp": latest.timestamp.isoformat()
        })
    return jsonify({"error": "No predictions available"}), 404

@app.route('/model2', methods=['GET'])
def get_model2():
    latest = Model2Output.query.order_by(Model2Output.timestamp.desc()).first()
    if latest:
        return jsonify({
            "prediction": latest.prediction,
            "timestamp": latest.timestamp.isoformat()
        })
    return jsonify({"error": "No predictions available"}), 404

@app.route('/model3', methods=['GET'])
def get_model3():
    latest = Model3Output.query.order_by(Model3Output.timestamp.desc()).first()
    if latest:
        return jsonify({
            "prediction": latest.prediction,
            "timestamp": latest.timestamp.isoformat()
        })
    return jsonify({"error": "No predictions available"}), 404

@app.route('/history', methods=['GET'])
def get_history():
    # Get the last 1000 records
    history = SensorData.query.order_by(SensorData.timestamp.desc()).limit(1000).all()
    
    return jsonify([{
        "timestamp": record.timestamp.isoformat(),
        "mouse_present": record.mouse_present,
        "mouse_weight": record.mouse_weight,
        "bait1_touched": record.bait1_touched,
        "bait2_touched": record.bait2_touched,
        "temperature": record.temperature,
        "humidity": record.humidity
    } for record in history])

if __name__ == '__main__':
    # Ensure the database directory exists
    os.makedirs('database', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True) 