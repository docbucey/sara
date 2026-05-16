#!/usr/bin/env bash
# =============================================================================
#  sara_rpi_setup.sh
#  Run once on a fresh Raspberry Pi OS Lite (64-bit) to turn the RPi into
#  a headless SARA control node with a WiFi access point.
#
#  Tested: RPi Zero 2W, RPi 3B, RPi 3B+
#  OS:     Raspberry Pi OS Lite (Bookworm, 64-bit)
#
#  After this script:
#    - RPi broadcasts WiFi:  SARA-NET  (password: sarabridge)
#    - RPi static IP on AP:  192.168.42.1
#    - SARA control server:  http://192.168.42.1:5050
#    - Auto-starts on boot via systemd
#
#  On the Windows PC, set:
#    $env:SARA_HOST = "192.168.42.1:5050"   # in PowerShell
#    setx SARA_HOST "192.168.42.1:5050"     # permanent (run_sara.bat)
#  Then launch SARA.exe — VALANCE will find CONTROL on the RPi.
# =============================================================================

set -e

SARA_DIR="/opt/sara"
SARA_USER="sara"
AP_SSID="SARA-NET"
AP_PASS="sarabridge"
AP_IP="192.168.42.1"
AP_RANGE_START="192.168.42.10"
AP_RANGE_END="192.168.42.50"

echo "=== SARA RPi Setup ==="
echo "  AP SSID : $AP_SSID"
echo "  AP IP   : $AP_IP"
echo "  SARA dir: $SARA_DIR"
echo ""

# ── 1. System packages ───────────────────────────────────────────────────────
echo "[1/7] Installing system packages..."
apt-get update -qq
apt-get install -y \
    python3 python3-pip python3-venv \
    hostapd dnsmasq \
    git curl

# ── 2. SARA user ─────────────────────────────────────────────────────────────
echo "[2/7] Creating sara system user..."
id -u "$SARA_USER" &>/dev/null || useradd -r -s /usr/sbin/nologin "$SARA_USER"

# ── 3. Copy/link SARA source ─────────────────────────────────────────────────
echo "[3/7] Setting up SARA directory at $SARA_DIR..."
# If the SARA repo is already here (SD card flashed with repo), link it.
# Otherwise clone from GitHub.
if [ -d "/home/pi/sara" ]; then
    ln -sfn /home/pi/sara "$SARA_DIR"
else
    git clone https://github.com/docbucey/sara.git "$SARA_DIR"
fi
chown -R "$SARA_USER":"$SARA_USER" "$SARA_DIR"

# ── 4. Python venv + deps ────────────────────────────────────────────────────
echo "[4/7] Creating Python venv and installing requirements..."
sudo -u "$SARA_USER" python3 -m venv "$SARA_DIR/venv"
if [ -f "$SARA_DIR/requirements.txt" ]; then
    sudo -u "$SARA_USER" "$SARA_DIR/venv/bin/pip" install -q -r "$SARA_DIR/requirements.txt"
fi
# Minimal deps if no requirements.txt yet
sudo -u "$SARA_USER" "$SARA_DIR/venv/bin/pip" install -q flask requests

# ── 5. systemd service ───────────────────────────────────────────────────────
echo "[5/7] Installing sara-control systemd service..."
cat > /etc/systemd/system/sara-control.service << EOF
[Unit]
Description=SARA Control Server
After=network.target

[Service]
Type=simple
User=$SARA_USER
WorkingDirectory=$SARA_DIR
ExecStart=$SARA_DIR/venv/bin/python $SARA_DIR/sara_control/server_con.py --http --host 0.0.0.0 --port 5050
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sara-control
systemctl start sara-control

# ── 6. WiFi Access Point (hostapd + dnsmasq) ─────────────────────────────────
echo "[6/7] Configuring WiFi AP ($AP_SSID)..."

# Static IP for wlan0
cat > /etc/dhcpcd.conf.d/sara-ap.conf << EOF
interface wlan0
    static ip_address=$AP_IP/24
    nohook wpa_supplicant
EOF

# Append to dhcpcd.conf if the drop-in dir doesn't exist (older OS)
if [ ! -d /etc/dhcpcd.conf.d ]; then
    echo -e "\ninterface wlan0\n    static ip_address=$AP_IP/24\n    nohook wpa_supplicant" \
        >> /etc/dhcpcd.conf
    rm -f /etc/dhcpcd.conf.d/sara-ap.conf
fi

# hostapd config
cat > /etc/hostapd/sara.conf << EOF
interface=wlan0
driver=nl80211
ssid=$AP_SSID
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$AP_PASS
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
echo 'DAEMON_CONF="/etc/hostapd/sara.conf"' >> /etc/default/hostapd

# dnsmasq DHCP config
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig 2>/dev/null || true
cat > /etc/dnsmasq.conf << EOF
interface=wlan0
dhcp-range=$AP_RANGE_START,$AP_RANGE_END,255.255.255.0,24h
# Resolve "sara" hostname to the RPi
address=/sara/$AP_IP
EOF

# Enable hostapd
systemctl unmask hostapd
systemctl enable hostapd
systemctl start hostapd
systemctl restart dnsmasq

# ── 7. Done ──────────────────────────────────────────────────────────────────
echo ""
echo "[7/7] Setup complete."
echo ""
echo "  WiFi AP  : $AP_SSID  (password: $AP_PASS)"
echo "  RPi IP   : $AP_IP"
echo "  SARA URL : http://$AP_IP:5050/health"
echo ""
echo "  On the Windows PC, run ONE of these:"
echo "    PowerShell: \$env:SARA_HOST = '$AP_IP:5050'"
echo "    Permanent : setx SARA_HOST '$AP_IP:5050'"
echo "    Or edit   : run_sara.bat and add SET SARA_HOST=$AP_IP:5050"
echo ""
echo "  Then launch SARA.exe and check the green 'SARA ready' LED."
