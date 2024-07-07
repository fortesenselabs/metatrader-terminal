![deploy workflow](https://github.com/FortesenseLabs/metatrader-terminal/actions/workflows/deploy.yml/badge.svg)

# MetaTrader (with vnc-alpine)

Imagine a dedicated server that acts as a bridge between your MetaTrader terminal and the world of automation and integration. That's the essence of the Metatrader Service. It's a standalone server application designed to interact with your MetaTrader terminal using NATS for efficient, real-time communication.

- **NATS**: This high-performance messaging system enables fast, reliable communication between the server and your terminal. It allows for instant updates and reactive actions based on market movements, making it ideal for financial applications.

**Potential Use Cases:**

- **Copy Trading**: Develop a system for replicating trades from successful traders directly on the server.
- **Risk Management**: Implement automated risk management tools that monitor positions and react to market changes.
- **Backtesting & Optimization**: Run backtests and optimize your trading strategies on the server without impacting your live trading activity.
- **Data Analysis and Research**: Utilize the server to collect, store, and analyze historical and real-time market data for advanced research purposes.

## Container

The container provides a [VNC](https://en.wikipedia.org/wiki/Virtual_Network_Computing)-enabled and wine container based on Alpine Linux.

The container is meant to serve as a basis for containerized X11 applications using wine. It has the following features:

- Openbox minimal Window Manager
- Graphical login
- wine64
- python3

Based on Alpine Linux, the container is less than 500 MB in size. Most of this is the X11 window system, wine, and python3.

### Extra:

- Metatrader 5 64bit
- dwxconnect expert adviser datafeed [dwxconnect](https://github.com/darwinex/dwxconnect)
- Server (with NATS)

## Usage

Metatrader 5 on Docker and VNC

Open your preferred VNC viewer and go to `localhost:5900`.

### Connect to the MT5 Terminal via VNC

You can interact with the MT5 terminal using a graphical interface via VNC. Use a VNC client on your system or a web-based VNC viewer to connect to `localhost:5900`. Enter the default password set for the VNC server.

**Default Credentials**:

- **Username**: root
- **Password**: root

### Access the NATS Server

To manage the MT5 terminal via the NATS server, configure your application to connect to `localhost:4222` using the NATS protocol. This allows you to interact programmatically with the MT5 terminal.

## Development

Create a `.env` file from the `.env.example` file.

```bash
python -m venv .venv # (use python3.9)
python -m pip install -r metatrader-5/requirements.txt
# python -m pytest -v
```

### VNC LOGIN

```
login: root
password: root
```

Run and build an image named `fortesenselabsmt` and run the container named `fortesenselabsmt`.

```bash
make run
```

Build image named `fortesenselabsmt`.

```bash
make build
```

Login to the shell.

```bash
 make shell
```

## TODOS

- Write a client in Python (can follow the python-binance format).

## Resources

- [Backtrader-MQL5-API](https://github.com/AwesomeTrading/Backtrader-MQL5-API)
- [AwesomeTrading](https://github.com/orgs/AwesomeTrading/)
- [MTSocketAPI Python](https://www.mtsocketapi.com/doc5/for_developers/Python.html)
- [lws2mql](https://github.com/AwesomeTrading/lws2mql)
- [Mastering Financial Pattern](https://www.oreilly.com/library/view/mastering-financial-pattern/9781098120467/ch01.html)
- [Metatrader5-Docker](https://github.com/ejtraderLabs/Metatrader5-Docker)

## Errors

```bash
 89.47 ERROR: unable to select packages:
 89.54   libressl3.1-libcrypto (no such package):
     89.54     required by: world[libressl3.1-libcrypto]
```

You can use the link to check if the Alpine packages exist in their respective branches in the repo:
https://pkgs.alpinelinux.org/contents?file=&path=&name=x11vnc&branch=edge&repo=community&arch=x86_64

### linux/arm64 build failing

Linux/arm64 building failing out of the two platforms in the pipeline:

Platforms: `linux/amd64`, `linux/arm64`

```bash
3.282 (22/22) Installing samba-winbind (4.15.13-r0)
3.326 Executing busybox-1.34.1-r7.trigger
3.379 OK: 325 MiB in 174 packages
3.533 fetch http://dl-3.alpinelinux.org/alpine/v3.15/community/aarch64/APKINDEX.tar.gz
unable to select packages:
5.467   wine (no such package):
5.467     required by: world[wine]
------
 1 warning found (use --debug to expand):
 - LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 33)
Dockerfile.mt5:110
--------------------
 109 |     # wine
 110 | >>> RUN apk update \
 111 | >>>     && apk add samba-winbind \
 112 | >>>     && apk add wine --arch=all --repository http://dl-3.alpinelinux.org/alpine/v3.15/community/ \
 113 | >>>     && ln -s /usr/bin/wine64 /usr/bin/wine
 114 |
--------------------
ERROR: failed to solve: process "/bin/sh -c apk update     && apk add samba-winbind     && apk add wine --arch=all --repository http://dl-3.alpinelinux.org/alpine/v3.15/community/     && ln -s /usr/bin/wine64 /usr/bin/wine" did not complete successfully: exit code: 1
Error: buildx failed with: ERROR: failed to solve: process "/bin/sh -c apk update     && apk add samba-winbind     && apk add wine --arch=all --repository http://dl-3.alpinelinux.org/alpine/v3.15/community/     && ln -s /usr/bin/wine64 /usr/bin/wine" did not complete successfully: exit code: 1
```

Line in Dockerfile:

```Dockerfile
# RUN apk update \
#     && apk add samba-winbind \
#     && apk add wine --arch=all --repository http://dl-3.alpinelinux.org/alpine/v3.15/community/ \
#     && ln -s /usr/bin/wine64 /usr/bin/wine
```

## MT Auto Login Testing

https://github.com/EA31337/EA-Tester/

```bash
wine ./terminal64.exe '/portable' '/config:C:\Program Files\Metatrader 5\Config\common-config-custom.ini'
```

## Server DUMP

**App Logging:**

```python
# self.log_formatter = logging.Formatter(
#             "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s"
#         )
```

**Config:**

```python
# docker_settings = Settings(".docker")
# production_settings = Settings(".production")
# test_settings = Settings(".test")

# print(
#     docker_settings.metatrader_files_dir
# )

# MetaTraderFilesDir: str = os.environ.get("MT_FILES_DIR")
# PYDANTIC_SETTINGS_PREFIX = os.environ.get("PYDANTIC_SETTINGS_POSTFIX", "")

# class Settings:
#     def __init__(self, env_postfix=""):
#         self.env_postfix = env_postfix
#         self.metatrader_files_dir = self._get_setting("MT_FILES_DIR")

#     def _get_setting(self, key):
#         value = os.environ.get(f"{key}{self.env_postfix}")
#         if not value:
#             raise ValueError(f"Missing environment variable: {key}")
#         return value

# docker_settings = Settings(".docker")
# production_settings = Settings(".production")
# test_settings = Settings(".test")

# print(docker_settings.metatrader_files_dir)  # This will print the value from the .docker environment variable
```

**BaseHandler: **

```python
        try:
            self.dwx_client = DWXClient(
                self,
                dwx_client_params.mt_directory_path,
                dwx_client_params.sleep_delay,
                dwx_client_params.max_retry_command_seconds,
                dwx_client_params.verbose,
            )
        except (ConnectionError, DWXClientError) as e:  # Catch more specific errors
            raise ValueError(
                "An error occurred while connecting to MetaTrader: ", e
            ) from e
```
