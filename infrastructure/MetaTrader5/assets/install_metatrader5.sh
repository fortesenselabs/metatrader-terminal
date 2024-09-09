#!/bin/sh

# MetaTrader download url
URL="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

# Download MetaTrader
wget $URL

# Set environment to Windows 10
winecfg -v=win10
# Start MetaTrader installer
wine mt5setup.exe

# # Installing MT5
# echo "Installing MT5"
# if ! test -f "mt5setup.exe"; then
# wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe
# fi
# if ! test -f "/workspaces/releat/data/platforms/mt5/0/MetaTrader 5/terminal64.exe"; then
#     wine mt5setup.exe /auto
#     mkdir -p /workspaces/releat/data/platforms/mt5/0
#     cp -r "/root/.wine/drive_c/Program Files/MetaTrader 5" /workspaces/releat/data/platforms/mt5/0
# fi
# # && rm mt5setup.exe \
# echo "MT5 installed successfully"