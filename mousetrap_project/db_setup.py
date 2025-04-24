from app import db, SensorData, Model1Output, Model2Output, Model3Output
from datetime import datetime, timedelta

def init_db():
    db.create_all()
    print("Database initialized successfully!")

def clear_old_data():
    # Delete data older than 3 months
    three_months_ago = datetime.utcnow() - timedelta(days=90)
    SensorData.query.filter(SensorData.timestamp < three_months_ago).delete()
    Model1Output.query.filter(Model1Output.timestamp < three_months_ago).delete()
    Model2Output.query.filter(Model2Output.timestamp < three_months_ago).delete()
    Model3Output.query.filter(Model3Output.timestamp < three_months_ago).delete()
    db.session.commit()
    print("Old data cleared successfully!")

if __name__ == '__main__':
    init_db()
    clear_old_data() 