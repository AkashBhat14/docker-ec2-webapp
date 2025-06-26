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

### Step 1: Launch EC2 Instance

1. **Create EC2 Instance**:
   - Instance type: `t2.micro` (free tier)
   - AMI: Ubuntu 22.04 LTS
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
├── docker-compose.yml      # Container orchestration
├── .env                    # Environment variables
└── README.md              # This file
```

## 🔐 AWS IAM Role Setup for S3 Access

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

```bash
# Create bucket (replace with unique name)
aws s3 mb s3://your-chat-app-bucket

# Set bucket policy (optional)
aws s3api put-bucket-policy --bucket your-chat-app-bucket --policy file://bucket-policy.json
```

### Step 4: Update Environment Configuration

Add S3 bucket name to your `.env` file:
```bash
# Your existing variables
GEMINI_API_KEY="your_actual_gemini_api_key"
NEXT_PUBLIC_API_URL="http://YOUR_EC2_PUBLIC_IP:5000"

# Add S3 bucket name
S3_BUCKET_NAME="your-chat-app-bucket"
```

### Step 5: Deploy with S3 Support

```bash
# Rebuild and deploy with S3 support
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check logs for S3 connectivity
docker-compose logs backend
```

### Step 6: Test S3 Access

After deployment, test S3 connectivity:
- Backend S3 status: `http://YOUR_EC2_IP:5000/s3/status`
- Chat logs: `http://YOUR_EC2_IP:5000/s3/chat-logs`

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

## 🔧 Configuration Details

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini AI API key | `AIzaSy...` |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend | `http://65.0.139.226:5000` |
| `S3_BUCKET_NAME` | S3 bucket for storing chat logs | `your-chat-app-bucket` |

### Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | Next.js chat interface |
| `backend` | 5000 | FastAPI server with Gemini AI |

## 🔐 Security Considerations

- **API Keys**: Keep your Gemini API key secure and never commit it to version control
- **Firewall**: Consider restricting port access to specific IPs in production
- **HTTPS**: For production, set up SSL/TLS certificates
- **Updates**: Regularly update dependencies and base images

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs -f`
3. Verify your environment configuration
4. Ensure all prerequisites are met
