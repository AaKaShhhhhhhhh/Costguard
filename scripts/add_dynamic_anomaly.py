import requests
import datetime

url = "http://localhost:8000/api/v1/anomalies"
headers = {
    "X-API-Key": "default_secret_key",
    "Content-Type": "application/json"
}
data = {
    "provider": "Azure",
    "service": "Virtual Machine",
    "current_cost": 500.0,
    "expected_cost": 50.0,
    "deviation_percent": 900.0,
    "severity": "critical",
    "description": "DYNAMICALLY ADDED VIA SCRIPT",
    "timestamp": datetime.datetime.utcnow().isoformat()
}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
