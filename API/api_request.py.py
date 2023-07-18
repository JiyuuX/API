"""
API Endpoints:
register/
kline_1m/
kline_5m/
force_order/

"""

import requests
import base64

force_order_url = 'http://localhost:5000/kline_1m?data_size=5'  #data_size, value of data.

api_key = your_api_key
api_secret_key = 'your_api_secret_key'

credentials = f"{api_key}:{api_secret_key}"
credentials_bytes = credentials.encode('ascii')
base64_credentials = base64.b64encode(credentials_bytes).decode('ascii')

headers = {
    'Authorization': f'Basic {base64_credentials}'
}

response = requests.get(force_order_url, headers=headers)

# Check the response status code
if response.status_code == 200:
    # Print the fetched data
    data = response.json()
    print(data)

#REGISTER REQUEST
""" 
# API endpoint for user registration
register_url = 'http://localhost:5000/register'

# User data to be registered
user_data = {
    'username': 'your_username',
    'email': 'your_email',
    'password': 'your_password'
}

# Send a POST request to the API endpoint with the user data
response = requests.post(register_url, json=user_data)
"""

