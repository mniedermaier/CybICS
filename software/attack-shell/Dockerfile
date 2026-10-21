# The attack shell: a small attacker host inside the plant network
# (172.18.0.100) with a terminal in the browser.  It is what the board has in
# place of the Kali attack machine, which at 6 GB does not fit a Pi Zero 2 W,
# and it keeps attack tools out of the landing container, whose memory limit a
# single scan from its webshell could exhaust.
#
# Built from the repository root, like the landing image, so that it can carry
# its own copy of training/.
FROM python:3.12-alpine

RUN apk add --no-cache \
    bash \
    bash-completion \
    ttyd \
    tmux \
    nmap \
    nmap-scripts \
    nmap-nselibs \
    curl \
    wget \
    bind-tools \
    netcat-openbsd \
    socat \
    tcpdump \
    iproute2 \
    iputils \
    iptables \
    hydra \
    ffuf \
    git \
    picocom \
    vim \
    nano \
    less \
    procps

COPY software/attack-shell/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# nmap's list of 5000 common passwords stands in for rockyou (134 MB) and
# covers the lab's weak logins.
RUN mkdir -p /usr/share/wordlists \
    && ln -s /usr/share/nmap/nselib/data/passwords.lst /usr/share/wordlists/passwords.txt \
    && ln -s /usr/share/nmap/nselib/data/usernames.lst /usr/share/wordlists/usernames.txt

WORKDIR /CybICS
COPY training/ training/
# The opcua module's leaked admin certificate; its README sends students to
# this path.
COPY software/opcua/certificates/ software/opcua/certificates/
COPY training/flood_overwrite/flooding_hpt.py /usr/local/bin/flooding_hpt.py
RUN chmod +x /usr/local/bin/flooding_hpt.py

COPY software/attack-shell/bashrc /root/.bashrc
RUN echo ". ~/.bashrc" > /root/.bash_profile
COPY software/attack-shell/tmux.conf /root/.tmux.conf
COPY software/attack-shell/motd /etc/motd

# Script output shows up as it is printed, not when the script ends.
ENV PYTHONUNBUFFERED=1
# The training scripts and READMEs address the device as $DEVICE_IP.  From
# inside the plant network that is the bridge gateway, the host that publishes
# every service, the IDS and the landing page included.
ENV DEVICE_IP=172.18.0.1
ENV TERM=xterm-256color
WORKDIR /root

EXPOSE 7681

# Every browser tab attaches to the same tmux session, so a scan keeps running
# when the dashboard unloads the terminal and is still there on return.
CMD ["ttyd", "--writable", "--port", "7681", \
     "--client-option", "fontSize=14", \
     "--client-option", "titleFixed=CybICS attack shell", \
     "--client-option", "disableLeaveAlert=true", \
     "--client-option", "theme={\"background\":\"#0a0a0a\",\"foreground\":\"#e6e6e6\",\"cursor\":\"#ff6b00\",\"selectionBackground\":\"#ff6b0055\"}", \
     "tmux", "new-session", "-A", "-s", "cybics"]
