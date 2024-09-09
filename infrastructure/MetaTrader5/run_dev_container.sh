#!/bin/sh

docker run --rm -it -p 18812:18812/tcp -p 5900:5900/tcp --env-file ./.env --name mt5_terminal metatrader5-terminal:latest
