"""
VNC Client for MetaTrader 5 Docker Login

## Resources:
    - https://github.com/sibson/vncdotool/blob/main/docs/library.rst
"""

import os
import time
from vncdotool import api
from dotenv import load_dotenv


class VNCMT5Client:
    """
    A client to automate MetaTrader 5 login using VNC.

    Attributes:
        client (api.VNCDoToolClient): The VNC client connection object.
    """

    def __init__(self, server_url: str, password: str = None, timeout: int = 10):
        """
        Initialize the VNCMT5Client with the server URL and optional password.

        Args:
            server_url (str): The VNC server URL to connect to.
            password (str): The password for the VNC server (default is None).
            timeout (int): Timeout for the VNC client connection (default is 10 seconds).
        """
        self.client = api.connect(server_url, password=password)
        self.client.timeout = timeout

    def clear_and_type_value(self, value: str, empty_field: bool = False, next_field_count: int = 1):
        """
        Clears a form field, enters a new value, and optionally moves to the next field.

        Args:
            value (str): The string value to enter in the form field.
            empty_field (bool): Whether to empty the field before entering the value (default is False).
            next_field_count (int): The number of times to press 'Tab' to move to the next field (default is 1).
        """
        if empty_field:
            # Select all text and delete it
            self.client.keyPress('ctrl-A')
            self.client.keyPress('del')
            time.sleep(0.1)

        # Enter the new value with a slight delay between each character
        for character in value:
            self.client.keyPress(character)
            time.sleep(0.1)

        # Optionally, press Tab to move to the next field
        for _ in range(next_field_count):
            self.client.keyPress('tab')
            time.sleep(0.1)
        
        time.sleep(2)

    def ping_mt_server(self, server: str):
        """
        Ping MetaTrader's server by searching for the broker server in the list of company servers available.
        
        Args:
            server (str): The broker server name to search for.
        """
        time.sleep(5)

        # Click on the File tab
        self.client.mouseMove(20, 22)
        self.client.mousePress(1)
        time.sleep(0.5)

        # Click on Open an Account
        self.client.mouseMove(100, 310)
        self.client.mousePress(1)
        time.sleep(0.5)

        # Search for server in list of companies 
        self.client.mouseMove(350, 250)
        self.client.mousePress(1)
        time.sleep(0.5)

        self.clear_and_type_value(server, empty_field=True)
        self.client.keyPress('enter')
        time.sleep(5)

        # Close search dialog 
        self.client.mouseMove(930, 630)
        self.client.mousePress(1)
        time.sleep(0.5)

    def login_to_mt5(self, login: str, password: str, server: str):
        """
        Logs in to the MetaTrader 5 account.

        Args:
            login (str): The MetaTrader 5 account login number.
            password (str): The MetaTrader 5 account password.
            server (str): The MetaTrader 5 server name.
        """
        # Probe server
        self.ping_mt_server(server)
        time.sleep(2)

        # Click on the File tab
        self.client.mouseMove(20, 22)
        self.client.mousePress(1)
        time.sleep(0.5)

        # Click on Login to Trade Account
        self.client.mouseMove(100, 380)
        self.client.mousePress(1)

        # Fill the Login form
        self.clear_and_type_value(login)
        # Move to the next field
        self.clear_and_type_value(password, next_field_count=2)
        # Move to the next field
        self.clear_and_type_value(server, empty_field=True)

        time.sleep(0.2)
        self.client.keyPress('enter')
        time.sleep(10)

    def enable_algo_trading(self):
        """
        Enables algorithmic trading on the MetaTrader 5 platform.
        """
        # Enable Algo trading
        self.client.mouseMove(890, 50)
        self.client.mousePress(1)
        time.sleep(0.2)

    def open_journal_tab(self):
        """
        Tries to open the Journal tab on MetaTrader 5 (optional).
        """
        # Try to open Journal tab (optional)
        self.client.mouseMove(690, 760)
        self.client.mousePress(1)
        time.sleep(0.2)

    def capture_screenshot(self, file_name: str = 'screenshot.png'):
        """
        Captures a screenshot of the current VNC screen.

        Args:
            file_name (str): The name of the file to save the screenshot (default is 'screenshot.png').
        """
        try:
            self.client.captureScreen(file_name)
        except TimeoutError:
            print('Timeout when capturing screen')

    def disconnect(self):
        """
        Disconnects the VNC client.
        """
        if self.client is not None:
            self.client.disconnect()
            self.client = None

    def _set_login_successful_env_var(self):
        """
        Sets an environment variable to indicate a successful login.
        """
        os.environ['LOGIN_SUCCESSFUL'] = 'true'

    def verify_login(self, login: str, password: str, server: str) -> bool:
        """
        Verifies if the MetaTrader 5 login was successful.

        This method attempts to log in to the MetaTrader 5 server using the provided credentials.
        If the login is unsuccessful, it raises an exception with the error details.

        Args:
            login (str): The MetaTrader 5 account login number.
            password (str): The MetaTrader 5 account password.
            server (str): The MetaTrader 5 server name.
        
        Returns:
            bool: True if the login is successful, False otherwise.
        
        Raises:
            Exception: If the login fails, with the error code and description.
        """
        time.sleep(15)

        import MetaTrader5 as mt5

        # Attempt to establish a connection to the MetaTrader 5 terminal
        is_connected = mt5.initialize(
            "",
            login=int(login),
            password=password,
            server=server,
            timeout=120,
            portable=True
        )

        if is_connected:
            print(f"Login successful: {is_connected}")
            self._set_login_successful_env_var()
            return True
        else:
            error_code, error_description = mt5.last_error()

            # Check for IPC timeout => -10005:
            if int(error_code) != mt5.RES_E_INTERNAL_FAIL_TIMEOUT: 
                raise Exception(f"Login failed, error code = {error_code}, description = {error_description}")
            
            # Probe server
            self.ping_mt_server(server)
            time.sleep(0.5)
            self.verify_login(login, password, server)

