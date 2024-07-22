from datetime import datetime, timezone
import socket


class SocketClient:
    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.mySocket = socket.socket()
        self.connected = False

    def connect(self):
        try:
            self.mySocket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to server at {self.host}:{self.port}")
        except socket.error as e:
            print(f"Failed to connect: {e}")

    def generate_command_id(self):
        now = datetime.now(timezone.utc)
        return round(now.timestamp())

    def send_command(self, command, content):
        if not self.connected:
            print("Not connected to server.")
            return
        command_id = self.generate_command_id()
        message = f"<:{command_id}|{command}|{content}:>"
        try:
            self.mySocket.send(message.encode())
            data = self.mySocket.recv(1024).decode()
            print("Received from server: " + data)
        except socket.error as e:
            print(f"Failed to send command: {e}")
            self.connected = False

    def close_all_orders(self):
        self.send_command("CLOSE_ALL_ORDERS", "")

    def open_order(
        self,
        symbol="EURUSD",
        order_type="buy",
        lots=0.01,
        price=0,
        stop_loss=0,
        take_profit=0,
        magic=0,
        comment="",
        expiration=0,
    ):
        data = [
            symbol,
            order_type,
            lots,
            price,
            stop_loss,
            take_profit,
            magic,
            comment,
            expiration,
        ]
        self.send_command("OPEN_ORDER", ",".join(str(p) for p in data))

    def close(self):
        if self.connected:
            self.mySocket.close()
            self.connected = False
            print("Connection closed")


def main():
    client = SocketClient()
    client.connect()

    while True:
        user_input = input(
            "Enter Command (type 'open_order' to open an order, 'close_all' to close all orders, 'q' to quit): "
        )
        if user_input.lower() == "close_all":
            client.close_all_orders()
        elif user_input.lower() == "open_order":
            symbol = input("Enter Symbol: ")
            order_type = input("Enter Order Type (buy/sell): ")
            volume = input("Enter Volume: ")
            price = input("Enter Price: ")
            sl = input("Enter Stop Loss: ")
            tp = input("Enter Take Profit: ")
            client.open_order(symbol, order_type, volume, price, sl, tp)
        elif user_input.lower() == "q":
            break
        else:
            command = input("Enter Command: ")
            content = input("Enter Content: ")
            client.send_command(command, content)

    client.close()


if __name__ == "__main__":
    main()
