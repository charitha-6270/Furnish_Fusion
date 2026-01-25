#!/bin/bash
# EC2 User Data Script for Furnish Fusion
# This script runs when the EC2 instance starts

# Update system
yum update -y

# Install Python 3.11
yum install -y python3.11 python3.11-pip

# Create application directory
mkdir -p /opt/furnish-fusion
cd /opt/furnish-fusion

# Note: Application files should be copied here manually or via deployment script
# This script sets up the environment

# Install Python dependencies (will be done after files are copied)
# pip3.11 install -r requirements.txt

# Create systemd service file
cat > /etc/systemd/system/furnish-fusion.service <<EOF
[Unit]
Description=Furnish Fusion Flask Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/furnish-fusion
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="SECRET_KEY=CHANGE_THIS_IN_PRODUCTION"
Environment="AWS_REGION=us-east-1"
Environment="SNS_TOPIC_ARN=YOUR_SNS_TOPIC_ARN"
Environment="DEBUG=False"
ExecStart=/usr/local/bin/gunicorn --bind 0.0.0.0:8000 --workers 4 aws_app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable service (but don't start yet - files need to be copied first)
systemctl daemon-reload
systemctl enable furnish-fusion

echo "EC2 setup complete. Copy application files and install dependencies, then start service."

