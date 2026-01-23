FROM kalilinux/kali-rolling:latest

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive
ENV USER=root

# Update and install essential tools + desktop environment
RUN apt-get update && apt-get install -y \
    # Desktop environment and VNC
    xfce4 \
    xfce4-terminal \
    tigervnc-standalone-server \
    tigervnc-common \
    dbus-x11 \
    supervisor \
    firefox-esr \
    # Network scanning and enumeration
    nmap \
    masscan \
    netcat-traditional \
    netcat-openbsd \
    socat \
    tcpdump \
    net-tools \
    iputils-ping \
    traceroute \
    whois \
    dnsutils \
    # Protocol analysis
    wireshark \
    tshark \
    # Web testing tools
    nikto \
    sqlmap \
    dirb \
    curl \
    wget \
    # Password cracking
    hydra \
    john \
    hashcat \
    # Exploitation frameworks
    metasploit-framework \
    # Programming and scripting
    python3 \
    python3-pip \
    python3-dev \
    git \
    # Utilities
    vim \
    nano \
    tmux \
    screen \
    bash-completion \
    man-db \
    # Build tools for compiling exploits
    gcc \
    g++ \
    make \
    automake \
    autoconf \
    libtool \
    && rm -rf /var/lib/apt/lists/*

# Install noVNC
RUN git clone --depth 1 https://github.com/novnc/noVNC.git /opt/novnc \
    && git clone --depth 1 https://github.com/novnc/websockify.git /opt/novnc/utils/websockify

# Install Python packages for ICS/OT security
RUN pip3 install --no-cache-dir --break-system-packages \
    scapy \
    pymodbus \
    python-snap7 \
    opcua \
    requests \
    pycryptodome \
    paramiko \
    impacket

# Install industrial security tools
WORKDIR /opt

# ISF (Industrial Exploitation Framework) - similar to Metasploit but for ICS
RUN git clone https://github.com/dark-lbp/isf.git && \
    cd isf && \
    pip3 install --no-cache-dir --break-system-packages -r requirements.txt || true

# Modbus penetration testing tools (make optional if repo is unavailable)
RUN git clone https://github.com/enddo/smod.git && \
    cd smod && \
    pip3 install --no-cache-dir --break-system-packages -r requirements.txt || \
    echo "SMOD installation skipped (repository unavailable)"

# S7comm tools for Siemens PLCs
RUN git clone https://github.com/klsecservices/s7scan.git || \
    echo "s7scan installation skipped (repository unavailable)"

# PLCinject for Modbus attacks
RUN git clone https://github.com/SCADACS/PLCinject.git || \
    echo "PLCinject installation skipped (repository unavailable)"

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
# Mark desktop launchers as trusted\n\
for desktop_file in /root/Desktop/*.desktop; do\n\
  if [ -f "$desktop_file" ]; then\n\
    gio set "$desktop_file" metadata::trusted true 2>/dev/null || true\n\
  fi\n\
done\n\
exec startxfce4' > /root/.vnc/xstartup \
    && chmod +x /root/.vnc/xstartup

# Create XFCE config directory and backgrounds directory
RUN mkdir -p /root/.config/xfce4/xfconf/xfce-perchannel-xml /usr/share/backgrounds

# Copy attack machine background
COPY attack-background.png /usr/share/backgrounds/attack-background.png

# Configure XFCE to use the attack machine background
RUN echo '<?xml version="1.0" encoding="UTF-8"?>\n\
<channel name="xfce4-desktop" version="1.0">\n\
  <property name="backdrop" type="empty">\n\
    <property name="screen0" type="empty">\n\
      <property name="monitor0" type="empty">\n\
        <property name="workspace0" type="empty">\n\
          <property name="color-style" type="int" value="0"/>\n\
          <property name="image-style" type="int" value="5"/>\n\
          <property name="last-image" type="string" value="/usr/share/backgrounds/attack-background.png"/>\n\
        </property>\n\
      </property>\n\
      <property name="monitorVNC-0" type="empty">\n\
        <property name="workspace0" type="empty">\n\
          <property name="color-style" type="int" value="0"/>\n\
          <property name="image-style" type="int" value="5"/>\n\
          <property name="last-image" type="string" value="/usr/share/backgrounds/attack-background.png"/>\n\
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
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create workspace directory
RUN mkdir -p /root/Desktop/workspace
WORKDIR /root/Desktop/workspace

# Create desktop shortcuts for common tools
RUN mkdir -p /root/Desktop && \
    echo '[Desktop Entry]\n\
Version=1.0\n\
Type=Application\n\
Name=Terminal\n\
Comment=Kali Terminal\n\
Exec=xfce4-terminal\n\
Icon=utilities-terminal\n\
Terminal=false\n\
Categories=System;' > /root/Desktop/terminal.desktop && \
    chmod +x /root/Desktop/terminal.desktop && \
    echo '[Desktop Entry]\n\
Version=1.0\n\
Type=Application\n\
Name=Wireshark\n\
Comment=Network Protocol Analyzer\n\
Exec=wireshark\n\
Icon=wireshark\n\
Terminal=false\n\
Categories=Network;' > /root/Desktop/wireshark.desktop && \
    chmod +x /root/Desktop/wireshark.desktop && \
    echo '[Desktop Entry]\n\
Version=1.0\n\
Type=Application\n\
Name=Firefox\n\
Comment=Web Browser\n\
Exec=firefox-esr\n\
Icon=firefox-esr\n\
Terminal=false\n\
Categories=Network;' > /root/Desktop/firefox.desktop && \
    chmod +x /root/Desktop/firefox.desktop && \
    echo '[Desktop Entry]\n\
Version=1.0\n\
Type=Application\n\
Name=Metasploit Console\n\
Comment=Launch msfconsole\n\
Exec=xfce4-terminal -e msfconsole\n\
Icon=kali-menu\n\
Terminal=false\n\
Categories=Security;' > /root/Desktop/metasploit.desktop && \
    chmod +x /root/Desktop/metasploit.desktop

# Create targets reference file on Desktop
RUN echo 'CybICS Network Information\n\
==========================\n\
\n\
Your task: Discover and enumerate the ICS/SCADA target systems\n\
in this virtual environment.\n\
\n\
Network Hints:\n\
--------------\n\
- You are inside a Docker network (172.18.0.0/24)\n\
- Use hostnames (e.g., openplc, fuxa) or IP addresses\n\
- Common ICS/SCADA services run on standard ports\n\
- Web interfaces typically use ports 1881, 8080, 8090\n\
- Industrial protocols: Modbus TCP (502), S7comm (102), OPC-UA (4840)\n\
\n\
Important:\n\
- DO NOT use 127.0.0.x addresses - they only work on the host\n\
- Use Docker network addresses or hostnames instead\n\
- Start with network scanning to discover live hosts\n\
\n\
Getting Started:\n\
- Scan the network: nmap -sV 172.18.0.0/24\n\
- Identify services and their versions\n\
- Look for web interfaces, PLCs, HMIs, and SCADA systems\n' > /root/Desktop/TARGETS.txt

# Create a welcome message for terminal
RUN echo '#!/bin/bash\n\
echo ""\n\
echo "  ██████╗██╗   ██╗██████╗ ██╗ ██████╗███████╗"\n\
echo " ██╔════╝╚██╗ ██╔╝██╔══██╗██║██╔════╝██╔════╝"\n\
echo "██║      ╚████╔╝ ██████╔╝██║██║     ███████╗"\n\
echo "██║       ╚██╔╝  ██╔══██╗██║██║     ╚════██║"\n\
echo "╚██████╗   ██║   ██████╔╝██║╚██████╗███████║"\n\
echo " ╚═════╝   ╚═╝   ╚═════╝ ╚═╝ ╚═════╝╚══════╝"\n\
echo ""\n\
echo "CybICS Attack Machine - ICS/OT Security Training Platform"\n\
echo "========================================================="\n\
echo ""\n\
echo "Mission: Discover and assess ICS/SCADA systems in the network"\n\
echo "Network: 172.18.0.0/24 (see ~/Desktop/TARGETS.txt for hints)"\n\
echo ""\n\
echo "Available Tools:"\n\
echo "  Network Scanning: nmap, masscan"\n\
echo "  Protocol Analysis: wireshark, tshark"\n\
echo "  ICS Frameworks: ISF (/opt/isf), SMOD (/opt/smod)"\n\
echo "  Modbus Tools: pymodbus, PLCinject (/opt/PLCinject)"\n\
echo "  S7 Tools: snap7, s7scan (/opt/s7scan)"\n\
echo "  Exploitation: metasploit-framework"\n\
echo "  Web Testing: nikto, sqlmap, dirb"\n\
echo "  Password Attacks: hydra, john, hashcat"\n\
echo ""\n\
echo "Quick Start:"\n\
echo "  - Read hints:   cat ~/Desktop/TARGETS.txt"\n\
echo "  - Scan network: nmap -sV 172.18.0.0/24"\n\
echo "  - Find PLCs:    nmap --script modbus-discover 172.18.0.0/24"\n\
echo "  - Launch ISF:   cd /opt/isf && python3 isf.py"\n\
echo ""\n' > /usr/local/bin/welcome && \
    chmod +x /usr/local/bin/welcome

# Set up bash to show welcome message
RUN echo 'welcome' >> /root/.bashrc

# Initialize Metasploit database
RUN msfdb init || true

# Expose VNC and noVNC ports
EXPOSE 5902 6081

WORKDIR /root

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
