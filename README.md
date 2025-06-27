# Docker EC2 Chat WebApp

A full-stack chat application built with Next.js frontend and FastAPI backend, containerized with Docker and deployed on AWS EC2.

## 🏗️ Architecture

- **Frontend**: Next.js 15 with TypeScript, Tailwind CSS, and shadcn/ui components
- **Backend**: FastAPI with Python, integrated with Google Gemini AI
- **Deployment**: Docker containers on AWS EC2
- **AI Integration**: Google Gemini 2.5 Flash for chat responses

## 📋 Prerequisites

- AWS account with EC2 access
- Google AI Studio account for Gemini API key
- Basic knowledge of Docker and AWS

## 🚀 Local Development Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd docker-ec2-webapp
```

### 2. Environment Configuration
Create a `.env` file in the project root:
```bash
# Google Gemini API Key
GEMINI_API_KEY="your_gemini_api_key_here"

# API URL (for local development)
NEXT_PUBLIC_API_URL="http://localhost:5000"
```

### 3. Run Locally with Docker Compose
```bash
# Start all services
docker-compose up --build

# Run in detached mode
docker-compose up --build -d

# View logs
docker-compose logs -f
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## 🌩️ AWS EC2 Deployment

### 🔑 Prerequisites: IAM Role Setup (Required for S3 Features)

Before deploying, create an IAM role for your EC2 instance to access S3:

#### Step 1: Create S3 Bucket

1. **AWS Console → S3 → Create bucket**
2. **Bucket name**: `akash-chat-app-bucket-2025` (or your chosen name)
3. **Region**: Choose same region as your EC2 instance
4. **Keep default settings** for permissions and configuration
5. **Create bucket**

#### Step 2: Create IAM Policy

1. **AWS Console → IAM → Policies → Create Policy**
2. **Select "JSON" tab** and paste this policy:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "s3:GetObject",
                   "s3:PutObject",
                   "s3:ListBucket"
               ],
               "Resource": [
                   "arn:aws:s3:::akash-chat-app-bucket-2025",
                   "arn:aws:s3:::akash-chat-app-bucket-2025/*"
               ]
           }
       ]
   }
   ```
3. **Name**: `EC2-S3-ChatApp-Policy`
4. **Create policy**

#### Step 3: Create IAM Role

1. **AWS Console → IAM → Roles → Create Role**
2. **Trusted entity**: AWS service
3. **Use case**: EC2
4. **Permissions**: Search and select `EC2-S3-ChatApp-Policy`
5. **Role name**: `EC2-S3-Access-Role`
6. **Create role**

#### Step 4: Attach Role to EC2 (During Launch)

When launching your EC2 instance:
- **IAM Instance Profile**: Select `EC2-S3-Access-Role`

Or for existing instances:
1. **EC2 Console → Instances → Select your instance**
2. **Actions → Security → Modify IAM role**
3. **Select**: `EC2-S3-Access-Role`
4. **Update IAM role**

> **Note**: Without this IAM role, S3 features will be disabled but the chat app will still work locally.

---

Choose from three deployment methods based on your preference:

### 🚀 Option A: Automated Deployment with Cloud-Init (Fastest)

**Perfect for:** One-click deployment, production environments, consistent setups

Use the provided `cloud-init.yaml` script to automatically set up everything on EC2 boot.

#### Step 1: Prepare Your Environment

1. **Get your Gemini API key** from [Google AI Studio](https://aistudio.google.com/)
2. **Note your S3 bucket name**: `akash-chat-app-bucket-2025`
3. **Edit the cloud-init.yaml file** before launching:
   ```yaml
   # In cloud-init.yaml, replace this line:
   echo "GEMINI_API_KEY=your_actual_gemini_api_key_here" > .env
   # With your actual API key:
   echo "GEMINI_API_KEY=AIzaSy..." > .env
   ```

#### Step 2: Launch EC2 Instance with Cloud-Init

1. **AWS Console → EC2 → Launch Instance**
2. **AMI**: Ubuntu 24.04 LTS (recommended) or 22.04 LTS
3. **Instance type**: t2.micro (free tier) or larger
4. **Storage**: 20GB (recommended, 8GB minimum)
5. **Security Group**: Create or select group with these rules:
   ```
   Type: SSH, Port: 22, Source: Your IP (for SSH access)
   Type: Custom TCP, Port: 3000, Source: 0.0.0.0/0 (for frontend)
   Type: Custom TCP, Port: 5000, Source: 0.0.0.0/0 (for backend API)
   ```
6. **IAM Instance Profile**: Attach your `EC2-S3-Access-Role` (see IAM setup below)
7. **Advanced Details → User data**: Copy and paste the entire `cloud-init.yaml` content

#### Step 3: Wait for Automatic Setup (8-10 minutes)

The instance will automatically:
- ✅ Install Docker and Docker Compose
- ✅ Clone your repository
- ✅ Auto-detect EC2 public IP
- ✅ Configure environment variables
- ✅ Build and start containers
- ✅ Test all services

**Monitor progress:**
```bash
# SSH into instance after ~2 minutes
ssh -i your-key.pem ubuntu@your-new-ec2-ip

