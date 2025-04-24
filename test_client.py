import requests
import json
from datetime import datetime
import time
import random

def generate_station_data(group_num, station_num):
    """Generate sample data for a specific station"""
    base_temp = 20.0
    base_humidity = 50
    base_pressure = 1013.25
    
    # Add some variation based on group and station
    temp_variation = (group_num * 2) + (station_num * 0.5)
    humidity_variation = (group_num * 5) + (station_num * 2)
    pressure_variation = (group_num * 0.5) + (station_num * 0.1)
    
    # Add some random fluctuation
    temp_fluctuation = random.uniform(-1, 1)
    humidity_fluctuation = random.uniform(-2, 2)
    pressure_fluctuation = random.uniform(-0.1, 0.1)
    
    return {
        "device_id": f"G{group_num}-S{station_num}",
        "device_name": f"Group {group_num} Station {station_num}",
        "timestamp": datetime.now().isoformat(),
        "group_number": group_num,
        "station_number": station_num,
        "sensor_data": {
            "temperature": round(base_temp + temp_variation + temp_fluctuation, 1),
            "humidity": round(base_humidity + humidity_variation + humidity_fluctuation),
            "pressure": round(base_pressure + pressure_variation + pressure_fluctuation, 2),
            "battery_level": random.randint(80, 100),
            "signal_strength": random.choice(["strong", "medium", "weak"])
        }
    }

def send_all_stations_data():
    # Server URL (update this with your server's IP)
    server_url = "http://localhost:8080/api/data"
    
    # Send data for all stations
    for group in range(1, 4):  # 3 groups
        for station in range(1, 4):  # 3 stations per group
            station_data = generate_station_data(group, station)
            
            try:
                # Send POST request
                response = requests.post(
                    server_url,
                    json=station_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                print(f"\nSent data for Group {group} Station {station}")
                print(f"Device ID: {station_data['device_id']}")
                print(f"Response Status: {response.status_code}")
                print(f"Response Body: {response.json()}")
                
            except Exception as e:
                print(f"Error sending data for Group {group} Station {station}: {e}")
            
            # Small delay between stations
            time.sleep(0.5)

def query_all_data():
    # Server URL (update this with your server's IP)
    server_url = "http://localhost:8080/api/data"
    
    try:
        # Send GET request
        response = requests.get(server_url)
        
        print("\nAll Stored Data:")
        print(json.dumps(response.json(), indent=2))
        
    except Exception as e:
        print(f"Error querying data: {e}")

if __name__ == "__main__":
    print("Sending test data for all stations...")
    send_all_stations_data()
    
    print("\nWaiting for data to be processed...")
    time.sleep(2)  # Wait for the server to process the data
    
    print("\nQuerying stored data...")
    query_all_data() 