def load_mt5_credentials():
    """
    Loads environment variables and retrieves MetaTrader 5 credentials.

    :return: A tuple containing the login, password, and server values.
    """
    # Load environment variables
    load_dotenv()

    # Retrieve MetaTrader 5 credentials from environment variables
    login = os.getenv('MT5_ACCOUNT_NUMBER')
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER')

    return login, password, server

def main():
    # Load and check MetaTrader 5 credentials
    login, password, server = load_mt5_credentials()

    # Ensure required environment variables are set
    while not all([login, password, server]):
        print("Required environment variables (MT5_ACCOUNT_NUMBER, MT5_PASSWORD, MT5_SERVER) are not set.")
        time.sleep(5)  # Wait for 5 seconds before checking again
        # Reload credentials in case they are set during the loop
        login, password, server = load_mt5_credentials()

    VNC_SERVER_URL = "localhost"
    VNC_SERVER_PASSWORD = None

    # Create a VNCMT5Client instance
    vnc_mt5_client = VNCMT5Client(server_url=VNC_SERVER_URL, password=VNC_SERVER_PASSWORD)

    try:
        # Log in to MetaTrader 5
        vnc_mt5_client.login_to_mt5(login, password, server)

        # Enable algorithmic trading
        vnc_mt5_client.enable_algo_trading()

        # Optionally open the Journal tab
        vnc_mt5_client.open_journal_tab()

        # Verify login
        vnc_mt5_client.verify_login(login, password, server)

        raise KeyboardInterrupt("Login attempt completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Disconnect the VNC client
        vnc_mt5_client.disconnect()


if __name__ == "__main__":
    main()


# 
# There are two login approaches, 
#  - Only once: Where the file is utilized during the container startup.
#  - API connect: Where the file is called ass some sort of api to login the account, off course we can use the existing rpyc server.
# https://chatgpt.com/c/46d9d791-9271-4122-b462-f248e2671e16