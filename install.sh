#!/bin/bash
# IP Tracker/Grabber - installer (Created by Karim Mantash (DedsecLB))

echo "[*] Installing dependencies..."
if command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y python3 python3-pip python3-flask python3-requests curl
fi

echo "[*] Installing pyngrok cleanup (not needed)..."
pip3 uninstall -y pyngrok >/dev/null 2>&1

# --- Install cloudflared ---
echo "[*] Installing cloudflared..."
if ! command -v cloudflared >/dev/null 2>&1; then
    ARCH=$(dpkg --print-architecture 2>/dev/null || uname -m)
    case "$ARCH" in
        amd64|x86_64) CF_ARCH="amd64" ;;
        arm64|aarch64) CF_ARCH="arm64" ;;
        armv7l|armhf) CF_ARCH="arm" ;;
        i386|i686) CF_ARCH="386" ;;
        *) echo "[!] Unknown arch $ARCH, defaulting to amd64"; CF_ARCH="amd64" ;;
    esac
    curl -L --output /tmp/cloudflared.deb \
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}.deb"
    sudo dpkg -i /tmp/cloudflared.deb || sudo apt-get install -f -y
    rm -f /tmp/cloudflared.deb
else
    echo "[*] cloudflared already installed"
fi

# --- Install ipgrab command ---
echo "[*] Installing ipgrab command..."
sudo cp ip_grabber.py /usr/local/bin/ipgrab
sudo chmod +x /usr/local/bin/ipgrab

echo ""
echo "[+] Done! Run it with: ipgrab"
echo "[+] No account or token needed — Cloudflare quick tunnel is free and anonymous"
