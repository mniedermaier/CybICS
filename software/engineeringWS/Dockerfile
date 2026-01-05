FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive
ENV USER=root

# Install base packages and desktop environment
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    python3 \
    python3-pip \
    xfce4 \
    xfce4-terminal \
    tigervnc-standalone-server \
    tigervnc-common \
    dbus-x11 \
    supervisor \
    firefox \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install noVNC
RUN git clone --depth 1 https://github.com/novnc/noVNC.git /opt/novnc \
    && git clone --depth 1 https://github.com/novnc/websockify.git /opt/novnc/utils/websockify

# Install OpenPLC Editor dependencies
RUN apt-get update && apt-get install -y \
    python3-wxgtk4.0 \
    python3-numpy \
    python3-matplotlib \
    python3-lxml \
    python3-pip \
    python3-venv \
    autoconf \
    automake \
    libtool \
    flex \
    bison \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Download and install OpenPLC Editor
WORKDIR /opt
RUN git clone --recurse-submodules https://github.com/thiagoralves/OpenPLC_Editor.git

# Build matiec compiler
WORKDIR /opt/OpenPLC_Editor/matiec
RUN autoreconf -i \
    && ./configure \
    && make \
    && cp ./iec2c ../editor/arduino/bin/

# Install Python dependencies for OpenPLC Editor
# Note: wxPython, lxml, and matplotlib are already installed via apt packages
WORKDIR /opt/OpenPLC_Editor
RUN pip3 install --no-cache-dir \
    wheel \
    jinja2 \
    future \
    zeroconf \
    pyserial \
    pypubsub \
    pyro5 \
    attrdict3

# Create launch script
RUN echo '#!/bin/bash\n\
cd /opt/OpenPLC_Editor\n\
python3 editor/Beremiz.py "$@"' > /usr/local/bin/openplc-editor \
    && chmod +x /usr/local/bin/openplc-editor

# Set up VNC
RUN mkdir -p /root/.vnc \
    && echo "cybics" | vncpasswd -f > /root/.vnc/passwd \
    && chmod 600 /root/.vnc/passwd

# Create VNC startup script
RUN echo '#!/bin/bash\n\
xrdb $HOME/.Xresources 2>/dev/null || true\n\
exec startxfce4' > /root/.vnc/xstartup \
    && chmod +x /root/.vnc/xstartup

# Create XFCE config directory
RUN mkdir -p /root/.config/xfce4

# Configure supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create desktop shortcut for OpenPLC Editor
RUN mkdir -p /root/Desktop \
    && echo '[Desktop Entry]\n\
Version=1.0\n\
Type=Application\n\
Name=OpenPLC Editor\n\
Comment=IEC 61131-3 PLC Programming Tool\n\
Exec=openplc-editor\n\
Icon=/opt/OpenPLC_Editor/editor/images/brz.ico\n\
Terminal=false\n\
Categories=Development;' > /root/Desktop/openplc-editor.desktop \
    && chmod +x /root/Desktop/openplc-editor.desktop

# Expose VNC and noVNC ports
EXPOSE 5901 6080

WORKDIR /root

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