# Check cloud-init status
sudo cloud-init status

# Check if setup completed successfully
cat /home/ubuntu/SETUP_COMPLETE.txt

# If file exists, your app is ready!
```

#### Step 4: Access Your Application

Your app will be automatically available at:
- **Frontend**: `http://YOUR_EC2_PUBLIC_IP:3000`
- **Backend**: `http://YOUR_EC2_PUBLIC_IP:5000`
- **S3 Status**: `http://YOUR_EC2_PUBLIC_IP:5000/s3/status`

### 🛠️ Option B: Semi-Automated with Deploy Script (Most Flexible)

**Perfect for:** Development, learning, debugging, custom configurations

Use the `deploy.sh` script for step-by-step deployment with interactive options.

#### Step 1: Launch Basic EC2 Instance

1. **AWS Console → EC2 → Launch Instance**
2. **AMI**: Ubuntu 24.04 LTS
3. **Instance type**: t2.micro or larger
4. **Storage**: 20GB recommended
5. **Security Group**: Allow ports 22, 3000, 5000 (same as above)
6. **IAM Instance Profile**: Attach `EC2-S3-Access-Role` (optional for S3 features)

#### Step 2: Run Deploy Script

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Method 1: Direct download and run
curl -o deploy.sh https://raw.githubusercontent.com/AkashBhat14/docker-ec2-webapp/main/deploy.sh
chmod +x deploy.sh
./deploy.sh

# Method 2: Clone repository first
git clone https://github.com/AkashBhat14/docker-ec2-webapp.git
cd docker-ec2-webapp
chmod +x deploy.sh
./deploy.sh
```

#### Step 3: Interactive Setup

The script will:
- ✅ Install all dependencies with progress tracking
- ✅ Prompt you to enter your Gemini API key
- ✅ Auto-detect your EC2 public IP
- ✅ Build and test all services
- ✅ Create a detailed deployment summary

**Expected output:**
```bash
==========================================
Docker EC2 Chat WebApp Deployment Script
==========================================

[INFO] Installing Docker...
[SUCCESS] Docker installed successfully
[INFO] Getting EC2 public IP...
[SUCCESS] Public IP detected: 65.0.139.226

Do you want to edit the Gemini API key now? (y/n): y
Enter your Gemini API key: AIzaSy...
[SUCCESS] API key updated in environment file

[INFO] Building and starting Docker containers...
[SUCCESS] ✅ Backend is running
[SUCCESS] ✅ Frontend is running
[SUCCESS] 🎉 DEPLOYMENT COMPLETE!

Your app is running at: http://65.0.139.226:3000
```

### 🔧 Option C: Manual Deployment

### Step 1: Launch EC2 Instance

1. **Create EC2 Instance**:
   - Instance type: `t2.micro` (free tier)
   - AMI: Ubuntu 22.04 LTS
   - Storage: 20GB (recommended, 8GB minimum)
   - Security Group: Allow ports 22, 3000, 5000

2. **Security Group Configuration**:
   ```
   Type: SSH, Port: 22, Source: Your IP
   Type: Custom TCP, Port: 3000, Source: 0.0.0.0/0
   Type: Custom TCP, Port: 5000, Source: 0.0.0.0/0
   ```

### Step 2: Server Setup

1. **Connect to EC2**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-public-ip
   ```

