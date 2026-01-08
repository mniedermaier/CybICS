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
# Disable screen blanking and DPMS\n\
xset s off\n\
xset -dpms\n\
xset s noblank\n\
exec startxfce4' > /root/.vnc/xstartup \
    && chmod +x /root/.vnc/xstartup

# Create XFCE config directory and backgrounds directory
RUN mkdir -p /root/.config/xfce4 /usr/share/backgrounds

# Copy CybICS background
COPY engineeringWS/cybics-background.png /usr/share/backgrounds/cybics-background.png

# Configure XFCE to use the CybICS background
RUN mkdir -p /root/.config/xfce4/xfconf/xfce-perchannel-xml && \
    echo '<?xml version="1.0" encoding="UTF-8"?>\n\
<channel name="xfce4-desktop" version="1.0">\n\
  <property name="backdrop" type="empty">\n\
    <property name="screen0" type="empty">\n\
      <property name="monitor0" type="empty">\n\
        <property name="workspace0" type="empty">\n\
          <property name="color-style" type="int" value="0"/>\n\
          <property name="image-style" type="int" value="5"/>\n\
          <property name="last-image" type="string" value="/usr/share/backgrounds/cybics-background.png"/>\n\
        </property>\n\
      </property>\n\
      <property name="monitorVNC-0" type="empty">\n\
        <property name="workspace0" type="empty">\n\
          <property name="color-style" type="int" value="0"/>\n\
          <property name="image-style" type="int" value="5"/>\n\
          <property name="last-image" type="string" value="/usr/share/backgrounds/cybics-background.png"/>\n\
        </property>\n\
      </property>\n\
    </property>\n\
  </property>\n\
</channel>' > /root/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml

# Disable XFCE screensaver and power management
RUN echo '<?xml version="1.0" encoding="UTF-8"?>\n\
<channel name="xfce4-screensaver" version="1.0">\n\
  <property name="saver" type="empty">\n\
    <property name="mode" type="int" value="0"/>\n\
    <property name="enabled" type="bool" value="false"/>\n\
  </property>\n\
  <property name="lock" type="empty">\n\
    <property name="enabled" type="bool" value="false"/>\n\
  </property>\n\
</channel>' > /root/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-screensaver.xml && \
    echo '<?xml version="1.0" encoding="UTF-8"?>\n\
<channel name="xfce4-power-manager" version="1.0">\n\
  <property name="xfce4-power-manager" type="empty">\n\
    <property name="dpms-enabled" type="bool" value="false"/>\n\
    <property name="blank-on-ac" type="int" value="0"/>\n\
    <property name="dpms-on-ac-sleep" type="uint" value="0"/>\n\
    <property name="dpms-on-ac-off" type="uint" value="0"/>\n\
  </property>\n\
</channel>' > /root/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml

# Configure supervisor
COPY engineeringWS/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

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

# Create CybICS folder on Desktop for project files
RUN mkdir -p /root/Desktop/CybICS

# Copy Beremiz project files to Desktop
COPY engineeringWS/plc-software/ /root/Desktop/CybICS/

# Create a README in the CybICS folder
RUN echo 'CybICS Project Files\n\
=====================\n\n\
This folder contains the CybICS PLC program (Beremiz project).\n\n\
To open the project:\n\
1. Double-click "OpenPLC Editor" on the desktop\n\
2. File -> Open Project\n\
3. Navigate to /root/Desktop/CybICS/\n\
4. Select the folder and open beremiz.xml\n\n\
You can then modify the program and generate code for deployment to OpenPLC.\n\n\
For more information, visit: https://github.com/hsainnos/CybICS\n' > /root/Desktop/CybICS/README.txt

# Expose VNC and noVNC ports
EXPOSE 5901 6080

WORKDIR /root

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
