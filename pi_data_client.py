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

def get_all_contacts():
    """Get all contacts from the server"""
    try:
        response = requests.get(f'{BASE_URL}/contacts')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching contacts: {e}")
        return None

def add_contact():
    """Add a new contact"""
    name = input("Enter name: ")
    email = input("Enter email (optional, press Enter to skip): ").strip() or None
    phone = input("Enter phone (optional, press Enter to skip): ").strip() or None
    
    data = {
        "name": name,
        "email": email,
        "phone": phone
    }
    
    try:
        response = requests.post(f'{BASE_URL}/contacts', json=data)
        response.raise_for_status()
        print("\nContact added successfully!")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error adding contact: {e}")
        return None

def get_contact():
    """Get a specific contact"""
    contact_id = input("Enter contact ID: ")
    try:
        response = requests.get(f'{BASE_URL}/contacts/{contact_id}')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching contact: {e}")
        return None

def update_contact():
    """Update an existing contact"""
    contact_id = input("Enter contact ID to update: ")
    
    try:
        # First get the current contact data
        response = requests.get(f'{BASE_URL}/contacts/{contact_id}')
        response.raise_for_status()
        current = response.json()['data']
        
        # Get updated information
        print("\nPress Enter to keep current value")
        name = input(f"Name [{current['name']}]: ").strip() or current['name']
        email = input(f"Email [{current.get('email', '')}]: ").strip() or current.get('email')
        phone = input(f"Phone [{current.get('phone', '')}]: ").strip() or current.get('phone')
        
        data = {
            "name": name,
            "email": email,
            "phone": phone
        }
        
        response = requests.put(f'{BASE_URL}/contacts/{contact_id}', json=data)
        response.raise_for_status()
        print("\nContact updated successfully!")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error updating contact: {e}")
        return None

def delete_contact():
    """Delete a contact"""
    contact_id = input("Enter contact ID to delete: ")
    
    try:
        response = requests.delete(f'{BASE_URL}/contacts/{contact_id}')
        response.raise_for_status()
        print("\nContact deleted successfully!")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error deleting contact: {e}")
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

def print_contact(contact):
    """Print a single contact in a readable format"""
    print("\n" + "=" * 40)
    print(f"ID: {contact.get('id', 'N/A')}")
    print(f"Name: {contact.get('name', 'N/A')}")
    print(f"Email: {contact.get('email', 'N/A')}")
    print(f"Phone: {contact.get('phone', 'N/A')}")
    print("=" * 40)

def print_contacts(data):
    """Print contacts in a readable format"""
    if not data or 'data' not in data:
        print("No contacts to display")
        return
        
    print(f"\nTotal contacts: {data.get('count', 0)}")
    
    for contact in data['data']:
        print_contact(contact)

def main():
    while True:
        print("\nOptions:")
        print("1. Get all data")
        print("2. Get latest data")
        print("3. Get data for specific device")
        print("4. Save data to file")
        print("5. List all contacts")
        print("6. Add new contact")
        print("7. View contact")
        print("8. Update contact")
        print("9. Delete contact")
        print("10. Save contacts to file")
        print("11. Exit")
        
        choice = input("\nEnter your choice (1-11): ")
        
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
            data = get_all_contacts()
            if data:
                print_contacts(data)
                
        elif choice == '6':
            add_contact()
            
        elif choice == '7':
            data = get_contact()
            if data and 'data' in data:
                print_contact(data['data'])
                
        elif choice == '8':
            update_contact()
            
        elif choice == '9':
            delete_contact()
            
        elif choice == '10':
            data = get_all_contacts()
            if data:
                filename = input("Enter filename (or press Enter for default): ")
                if filename:
                    save_to_file(data, filename)
                else:
                    save_to_file(data)
                    
        elif choice == '11':
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main() 