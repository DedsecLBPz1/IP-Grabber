cat > install.sh << 'EOF'
#!/bin/bash
# IP Tracker/Grabber - installer (Created by Karim Mantash (DedsecLB))

echo "[*] Installing dependencies..."
if command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y python3 python3-pip python3-flask python3-requests git
fi

echo "[*] Installing pyngrok..."
pip3 install pyngrok --break-system-packages 2>/dev/null || pip3 install pyngrok

echo "[*] Installing ipgrab command..."
sudo cp ip_grabber.py /usr/local/bin/ipgrab
sudo chmod +x /usr/local/bin/ipgrab

echo "[+] Done! Run it with: ipgrab"
echo "[!] First time? Set your ngrok token: ngrok config add-authtoken <YOUR_TOKEN>"
EOF
chmod +x install.sh
