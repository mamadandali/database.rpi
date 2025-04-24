import requests
import json
from datetime import datetime
import os

# Configuration
PI_IP = '192.168.1.100'  # Replace with your Raspberry Pi's IP address
PI_PORT = 5000
BASE_URL = f'http://{PI_IP}:{PI_PORT}/api'

def get_all_data():
    """Get all data from the server"""
    try:
        response = requests.get(f'{BASE_URL}/data')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching all data: {e}")
        return None

def get_latest_data():
    """Get latest data from each device"""
    try:
        response = requests.get(f'{BASE_URL}/data/latest')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest data: {e}")
        return None

def get_device_data(device_id):
    """Get data for a specific device"""
    try:
        response = requests.get(f'{BASE_URL}/data/device/{device_id}')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching device data: {e}")
        return None

def save_to_file(data, filename=None):
    """Save data to a JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'sensor_data_{timestamp}.json'
    
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to file: {e}")

def print_data(data):
    """Print data in a readable format"""
    if not data or 'data' not in data:
        print("No data to display")
        return
        
    print(f"\nTotal records: {data.get('count', 0)}")
    print("=" * 80)
    
    for record in data['data']:
        print(f"\nDevice: {record.get('device_id', 'Unknown')}")
        print(f"Timestamp: {record.get('timestamp', 'Unknown')}")
        print(f"Temperature: {record.get('temperature', 'N/A')}°C")
        print(f"Humidity: {record.get('humidity', 'N/A')}%")
        print(f"Pressure: {record.get('pressure', 'N/A')} hPa")
        print(f"Battery: {record.get('battery_level', 'N/A')}%")
        print(f"Signal: {record.get('signal_strength', 'N/A')}")
        print("-" * 40)

def main():
    while True:
        print("\nOptions:")
        print("1. Get all data")
        print("2. Get latest data")
        print("3. Get data for specific device")
        print("4. Save data to file")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            data = get_all_data()
            if data:
                print_data(data)
                if input("\nSave to file? (y/n): ").lower() == 'y':
                    save_to_file(data)
                    
        elif choice == '2':
            data = get_latest_data()
            if data:
                print_data(data)
                if input("\nSave to file? (y/n): ").lower() == 'y':
                    save_to_file(data)
                    
        elif choice == '3':
            device_id = input("Enter device ID (e.g., G1-S1): ")
            data = get_device_data(device_id)
            if data:
                print_data(data)
                if input("\nSave to file? (y/n): ").lower() == 'y':
                    save_to_file(data)
                    
        elif choice == '4':
            filename = input("Enter filename (or press Enter for default): ")
            if filename:
                save_to_file(data, filename)
            else:
                save_to_file(data)
                
        elif choice == '5':
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main() 