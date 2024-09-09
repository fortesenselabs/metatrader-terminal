#!/bin/sh

/usr/bin/Xtigervnc -desktop "$VNC_DESKTOP_NAME" -geometry "$VNC_GEOMETRY" -listen tcp -ac -rfbport 5900 -SecurityTypes None -AlwaysShared -AcceptKeyEvents -AcceptPointerEvents -AcceptSetDesktopSize -SendCutText -AcceptCutText :0

# usr/bin/Xtigervnc -desktop "Metatrader5" -localhost -rfbport 5900 -SecurityTypes None -AlwaysShared -AcceptKeyEvents -AcceptPointerEvents -AcceptSetDesktopSize -SendCutText -AcceptCutText :0
# exec Xtigervnc -desktop "$VNC_DESKTOP_NAME" -geometry "$VNC_GEOMETRY" -listen tcp -ac -SecurityTypes None -AlwaysShared -AcceptKeyEvents -AcceptPointerEvents -SendCutText -AcceptCutText :0


# 9876 5900 | if tigervnc needs to be accessed use a proxy such as Caddy
#
# https://www.digitalocean.com/community/tutorials/how-to-remotely-access-gui-applications-using-docker-and-caddy-on-debian-9
# https://github.com/oposs/tl-docker/
#
# add option to automatically connect to an instance
# /usr/local/bin/easy-novnc --addr :8080 --host localhost --port 5900 --no-url-password --novnc-params "resize=remote"
# Hide connection options from the main screen: --basic-ui
# https://github.com/pgaskin/easy-novnc
# tigervnc options =>  -localhost -rfbport 5900
#
# https://github.com/dtinth/xtigervnc-docker/
# https://github.com/cair/pyVNC
# https://github.com/sibson/vncdotool