2. **Install Docker and Docker Compose**:
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Docker
   sudo apt install docker.io -y
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -aG docker ubuntu

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose

   # Logout and login again for group changes to take effect
   exit
   ```

3. **Clone Repository**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-public-ip
   git clone <your-repo-url>
   cd docker-ec2-webapp
   ```

### Step 3: Configuration

1. **Create Environment File**:
   ```bash
   nano .env
   ```

   Add the following content (replace with your values):
   ```env
   # Your Google Gemini API Key
   GEMINI_API_KEY="your_actual_gemini_api_key"

   # Your EC2 Public IP
   NEXT_PUBLIC_API_URL="http://YOUR_EC2_PUBLIC_IP:5000"
   ```

2. **Update Frontend API URL** (if needed):
   The frontend is currently hardcoded to use the IP. If you want to use environment variables, update `frontend/src/app/page.tsx`:
   ```typescript
   const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5000";
   ```

### Step 4: Deploy Application

1. **Build and Start Containers**:
   ```bash
   # Build and start services
   docker-compose up --build -d

   # Check container status
   docker-compose ps

   # View logs
   docker-compose logs -f
   ```

2. **Verify Deployment**:
   - Backend: http://YOUR_EC2_PUBLIC_IP:5000 (should show: `{"message":"Hello from Docker on EC2!"}`)
   - Frontend: http://YOUR_EC2_PUBLIC_IP:3000

## 🐛 Troubleshooting

### Common Issues

#### 1. Frontend Not Connecting to Backend
**Problem**: Frontend shows "Failed to send message" errors.

**Solution**: Check if the API URL is correctly configured:
```bash
# Check container logs
docker-compose logs frontend
docker-compose logs backend

# Verify environment variables
docker exec chat-frontend env | grep NEXT_PUBLIC_API_URL
```

#### 2. Container Build Failures
**Problem**: Build fails with "no space left on device".

**Solution**: Clean up Docker system:
```bash
# Remove unused Docker resources
docker system prune -a --volumes

# Check disk space
df -h

# If still low, increase EBS volume size in AWS Console
```

#### 3. Port Access Issues
**Problem**: Cannot access application from browser.

**Solution**: Verify EC2 Security Group:
- Ensure ports 3000 and 5000 are open to 0.0.0.0/0
- Check if EC2 instance is running
- Verify containers are running: `docker-compose ps`

#### 4. Environment Variable Issues
**Problem**: Variables not being passed correctly.

**Solution**: Rebuild containers with no cache:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Useful Commands

```bash
# Container Management
docker-compose up -d              # Start in background
docker-compose down               # Stop containers
docker-compose restart            # Restart services
docker-compose logs -f            # Follow logs
docker-compose ps                 # Check status

# Cleanup Commands
docker-compose down --volumes --remove-orphans
docker system prune -a --volumes
docker image prune -a

# Debugging
docker exec -it chat-frontend sh  # Access frontend container
docker exec -it chat-backend sh   # Access backend container
```

## 📁 Project Structure

```
docker-ec2-webapp/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── Dockerfile          # Backend container config
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   └── app/
│   │       └── page.tsx    # Main chat interface
│   ├── Dockerfile          # Frontend container config
│   └── package.json        # Node.js dependencies
├── cloud-init.yaml         # Automated EC2 deployment script
├── docker-compose.yml      # Container orchestration
├── .env                    # Environment variables
└── README.md              # This file
```


## 🔐 AWS IAM Role Setup for S3 Chat History

### Step 1: Create IAM Role

1. **AWS Console → IAM → Roles → Create Role**
2. **Trusted entity**: AWS Service → EC2
3. **Permissions**: Attach `AmazonS3FullAccess`
4. **Role name**: `EC2-S3-Access-Role`

### Step 2: Attach Role to EC2

1. **EC2 Console → Select Instance → Actions → Security → Modify IAM role**
2. **Select**: `EC2-S3-Access-Role`
3. **Update IAM role**

### Step 3: Create S3 Bucket

1. **AWS Console → S3 → Create bucket**
2. **Bucket name**: `akash-chat-app-bucket-2025` (or your chosen name)
3. **Region**: Choose same region as your EC2 instance
4. **Keep default settings** for permissions and configuration
5. **Create bucket**

