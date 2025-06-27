#!/bin/bash

# Docker EC2 Chat WebApp Deployment Script
# Run this script on a fresh Ubuntu instance to set up the application

set -e  # Exit on any error

echo "=========================================="
echo "Docker EC2 Chat WebApp Deployment Script"
echo "=========================================="
echo "Starting deployment at $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root!"
    print_error "Run as ubuntu user: ./deploy.sh"
    exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update

# Install required packages
print_status "Installing required packages (curl, git)..."
sudo apt install -y curl git

# Install Docker
print_status "Installing Docker..."
if command -v docker &> /dev/null; then
    print_warning "Docker is already installed"
    # Make sure Docker service is running
    sudo systemctl enable docker
    sudo systemctl start docker
else
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    sudo systemctl enable docker
    sudo systemctl start docker
    rm get-docker.sh
    print_success "Docker installed successfully"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if command -v docker-compose &> /dev/null; then
    print_warning "Docker Compose is already installed"
else
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
fi

# Check Docker group membership
if groups $USER | grep -q docker; then
    print_success "User is already in docker group"
else
    print_warning "User needs to be added to docker group"
    sudo usermod -aG docker $USER
    print_warning "You may need to log out and back in for group changes to take effect"
    print_warning "Or run: newgrp docker"
fi

# Wait for Docker to be ready
print_status "Waiting for Docker to be ready..."
sudo systemctl start docker
sleep 10

# Check Docker with timeout
DOCKER_TIMEOUT=60  # 60 seconds timeout
DOCKER_COUNTER=0

print_status "Checking Docker status..."
while ! docker info > /dev/null 2>&1; do
    if [ $DOCKER_COUNTER -ge $DOCKER_TIMEOUT ]; then
        print_error "Docker failed to start within $DOCKER_TIMEOUT seconds"
        print_error "Trying to fix Docker group permission issue..."
        
        # Try to fix group membership issue
        print_status "Applying group changes with newgrp..."
        if newgrp docker <<< 'docker info > /dev/null 2>&1'; then
            print_success "Docker is now accessible!"
            break
        else
            print_error "Docker group fix failed. Manual intervention required:"
            print_error "1. Check Docker service: sudo systemctl status docker"
            print_error "2. Restart Docker: sudo systemctl restart docker"
            print_error "3. Check logs: sudo journalctl -u docker -n 20"
            print_error "4. Try: newgrp docker"
            exit 1
        fi
    fi
    
    print_status "Docker not ready yet, waiting... (${DOCKER_COUNTER}s/${DOCKER_TIMEOUT}s)"
    sleep 5
    DOCKER_COUNTER=$((DOCKER_COUNTER + 5))
done

print_success "Docker is ready!"

# Clone repository
print_status "Cloning repository..."
cd ~
if [ -d "docker-ec2-webapp" ]; then
    print_warning "Repository already exists, pulling latest changes..."
    cd docker-ec2-webapp
    git pull origin main
else
    git clone https://github.com/AkashBhat14/docker-ec2-webapp.git
    cd docker-ec2-webapp
    print_success "Repository cloned successfully"
fi

# Get public IP
print_status "Getting EC2 public IP..."
if curl -s http://169.254.169.254/latest/meta-data/public-ipv4 > /dev/null 2>&1; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    print_success "Public IP detected: $PUBLIC_IP"
else
    print_warning "Could not detect EC2 public IP, using localhost"
    PUBLIC_IP="localhost"
fi

# Create environment file
print_status "Creating environment file..."
cat > .env << EOF
# Docker EC2 Chat WebApp Environment Configuration
# Generated on $(date)

# Google Gemini AI API Key (REPLACE WITH YOUR ACTUAL KEY)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# S3 Bucket for chat history storage
S3_BUCKET_NAME=akash-chat-app-bucket-2025

# API URL for frontend to connect to backend
NEXT_PUBLIC_API_URL=http://${PUBLIC_IP}:5000
EOF

print_success "Environment file created"
print_warning "⚠️  IMPORTANT: Edit .env file and replace 'your_actual_gemini_api_key_here' with your real Gemini API key!"

