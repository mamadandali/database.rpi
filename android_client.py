import requests
import json
import time
from datetime import datetime
import socket
import threading

class AndroidSensorClient:
    def __init__(self):
        self.server_url = None
        self.device_id = "AND-" + str(int(time.time()))[-6:]  # Unique device ID
        self.discovery_thread = None
        self.stop_discovery = False
        
    def discover_server(self):
        """Discover server on the network"""
        discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        discovery_socket.bind(('', 8081))  # Listen on broadcast port
        
        print("Searching for server on the network...")
        
        while not self.stop_discovery:
            try:
                data, addr = discovery_socket.recvfrom(1024)
                message = data.decode()
                if message.startswith("SERVER_PRESENCE:"):
                    _, hostname, port = message.split(':')
                    server_ip = addr[0]
                    self.server_url = f"http://{server_ip}:{port}/api/data"
                    print(f"\nFound server at {self.server_url}")
                    print(f"Server hostname: {hostname}")
                    return True
            except:
                pass
        return False
    
    def start_discovery(self):
        """Start server discovery in a separate thread"""
        self.discovery_thread = threading.Thread(target=self.discover_server)
        self.discovery_thread.daemon = True
        self.discovery_thread.start()
        
    def stop_discovery_thread(self):
        """Stop the discovery thread"""
        self.stop_discovery = True
        if self.discovery_thread:
            self.discovery_thread.join()
        
    def send_sensor_data(self, sensor_data):
        if not self.server_url:
            print("No server found. Starting discovery...")
            self.start_discovery()
            time.sleep(5)  # Wait for discovery
            if not self.server_url:
                print("Could not find server. Retrying later...")
                return False
                
        try:
            # Add device info and timestamp
            data = {
                "device_id": self.device_id,
                "device_name": "Android Sensor Device",
                "timestamp": datetime.now().isoformat(),
                "sensor_data": sensor_data
            }
            
            # Send POST request with JSON data
            response = requests.post(
                self.server_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Print the response
            print("\nServer Response:")
            print(json.dumps(response.json(), indent=2))
            
            return True
        except Exception as e:
            print(f"Error sending data: {e}")
            # If connection fails, try to rediscover server
            self.server_url = None
            return False

    def get_all_data(self):
        """Get all data stored on the server"""
        if not self.server_url:
            return None
            
        try:
            response = requests.get(self.server_url)
            return response.json()
        except Exception as e:
            print(f"Error getting data: {e}")
            return None

def main():
    client = AndroidSensorClient()
    
    print("Android client started")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Simulate sensor readings
            sensor_data = {
                "temperature": round(20.0 + (time.time() % 10), 1),  # Varying temperature
                "humidity": 60,
                "pressure": 1013.25,
                "battery_level": 85,
                "signal_strength": "strong"
            }
            
            # Send the data
            client.send_sensor_data(sensor_data)
            
            # Wait before sending next reading
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nStopping client...")
        client.stop_discovery_thread()

if __name__ == "__main__":
    main() 