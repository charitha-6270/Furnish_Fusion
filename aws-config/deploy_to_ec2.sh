#!/bin/bash
# Deployment script for Furnish Fusion to EC2
# Usage: ./deploy_to_ec2.sh

set -e

# Configuration - UPDATE THESE VALUES
EC2_SSH_KEY="${EC2_SSH_KEY:-/path/to/your-key.pem}"
EC2_HOST="${EC2_HOST:-ec2-user@your-ec2-ip}"
APP_DIR="/opt/furnish-fusion"

echo "🚀 Deploying Furnish Fusion to EC2..."
echo "Host: $EC2_HOST"
echo ""

# Check if key file exists
if [ ! -f "$EC2_SSH_KEY" ]; then
    echo "❌ SSH key file not found: $EC2_SSH_KEY"
    echo "   Set EC2_SSH_KEY environment variable or update the script"
    exit 1
fi

# Create deployment package (exclude unnecessary files)
echo "📦 Creating deployment package..."
zip -r deploy.zip . \
    -x "*.git*" \
    -x "*__pycache__*" \
    -x "*.pyc" \
    -x "*.pyo" \
    -x "*.pyd" \
    -x ".DS_Store" \
    -x "*.log" \
    -x "deploy.zip" \
    -x "aws-config/deploy_to_ec2.sh" \
    -x "aws-config/ec2_user_data.sh"

echo "✅ Package created: deploy.zip"
echo ""

# Copy files to EC2
echo "📤 Copying files to EC2..."
scp -i "$EC2_SSH_KEY" deploy.zip "$EC2_HOST:/tmp/"

# SSH and deploy
echo "🔧 Setting up application on EC2..."
ssh -i "$EC2_SSH_KEY" "$EC2_HOST" << 'ENDSSH'
    # Create app directory
    sudo mkdir -p /opt/furnish-fusion
    sudo chown ec2-user:ec2-user /opt/furnish-fusion
    cd /opt/furnish-fusion
    
    # Extract files
    unzip -o /tmp/deploy.zip -d .
    rm /tmp/deploy.zip
    
    # Install dependencies
    pip3.11 install -r requirements.txt --user
    
    # Restart service
    sudo systemctl restart furnish-fusion
    sudo systemctl status furnish-fusion
ENDSSH

# Cleanup
rm deploy.zip

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Update environment variables in /etc/systemd/system/furnish-fusion.service"
echo "2. Restart service: sudo systemctl restart furnish-fusion"
echo "3. Check logs: sudo journalctl -u furnish-fusion -f"
echo "4. Access application: http://$EC2_HOST:8000"