Or via CLI:
```bash
# Create bucket (replace with your unique name)
aws s3 mb s3://akash-chat-app-bucket-2025
```

---

## 🔄 Redeployment

To redeploy with new code:

```bash
# On your EC2 instance
cd docker-ec2-webapp
git pull origin main
docker-compose down
docker-compose up --build -d
```

## 🛠️ Deployment Troubleshooting

### Cloud-Init Deployment Issues

**Problem**: Cloud-init fails or doesn't complete setup
```bash
# Check cloud-init status
sudo cloud-init status

# View detailed logs
sudo journalctl -u cloud-init-local.service
sudo tail -f /var/log/cloud-init-output.log

# If status shows "error", check for errors:
grep -i error /var/log/cloud-init-output.log
```

**Common fixes:**
- Ensure your Gemini API key is correctly formatted in `cloud-init.yaml`
- Check that IAM role is properly attached to EC2 instance
- Verify security group allows ports 3000 and 5000
- Wait at least 10 minutes for full setup completion

### Deploy Script Issues

**Problem**: Script fails during Docker installation
```bash
# Run script with debug mode
bash -x deploy.sh

# Or check if Docker group needs manual setup
sudo usermod -aG docker $USER
newgrp docker
```

**Problem**: Script hangs on "Waiting for Docker to be ready"
```bash
# The script has a 60-second timeout, but you can force continue
# Press Ctrl+C and run:
sudo systemctl restart docker
sleep 5
./deploy.sh  # Run again
```

**Problem**: Can't access application after deployment
```bash
# Check if containers are running
docker-compose ps

# Check container logs
docker-compose logs frontend
docker-compose logs backend

# Verify your EC2 security group allows inbound traffic on ports 3000 and 5000
```

### S3 Integration Issues

**Problem**: S3 status shows "Access Denied"
- Verify IAM role `EC2-S3-Access-Role` is attached to EC2 instance
- Check S3 bucket name matches exactly in environment variables
- Ensure IAM policy includes correct bucket ARN

**Problem**: S3 status shows "Not Found"
- Verify S3 bucket exists and is in correct region
- Check bucket name spelling in environment variables
- Create bucket if it doesn't exist

### General Application Issues

**Problem**: Frontend can't connect to backend
```bash
# Test backend directly
curl http://your-ec2-ip:5000/health

# Check environment variables
docker exec chat-frontend env | grep NEXT_PUBLIC_API_URL

# Should show: NEXT_PUBLIC_API_URL=http://YOUR_EC2_IP:5000
```

**Problem**: Application runs locally but not on EC2
- Check EC2 security group rules (ports 22, 3000, 5000 must be open)
- Verify public IP address is used in frontend configuration
- Ensure Docker containers have proper networking

**Problem**: Chat messages not saving to S3
```bash
# Check S3 status endpoint
curl http://your-ec2-ip:5000/s3/status

# Test all S3 endpoints
curl http://your-ec2-ip:5000/s3/chat-history
curl http://your-ec2-ip:5000/s3/chat-history/count

# Check if IAM role allows S3 access
aws sts get-caller-identity  # Should show role info

# Check backend logs for S3 errors
docker-compose logs backend | grep -i s3
```

### Performance Issues

**Problem**: Slow response times
- Consider upgrading from t2.micro to t2.small or larger
- Monitor CPU and memory usage: `htop`
- Check container resources: `docker stats`

### Getting Help

If you encounter issues:
1. Check the troubleshooting steps above
2. Review container logs: `docker-compose logs`
3. Verify all environment variables are set correctly
4. Ensure IAM roles and security groups are properly configured
5. Check AWS CloudWatch logs for EC2 instance issues

---

## 📊 S3 Chat History Features

- **Automatic Saving**: Every chat conversation is automatically saved to S3
- **Organized Storage**: Chats are organized by date (`chat-history/YYYY-MM-DD/timestamp.json`)
- **History Retrieval**: API endpoint to retrieve recent chat history
- **Chat Statistics**: Get total count of stored conversations
- **Error Handling**: App continues to work even if S3 is unavailable

### Testing S3 Integration

After deployment, test S3 functionality with these commands:

