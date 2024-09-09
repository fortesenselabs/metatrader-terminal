# FROM golang:1.14-buster AS novnc-build

# WORKDIR /src

# RUN go mod init build && \
#     go get github.com/geek1011/easy-novnc@v1.1.0 && \
#     go build -o /bin/easy-novnc github.com/geek1011/easy-novnc

FROM tobix/pywine:3.9

# ----------------------------------------------------------------------------------------------
LABEL org.opencontainers.image.source=https://github.com/FortesenseLabs/metatrader-terminal
LABEL org.opencontainers.image.description="Metatrader 5 Terminal (with RPYC API)"
# ----------------------------------------------------------------------------------------------

# USER root
ENV DISPLAY :0
# ENV USER=root
# ENV PASSWORD=root
ENV HOME=/root
ENV SERVER_HOST='0.0.0.0'
ENV SERVER_PORT=18812
ENV VNC_DESKTOP_NAME="Metatrader5"
ENV VNC_GEOMETRY="1280x800"
ENV DRIVE_C=${WINEPREFIX}/drive_c
STOPSIGNAL SIGRTMIN+3

# MT5 Account Details 
ENV MT5_ACCOUNT_NUMBER=''
ENV MT5_PASSWORD=''
ENV MT5_SERVER=''

# Install required packages
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends openbox tigervnc-standalone-server supervisor gosu && \
    rm -rf /var/lib/apt/lists && \
    mkdir -p /usr/share/desktop-directories

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends lxterminal nano openssh-client \ 
    rsync xdg-utils htop \
    tar xzip gzip bzip2 zip unzip wget && \
    apt-get clean && \ 
    rm -rf /var/lib/apt/lists

# COPY --from=novnc-build /bin/easy-novnc /usr/local/bin/
COPY assets/menu.xml /etc/xdg/openbox/
COPY assets/supervisord.conf /etc/


WORKDIR /$HOME/
COPY assets .

RUN tar -xzf Metatrader-5.tar.gz -C "$DRIVE_C/" \
    && mv metatrader.desktop /usr/share/applications/ \
    && rm menu.xml supervisord.conf Metatrader-5.tar.gz 

RUN wine pip install -r requirements.txt \
    && chmod +x run_server.sh xtigervnc.sh easy-novnc.sh

EXPOSE 5900 18812 
# Used for debugs:
# - tiger vnc server => 5900
# - easy-novnc => 8000

CMD ["supervisord"]

# TODO: upgrade to wine >= 8 as wine 7 is unstable and unsupported by MT5  