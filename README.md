# Contact Management System

A Flask-based server and client system for managing contacts.

## Features

- SQLite database storage
- REST API endpoints for contact management
- Contact data display and editing
- Data export to JSON
- Full CRUD operations

## Server Setup (Raspberry Pi)

1. Install dependencies:
```bash
pip install flask
```

2. Update the database path in `pi_data_server.py`:
```python
DB_PATH = '/path/to/your/test.db'
```

3. Run the server:
```bash
python pi_data_server.py
```

## Client Setup (Laptop)

1. Install dependencies:
```bash
pip install requests
```

2. Update the Raspberry Pi IP in `pi_data_client.py`:
```python
PI_IP = '192.168.1.100'  # Replace with your Raspberry Pi's IP
```

3. Run the client:
```bash
python pi_data_client.py
```

## API Endpoints

- `GET /api/contacts` - Get all contacts
- `POST /api/contacts` - Add a new contact
- `GET /api/contacts/<id>` - Get a specific contact
- `PUT /api/contacts/<id>` - Update a contact
- `DELETE /api/contacts/<id>` - Delete a contact

## Data Structure

Each contact record contains:
- ID (auto-generated)
- Name (required)
- Email (optional)
- Phone (optional)
- Created At (auto-generated timestamp)

## Client Features

1. List all contacts
2. Add new contact
3. View contact details
4. Update existing contact
5. Delete contact
6. Export contacts to JSON file 