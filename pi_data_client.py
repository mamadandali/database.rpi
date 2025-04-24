import requests
import json
from datetime import datetime
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
PI_IP = '172.21.235.32'  # Updated to the correct Raspberry Pi IP
PI_PORT = 5000
BASE_URL = f'http://{PI_IP}:{PI_PORT}'  # Base URL without /api

# Configure retry strategy
retry_strategy = Retry(
    total=3,  # number of retries
    backoff_factor=1,  # wait 1, 2, 4 seconds between retries
    status_forcelist=[500, 502, 503, 504]  # HTTP status codes to retry on
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

def make_request(method, endpoint, **kwargs):
    """Make an HTTP request with retry logic"""
    try:
        url = f'{BASE_URL}/{endpoint}'
        response = session.request(method, url, timeout=5, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def get_all_contacts():
    """Get all contacts from the server"""
    return make_request('GET', 'contacts')

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
    
    result = make_request('POST', 'contacts', json=data)
    if result:
        print("\nContact added successfully!")
    return result

def get_contact():
    """Get a specific contact"""
    contact_id = input("Enter contact ID: ")
    return make_request('GET', f'contacts/{contact_id}')

def update_contact():
    """Update an existing contact"""
    contact_id = input("Enter contact ID to update: ")
    
    # First get the current contact data
    current = make_request('GET', f'contacts/{contact_id}')
    if not current or 'data' not in current:
        print("Contact not found")
        return None
        
    current = current['data']
    
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
    
    result = make_request('PUT', f'contacts/{contact_id}', json=data)
    if result:
        print("\nContact updated successfully!")
    return result

def delete_contact():
    """Delete a contact"""
    contact_id = input("Enter contact ID to delete: ")
    result = make_request('DELETE', f'contacts/{contact_id}')
    if result:
        print("\nContact deleted successfully!")
    return result

def save_to_file(data, filename=None):
    """Save data to a JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'contacts_{timestamp}.json'
    
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to file: {e}")

def print_contact(contact):
    """Print a single contact in a readable format"""
    print("\n" + "=" * 40)
    print(f"ID: {contact.get('id', 'N/A')}")
    print(f"Name: {contact.get('name', 'N/A')}")
    print(f"Email: {contact.get('email', 'N/A')}")
    print(f"Phone: {contact.get('phone', 'N/A')}")
    print(f"Created: {contact.get('created_at', 'N/A')}")
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
        print("1. List all contacts")
        print("2. Add new contact")
        print("3. View contact")
        print("4. Update contact")
        print("5. Delete contact")
        print("6. Save contacts to file")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ")
        
        if choice == '1':
            data = get_all_contacts()
            if data:
                print_contacts(data)
                
        elif choice == '2':
            add_contact()
            
        elif choice == '3':
            data = get_contact()
            if data and 'data' in data:
                print_contact(data['data'])
                
        elif choice == '4':
            update_contact()
            
        elif choice == '5':
            delete_contact()
            
        elif choice == '6':
            data = get_all_contacts()
            if data:
                filename = input("Enter filename (or press Enter for default): ")
                if filename:
                    save_to_file(data, filename)
                else:
                    save_to_file(data)
                    
        elif choice == '7':
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main() 