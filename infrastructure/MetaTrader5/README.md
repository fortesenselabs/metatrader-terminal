# Metatrader 5 Terminal with RPYC API

This Docker image provides a lightweight environment for running the Metatrader 5 Terminal with RPYC API access. It combines two base images:

- `golang:1.14-buster`: Used to build the `easy-novnc` tool for remote desktop access.
- `tobix/pywine:3.9`: Provides a Python environment with Wine for running the Metatrader 5 Terminal on Linux. [tobix/pywine:3.9](https://github.com/webcomics/pywine)

## Features

- Runs Metatrader 5 Terminal using Wine.
- Enables access to the RPYC API for remote control.
- Includes `easy-novnc` for optional remote desktop access (requires additional configuration)
- Exposes ports for RPYC API (18812) and potential VNC (8000)

## Usage

1. **Build the image:**

```
docker build -t metatrader5-terminal .
```

2. **Run the container:**

```
docker run -d --name metatrader5-terminal \
             -p 18812:18812 \
             -p 8000:8000 \
             metatrader5-terminal
```

This command runs the container in detached mode (`-d`) and maps the container's port 18812 to the host's port 18812 (`-p 18812:18812`). You can access the RPYC API from your host at `localhost:18812`.

**Optional: Remote Desktop Access**

This image includes `easy-novnc` for potential remote desktop access. However, additional configuration is needed outside the container, such as using a reverse proxy like Caddy. Refer to the following resources for setting up remote desktop access:

- [https://www.digitalocean.com/community/tutorial-collections/how-to-set-up-a-remote-desktop-with-x2go](https://www.digitalocean.com/community/tutorial-collections/how-to-set-up-a-remote-desktop-with-x2go)
- [https://github.com/gnzsnz/ib-gateway-docker/](https://github.com/gnzsnz/ib-gateway-docker/)

**Additional notes:**

- The container starts the `supervisord` process to manage services within the container.
- The container utilizes the `gosu` user management tool.
- Configuration files like `menu.xml` and `supervisord.conf` are copied into the container.

## Environment Variables

- `SERVER_HOST`: Hostname or IP address for RPYC API access (default: `0.0.0.0`).
- `SERVER_PORT`: Port for RPYC API access (default: `18812`).

## Dependencies

- Requires Docker to be installed and running.

## Contributing

Feel free to submit pull requests for improvements or bug fixes.

## License

This image is licensed under the terms of the respective base image licenses (Golang and tobix/pywine). Please refer to their respective repositories for details.
