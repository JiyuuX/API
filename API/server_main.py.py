import threading
import websocket
import json
import psycopg2
from colorama import init, Fore, Style
from time import sleep

init()  # Initialize colorama

URLS = [
    'wss://wss.com',
    'wss://wss.com',
    'wss://wss.com'
]

class WebSocketThread(threading.Thread):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.lock = threading.Lock()
        self.connection = self.create_database_connection()
        self.ws = None

    def run(self):
        self.connect_to_websocket()

    def connect_to_websocket(self):
        self.ws = websocket.WebSocketApp(self.url, on_open=self.on_open, on_message=self.on_message)
        self.ws.run_forever()

    def on_open(self, ws):
        print("WebSocket connection established.")

    def on_message(self, ws, message):
        # Process the received message based on the URL
        if 'forceOrder' in self.url:
            self.on_message_force_order(message)
        elif 'kline_1m' in self.url:
            self.on_message_kline_1m(message)
        elif 'kline_5m' in self.url:
            self.on_message_kline_5m(message)

    def on_message_force_order(self, message):
        websocket_data = json.loads(message)['o']
        print(f"Received data for force order: {websocket_data}")

        with self.lock:
            self.insert_into_database_force_order('force_order', websocket_data)
            print(f"{Fore.YELLOW}symbol: {websocket_data['s']}, status: {websocket_data['X']}, price: {websocket_data['p']}, origQty: {websocket_data['q']}, side: {websocket_data['S']}, time: {websocket_data['T']} {Style.RESET_ALL}")

    def on_message_kline_1m(self, message):
        websocket_data = json.loads(message)['k']
        print(f"Received data for kline 1m: {websocket_data}")

        if websocket_data['x']:
            print(f"{Fore.GREEN}1m True: {websocket_data}{Style.RESET_ALL}")
            with self.lock:
                self.insert_into_database('kline_1m', str(websocket_data['n']))
                print(f"{Fore.YELLOW} Added database value : {websocket_data['n']} {Style.RESET_ALL}")

    def on_message_kline_5m(self, message):
        websocket_data = json.loads(message)['k']
        print(f"Received data for kline 5m: {websocket_data}")

        if websocket_data['x']:
            print(f"{Fore.GREEN}5m True: {websocket_data}{Style.RESET_ALL}")
            with self.lock:
                self.insert_into_database('kline_5m', str(websocket_data['n']))
                print(f"{Fore.YELLOW} Added database value : {websocket_data['n']} {Style.RESET_ALL}")

    def create_database_connection(self):
        return psycopg2.connect(
            host="localhost",
            database="your_db",
            user="your_username",
            password="your_password"
        )

    def insert_into_database(self, table_name, data):
        print("Insert into function is running...")
        connection = self.connection
        cursor = connection.cursor()

        query = f"INSERT INTO {table_name} (number_of_trades) VALUES (%s)"
        values = (json.dumps(data),)  # Serialize data to JSON string

        cursor.execute(query, values)
        connection.commit()
        print("Data inserted into database")

    def insert_into_database_force_order(self, table_name, data):
        print("Insert into function is running...")
        connection = self.connection
        cursor = connection.cursor()

    
        symbol = data['s']
        status = data['X']
        price = data['p']
        origQty = data['q']
        side = data['S']
        time = data['T']

        query = f"INSERT INTO {table_name} (symbol, status, price, origQty, side, time) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (symbol, status, price, origQty, side, time)

        cursor.execute(query, values)
        connection.commit()
        print("Data inserted into database")


if __name__ == '__main__':
    threads = []

    # Create websocket connection threads as daemon threads
    for url in URLS:
        thread = WebSocketThread(url)
        thread.daemon = True
        threads.append(thread)
        thread.start()

    try:
        while True:
            sleep(0.5)  
    except KeyboardInterrupt:
        print("Program interrupted. Terminating...")
