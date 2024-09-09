import os
import argparse
from subprocess import Popen
from rpyc.utils.classic import DEFAULT_SERVER_PORT, DEFAULT_SERVER_SSL_PORT

SERVER_DIR = "server/"
SERVER_CODE = 'server.py'

def main():
    try:
        os.makedirs(SERVER_DIR, exist_ok=True) 
    except OSError as e:
        print(f"Error creating server directory: {e}")
        exit(1)

    parser = argparse.ArgumentParser(description='Create Server.')
    parser.add_argument('-pyp', '--python', type=str, default='python', help='Python that will run the server (have to be a Windows version!)')
    parser.add_argument('-h', '--host', type=str, default='0.0.0.0', help='The host to connect to. The default is 0.0.0.0')
    parser.add_argument('-p', '--port', type=int, default=DEFAULT_SERVER_PORT, help=f'The TCP listener port (default = {DEFAULT_SERVER_PORT!r}, default for SSL = {DEFAULT_SERVER_SSL_PORT!r})')
    parser.add_argument('-w', '--wine', type=str, default='wine', help='Command line to call wine program (default = wine)')
    args = parser.parse_args()

    wine_cmd = args.wine
    win_python_path = args.python
    port = args.port
    host = args.host

    server_file_path = os.path.join(SERVER_DIR, SERVER_CODE)
    server_file_path = server_file_path.replace(f"\\{SERVER_CODE}", f"/{SERVER_CODE}") # dirty fix for => C:\Python\python.exe: can't open file 'Z:\\tmp\\mt5linuxserver.py': [Errno 2] No such file or directory

    # Execute the command 
    Popen([
        wine_cmd,
        os.path.join(win_python_path),
        server_file_path,
        '--host', str(host),
        '--port', str(port),
    ], shell=True).wait()


if __name__ == '__main__':
    main()