# Check if user wants to edit the API key now
echo ""
read -p "Do you want to edit the Gemini API key now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your Gemini API key: " -r GEMINI_KEY
    if [ ! -z "$GEMINI_KEY" ]; then
        sed -i "s/your_actual_gemini_api_key_here/$GEMINI_KEY/g" .env
        print_success "API key updated in environment file"
    fi
fi

# Build and start containers
print_status "Building and starting Docker containers..."
print_status "This may take several minutes..."

# Try to run docker-compose, if it fails due to permissions, try with newgrp
if docker-compose up --build -d; then
    print_success "Containers started successfully"
else
    print_warning "Docker compose failed, trying with newgrp docker..."
    if newgrp docker <<< 'docker-compose up --build -d'; then
        print_success "Containers started successfully with newgrp"
    else
        print_error "Failed to start containers even with newgrp"
        print_error "Manual steps to fix:"
        print_error "1. Log out and log back in"
        print_error "2. Or run: newgrp docker"
        print_error "3. Then run: docker-compose up --build -d"
        exit 1
    fi
fi

# Wait for services to start
print_status "Waiting for services to start up..."
sleep 30

# Test services
print_status "Testing services..."

# Test backend
if curl -s http://localhost:5000/ > /dev/null; then
    print_success "✅ Backend is running"
    BACKEND_STATUS="Running"
else
    print_warning "❌ Backend may not be ready yet"
    BACKEND_STATUS="Check logs"
fi

# Test frontend
if curl -s http://localhost:3000/ > /dev/null; then
    print_success "✅ Frontend is running"
    FRONTEND_STATUS="Running"
else
    print_warning "❌ Frontend may not be ready yet"
    FRONTEND_STATUS="Check logs"
fi

# Test S3 (if configured)
if curl -s http://localhost:5000/s3/status > /dev/null; then
    print_success "✅ S3 integration is working"
    S3_STATUS="Connected"
else
    print_warning "⚠️  S3 integration needs IAM role configuration"
    S3_STATUS="Configure IAM role"
fi

# Create deployment summary
print_status "Creating deployment summary..."
cat > ~/DEPLOYMENT_SUMMARY.txt << EOF
Docker EC2 Chat WebApp - Deployment Summary
==========================================
Deployment completed at: $(date)

Application URLs:
- Frontend: http://${PUBLIC_IP}:3000 (${FRONTEND_STATUS})
- Backend:  http://${PUBLIC_IP}:5000 (${BACKEND_STATUS})
- S3 Status: http://${PUBLIC_IP}:5000/s3/status (${S3_STATUS})

Docker Information:
- Docker version: $(docker --version)
- Docker Compose version: $(docker-compose --version)

Container Status:
$(docker-compose ps)

Next Steps:
1. Edit .env file if you haven't set your Gemini API key yet
2. If you see permission errors, run: newgrp docker
3. Check logs: docker-compose logs
4. Restart if needed: docker-compose restart

Troubleshooting:
- View logs: docker-compose logs
- Restart app: docker-compose restart
- Rebuild: docker-compose down && docker-compose up --build -d
- Check environment: cat .env
EOF

# Final summary
echo ""
echo "=========================================="
print_success "🎉 DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
print_success "Your Docker EC2 Chat WebApp is now running!"
echo ""
echo "📱 Application URLs:"
echo "   Frontend: http://${PUBLIC_IP}:3000"
echo "   Backend:  http://${PUBLIC_IP}:5000"
echo ""
echo "📋 Summary file created: ~/DEPLOYMENT_SUMMARY.txt"
echo ""
echo "🔧 Quick commands:"
echo "   Check status:    docker-compose ps"
echo "   View logs:       docker-compose logs"
echo "   Restart:         docker-compose restart"
echo "   Stop:            docker-compose down"
echo ""
if [ "$PUBLIC_IP" = "localhost" ]; then
    print_warning "⚠️  Could not detect public IP. Update security groups to allow ports 3000 and 5000"
fi
echo ""
print_success "🚀 Happy chatting!"
echo "==========================================" 