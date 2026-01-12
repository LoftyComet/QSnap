#!/bin/bash
set -e

echo "=========================================="
echo "   Restarting QSnap Server Applications   "
echo "=========================================="

# 1. Cleaning up Nginx Default Config (Fixes 'Welcome to nginx' page)
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "[Nginx] Removing default configuration..."
    rm -f /etc/nginx/sites-enabled/default
fi

# 2. Ensure QSnap Nginx Config is active
if [ ! -f /etc/nginx/sites-enabled/qsnap ]; then
    if [ -f /root/QSnap/deployment/nginx.conf ]; then
        echo "[Nginx] Installing QSnap configuration..."
        cp /root/QSnap/deployment/nginx.conf /etc/nginx/sites-available/qsnap
        ln -sf /etc/nginx/sites-available/qsnap /etc/nginx/sites-enabled/
    else
        echo "Error: /root/QSnap/deployment/nginx.conf not found!"
        exit 1
    fi
fi

# 3. Restart Services
echo "[Systemd] Restarting Backend..."
systemctl restart qsnap-backend

echo "[Systemd] Restarting Frontend..."
systemctl restart qsnap-frontend

echo "[Systemd] Restarting Nginx..."
systemctl restart nginx

# 4. Show Status
echo "=========================================="
echo "             Service Status               "
echo "=========================================="
systemctl status qsnap-backend qsnap-frontend nginx --no-pager | grep "Active:" -B 2

echo ""
echo "Done! You can access the site at http://$(curl -s ifconfig.me)"

# ./start_server.sh
# journalctl -u qsnap-backend -n 50 --no-pager
# sudo systemctl stop qsnap-backend qsnap-frontend nginx
