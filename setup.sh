#!/bin/bash
set -e
apt-get update -qq && apt-get install -y -qq python3 python3-pip
mkdir -p /opt/vkusmorey
cd /opt/vkusmorey
pip3 install -q -r requirements.txt
cat > /etc/systemd/system/vkusmorey-excursions.service <<'EOF'
[Unit]
Description=x
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/vkusmorey
Environment=BOT_DIR=/opt/vkusmorey
EnvironmentFile=/opt/vkusmorey/.env
ExecStart=/usr/bin/python3 /opt/vkusmorey/bot_excursions.py
Restart=always
RestartSec=10
StartLimitBurst=0

[Install]
WantedBy=multi-user.target
EOF
cat > /etc/systemd/system/vkusmorey-products.service <<'EOF'
[Unit]
Description=x
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/vkusmorey
Environment=BOT_DIR=/opt/vkusmorey
EnvironmentFile=/opt/vkusmorey/.env
ExecStart=/usr/bin/python3 /opt/vkusmorey/bot_products.py
Restart=always
RestartSec=10
StartLimitBurst=0

[Install]
WantedBy=multi-user.target
EOF
cat > /etc/systemd/system/vkusmorey-vk.service <<'EOF'
[Unit]
Description=x
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/vkusmorey
Environment=BOT_DIR=/opt/vkusmorey
EnvironmentFile=/opt/vkusmorey/.env
ExecStart=/usr/bin/python3 /opt/vkusmorey/bot_vk.py
Restart=always
RestartSec=10
StartLimitBurst=0

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now vkusmorey-excursions vkusmorey-products vkusmorey-vk
systemctl status vkusmorey-excursions --no-pager
