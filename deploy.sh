#!/bin/bash
# Deploy homelab dashboard to monitoring container (192.168.1.127)
set -e
TARGET=root@192.168.1.127
SSH="ssh -o StrictHostKeyChecking=no $TARGET"
SCP="scp -o StrictHostKeyChecking=no"

echo "==> Installing API deps..."
$SSH "apt-get install -y python3-venv python3-pip > /dev/null 2>&1"
$SSH "mkdir -p /opt/homelab-api"
$SCP api/main.py api/requirements.txt $TARGET:/opt/homelab-api/
$SSH "cd /opt/homelab-api && python3 -m venv venv && venv/bin/pip install -q -r requirements.txt"

echo "==> Deploying frontend..."
$SCP www/index.html $TARGET:/var/www/html/index.html
# Only copy services.json if it doesn't already exist (preserve live edits)
$SSH "[ -f /var/www/html/services.json ] || true"
$SCP www/services.json $TARGET:/var/www/html/services.json.default
$SSH "[ -f /var/www/html/services.json ] || cp /var/www/html/services.json.default /var/www/html/services.json"
$SSH "chown www-data:www-data /var/www/html/services.json"

echo "==> Installing systemd service..."
$SCP systemd/homelab-api.service $TARGET:/etc/systemd/system/homelab-api.service
$SSH "systemctl daemon-reload && systemctl enable --now homelab-api"

echo "==> Updating nginx config..."
$SCP nginx/homelab.conf $TARGET:/etc/nginx/sites-available/default
$SSH "nginx -t && systemctl reload nginx"

echo "==> Done. Dashboard: http://192.168.1.127"
