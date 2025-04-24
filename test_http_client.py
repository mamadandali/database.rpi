import requests
import json
import time
import os

def send_json_file(server_url, json_file_path):
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            json_data = json.load(file)
        
        print(f"Loaded JSON data from {json_file_path}")
        
        # Send POST request with JSON data
        response = requests.post(
            server_url,
            json=json_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Print the response
        print("\nServer Response:")
        print(json.dumps(response.json(), indent=2))
        
        return True
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
        return False
    except json.JSONDecodeError:
        print(f"Error: {json_file_path} contains invalid JSON")
        return False
    except Exception as e:
        print(f"Error sending data: {e}")
        return False

if __name__ == "__main__":
    # Server URL - change this to match your server's IP address
    server_url = "http://127.0.0.1:5000/api/data"
    json_file = "sample_data.json"
    
    print(f"Sending {json_file} to server...")
    send_json_file(server_url, json_file) 