#### S3 Status Check
```bash
# Check S3 connection status
curl http://YOUR_EC2_IP:5000/s3/status

# Expected responses:
# Success: {"status": "connected", "bucket": "akash-chat-app-bucket-2025"}
# No IAM Role: {"status": "no_credentials", "message": "No AWS credentials found"}
# Wrong Bucket: {"status": "access_denied", "message": "Access denied to bucket"}
```

#### Chat History Retrieval
```bash
# Get recent chat conversations (last 10)
curl http://YOUR_EC2_IP:5000/s3/chat-history

# Expected response (if conversations exist):
# [
#   {
#     "timestamp": "2025-01-20T10:30:00Z",
#     "user_message": "Hello",
#     "ai_response": "Hi there! How can I help you today?",
#     "conversation_id": "conv_123"
#   }
# ]
```

#### Chat History Count
```bash
# Get total number of stored conversations
curl http://YOUR_EC2_IP:5000/s3/chat-history/count

# Expected response:
# {"total_conversations": 25, "bucket": "akash-chat-app-bucket-2025"}
```

#### Web Browser Testing
You can also test these endpoints directly in your browser:
- **S3 Status**: `http://YOUR_EC2_IP:5000/s3/status`
- **Chat History**: `http://YOUR_EC2_IP:5000/s3/chat-history`
- **Chat Count**: `http://YOUR_EC2_IP:5000/s3/chat-history/count`

### 🔑 How IAM Roles Work with Docker

The IAM role attached to your EC2 instance automatically provides credentials to:
- ✅ **EC2 instance** itself
- ✅ **Docker containers** running on the instance
- ✅ **Applications** inside the containers

**No need to:**
- Store AWS access keys in environment variables
- Configure AWS credentials manually
- Worry about credential rotation

The `boto3` library automatically discovers and uses the IAM role credentials through the AWS metadata service.

## 🔧 Configuration Reference

### Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Google Gemini AI API key | `AIzaSy...` | ✅ Yes |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend | `http://65.0.139.226:5000` | ✅ Yes |
| `S3_BUCKET_NAME` | S3 bucket for chat history storage | `akash-chat-app-bucket-2025` | ⚠️ Optional |

### Docker Services

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| `frontend` | 3000 | Next.js chat interface | `http://ip:3000` |
| `backend` | 5000 | FastAPI server with Gemini AI | `http://ip:5000/health` |

### API Endpoints

| Endpoint | Method | Description | Response Example |
|----------|--------|-------------|------------------|
| `/health` | GET | Backend health check | `{"status": "healthy"}` |
| `/chat` | POST | Send message to AI | `{"response": "AI response text"}` |
| `/s3/status` | GET | S3 connection status | `{"status": "connected", "bucket": "bucket-name"}` |
| `/s3/chat-history` | GET | Retrieve recent chat history (last 10) | `[{"timestamp": "...", "user_message": "...", "ai_response": "..."}]` |
| `/s3/chat-history/count` | GET | Get total conversation count | `{"total_conversations": 25, "bucket": "bucket-name"}` |

#### S3 Endpoint Details

**`/s3/status`** - Check S3 connectivity and permissions
- ✅ Connected: `{"status": "connected", "bucket": "your-bucket-name"}`
- ❌ No credentials: `{"status": "no_credentials", "message": "No AWS credentials found"}`
- ❌ Access denied: `{"status": "access_denied", "message": "Access denied to bucket"}`

**`/s3/chat-history`** - Retrieve recent conversations
- Returns last 10 chat conversations in reverse chronological order
- Each conversation includes timestamp, user message, AI response, and conversation ID
- Returns empty array `[]` if no conversations exist

**`/s3/chat-history/count`** - Get conversation statistics  
- Returns total number of stored conversations across all dates
- Includes bucket name for verification

## 🔐 Security Best Practices

- **API Keys**: Keep your Gemini API key secure and never commit it to version control
- **Firewall**: Consider restricting port access to specific IPs in production
- **HTTPS**: For production, set up SSL/TLS certificates and reverse proxy
- **Updates**: Regularly update dependencies and base images
- **IAM**: Use minimal permissions in IAM policies (only required S3 actions)

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch  
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For questions or issues:
1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs -f`
3. Verify your environment configuration
4. Ensure all prerequisites are met
5. Create an issue on GitHub with detailed error information