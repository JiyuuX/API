
from flask import Flask, jsonify, request, Response
from functools import wraps
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import base64
import psycopg2
import time
import threading

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'database': 'your_db',
    'user': 'your_username',
    'password': 'your_password'
}

# store request timestamps for each user and IP address
user_request_times = {}
ip_request_times = {}


# Function to check and enforce basic authentication
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        print("Received Authorization header:", auth)  # Add this line for debugging

        if not auth or not auth.startswith('Basic '):
            return Response('Authentication required', 401, {'WWW-Authenticate': 'Basic realm="API Key and Secret Key Required"'})

        
        try:
            credentials_bytes = base64.b64decode(auth[len('Basic '):])
            credentials = credentials_bytes.decode('utf-8')
            api_key, api_secret_key = credentials.split(":")
        except Exception as e:
            print("Error while decoding Authorization header:", str(e))  # Add this line for debugging
            return Response('Invalid Authorization Header', 400)

        
        with psycopg2.connect(**db_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM user_information WHERE api_key = %s AND api_secret_key = %s',
                               (api_key, api_secret_key))
                data = cursor.fetchone()

        if not data:
            return Response('Invalid API Key or API Secret Key', 401)

        return f(*args, **kwargs)

    return decorated


#register a new user with IP address restriction
@app.route('/register', methods=['POST'])
def register_user():
    remote_ip = get_remote_address()
    
    if has_exceeded_ip_limit(remote_ip, 2):
        return Response('Too many registration requests. Please try again later.', 429)

    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    
    with psycopg2.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM user_information WHERE username = %s OR email = %s', (username, email))
            existing_user = cursor.fetchone()

    if existing_user:
        return jsonify({'message': 'Username or email already registered'}), 409

    # Generate API key and API secret key
    api_key, api_secret_key = generate_api_keys()

    
    salt = os.urandom(32)
    salted_password = salt + password.encode()
    hashed_password = hashlib.sha256(salted_password).hexdigest()

    
    with psycopg2.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO user_information (username, email, password, api_key, api_secret_key) VALUES (%s, %s, %s, %s, %s)',
                           (username, email, hashed_password, api_key, api_secret_key))

    # Send API keys to the user's email
    send_api_keys_to_email(username, email, api_key, api_secret_key)

    return jsonify({'message': 'User registered successfully'}), 201


# generate API key and API secret key
def generate_api_keys():
    api_key = secrets.token_urlsafe(16)  
    api_secret_key = secrets.token_urlsafe(32) 
    return api_key, api_secret_key


# send API keys to user's email
def send_api_keys_to_email(username, email, api_key, api_secret_key):
    # Email configuration
    sender_email = your_email_address
    sender_password = 'your_password'  

    # Email content
    subject = 'Your API Keys'
    message = f'''
    Hello {username},

    Thank you for registering! Here are your API keys:

    API Key: {api_key}
    API Secret Key: {api_secret_key}

    Keep these keys secure and do not share them with anyone.

    Regards,
    Sended from API-BURAK
    '''

    # Create a MIMEText object
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject

    
    msg.attach(MIMEText(message, 'plain'))

    try:
       
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Use the appropriate SMTP server and port
        server.starttls()
        
        server.login(sender_email, sender_password)
        
        server.sendmail(sender_email, email, msg.as_string())
       
        server.quit()

        print("Email sent successfully")
    except Exception as e:
        print("Error sending email:", str(e))


#get the remote IP address
def get_remote_address():
    if 'X-Forwarded-For' in request.headers:
        return request.headers.getlist('X-Forwarded-For')[0]
    else:
        return request.remote_addr


#check if an IP address has exceeded the request limit
def has_exceeded_ip_limit(ip_address, limit_per_day):
    last_request_time = ip_request_times.get(ip_address, 0)
    current_time = time.time()
    
    if current_time - last_request_time > 24 * 60 * 60:
        
        ip_request_times[ip_address] = current_time
        return False
    else:
       
        return len([t for t in ip_request_times.values() if current_time - t < 24 * 60 * 60]) >= limit_per_day


#check if a user has exceeded the request limit
def has_exceeded_user_limit(api_key, limit_per_minute):
    last_request_time = user_request_times.get(api_key, 0)
    current_time = time.time()
   
    if current_time - last_request_time > 60:
       
        user_request_times[api_key] = current_time
        return False
    else:
       
        return len([t for t in user_request_times.values() if current_time - t < 60]) >= limit_per_minute


# clean the user and IP request times every 1 hour
def clean_request_times():
    while True:
        current_time = time.time()
        
        for api_key, request_time in list(user_request_times.items()):
            if current_time - request_time >= 3600:
                del user_request_times[api_key]
       
        for ip_address, request_time in list(ip_request_times.items()):
            if current_time - request_time >= 3600:
                del ip_request_times[ip_address]
        time.sleep(3600)  # Sleep for 1 hour



# API routes to fetch data
@app.route('/force_order', methods=['GET'])
@requires_auth
def get_force_order_data():
    data_size = min(int(request.args.get('data_size', 30)), 1000) 
    api_key = request.headers.get('Authorization').split(':')[0][len('Basic '):]

    if has_exceeded_user_limit(api_key, 1):
        response= {'message':'Too many requests to force_order. Please try again.',
                   'status':'429'}
        return jsonify(response)#Response('Too many requests. Please try again later.', 429)

    with psycopg2.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM force_order LIMIT %s', (data_size,))
            data = cursor.fetchall()

    response = {'data': data}
    return jsonify(response)


@app.route('/kline_1m', methods=['GET'])
@requires_auth
def get_kline_1m_data():
    data_size = min(int(request.args.get('data_size', 30)), 1000)  
    api_key = request.headers.get('Authorization').split(':')[0][len('Basic '):]

    if has_exceeded_user_limit(api_key, 1):
        response = {'message': 'Too many requests to kline_1m. Please try again.',
                    'status': '429'}
        return jsonify(response)

    with psycopg2.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM kline_1m LIMIT %s', (data_size,))
            data = cursor.fetchall()

    response = {'data': data}
    return jsonify(response)


@app.route('/kline_5m', methods=['GET'])
@requires_auth
def get_kline_5m_data():
    data_size = min(int(request.args.get('data_size', 30)), 1000)  
    api_key = request.headers.get('Authorization').split(':')[0][len('Basic '):]

    if has_exceeded_user_limit(api_key, 1):
        response = {'message': 'Too many requests to kline_1m. Please try again.',
                    'status': '429'}
        return jsonify(response)

    with psycopg2.connect(**db_config) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM kline_5m LIMIT %s', (data_size,))
            data = cursor.fetchall()

    response = {'data': data}
    return jsonify(response)

if __name__ == '__main__':
   
    cleaning_thread = threading.Thread(target=clean_request_times)
    cleaning_thread.daemon = True
    cleaning_thread.start()

    app.run(host='localhost', port=5000, debug=False)


