#!/bin/bash
set -e

echo "Starting Deployment..."

# 1. Install System Dependencies
echo "[1/5] Installing system dependencies..."
apt-get update
apt-get install -y python3-pip python3-venv nginx curl

# Install Node.js 20.x (LTS)
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

# 2. Setup Backend
echo "[2/5] Setting up Backend..."
cd /root/QSnap/backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
# Using --timeout to prevent timeouts on large packages like torch
pip install --timeout=1000 -r requirements.txt
deactivate

# 3. Setup Frontend
echo "[3/5] Setting up Frontend..."
cd /root/QSnap/frontend
# Configure API URL for production build
echo "NEXT_PUBLIC_API_URL=/api" > .env.production

npm install
npm run build

# 4. Configure Services
echo "[4/5] Configuring Services..."
cp /root/QSnap/deployment/qsnap-backend.service /etc/systemd/system/
cp /root/QSnap/deployment/qsnap-frontend.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable qsnap-backend
systemctl enable qsnap-frontend

echo "Restarting services..."
systemctl restart qsnap-backend
systemctl restart qsnap-frontend

# 5. Configure Nginx
echo "[5/5] Configuring Nginx..."
cp /root/QSnap/deployment/nginx.conf /etc/nginx/sites-available/qsnap
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/qsnap /etc/nginx/sites-enabled/

systemctl restart nginx

echo "========================================"
echo "Deployment Finished Successfully!"
echo "Your app should be live on port 80."
echo "========================================"
