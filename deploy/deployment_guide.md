# 🚀 Better French Max - Deployment Guide

## **How to Run the Scheduler 24/7**

You have **multiple deployment options** depending on your infrastructure. Here are the best approaches:

---

## 🏆 **RECOMMENDED: Option 1 - System Service (Best for VPS/Dedicated Server)**

### **Create a Systemd Service (Linux/macOS)**

**1. Create service file:**
```bash
sudo nano /etc/systemd/system/better-french-max.service
```

**2. Add this configuration:**
```ini
[Unit]
Description=Better French Max Automated System
After=network.target
Wants=network.target

[Service]
Type=simple
User=your_username
Group=your_group
WorkingDirectory=/Users/anandsoni/Desktop/Project Better French
ExecStart=/usr/bin/python3 scripts/scheduler_main.py
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
Environment=PYTHONPATH=/Users/anandsoni/Desktop/Project Better French
Environment=OPENROUTER_API_KEY=your_api_key_here

[Install]
WantedBy=multi-user.target
```

**3. Enable and start the service:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable better-french-max.service

# Start the service
sudo systemctl start better-french-max.service

# Check status
sudo systemctl status better-french-max.service

# View logs
sudo journalctl -u better-french-max.service -f
```

**✅ Benefits:**
- ✅ Automatic startup on system boot
- ✅ Automatic restart if crashed
- ✅ System-level logging and monitoring
- ✅ Easy start/stop/restart commands
- ✅ Resource limits and security

---

## 🐳 **Option 2 - Docker Deployment (Best for Scalability)**

**1. Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data/live data/processed data/archive

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for web interface (if needed)
EXPOSE 8001

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=1m --retries=3 \
  CMD python3 -c "import json; print(json.load(open('logs/health_status.json'))['status'])" || exit 1

# Run the scheduler
CMD ["python3", "scripts/scheduler_main.py"]
```

**2. Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  better-french-max:
    build: .
    container_name: better-french-max-scheduler
    restart: unless-stopped
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - TZ=Europe/Paris
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    ports:
      - "8001:8001"
    networks:
      - french-max-network
    healthcheck:
      test: ["CMD", "python3", "-c", "import requests; requests.get('http://localhost:8001/health')"]
      interval: 5m
      timeout: 30s
      retries: 3

  # Optional: Add a web dashboard
  dashboard:
    image: nginx:alpine
    container_name: better-french-max-dashboard
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./website:/usr/share/nginx/html
    depends_on:
      - better-french-max
    networks:
      - french-max-network

networks:
  french-max-network:
    driver: bridge
```

**3. Deploy with Docker:**
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f better-french-max

# Stop
docker-compose down

# Update
docker-compose pull && docker-compose up -d
```

**✅ Benefits:**
- ✅ Isolated environment
- ✅ Easy deployment and scaling
- ✅ Built-in health monitoring
- ✅ Platform-independent
- ✅ Easy backup and migration

---

## ⏰ **Option 3 - Cron + Process Manager (Simple & Reliable)**

**1. Create a process manager script:**
```bash
#!/bin/bash
# File: scripts/run_scheduler.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PIDFILE="$PROJECT_DIR/scheduler.pid"
LOGFILE="$PROJECT_DIR/logs/scheduler_runner.log"

cd "$PROJECT_DIR"

# Check if already running
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "$(date): Scheduler already running with PID $PID" >> "$LOGFILE"
        exit 0
    else
        echo "$(date): Removing stale PID file" >> "$LOGFILE"
        rm "$PIDFILE"
    fi
fi

# Start the scheduler
echo "$(date): Starting Better French Max scheduler" >> "$LOGFILE"
python3 scripts/scheduler_main.py &
PID=$!
echo $PID > "$PIDFILE"

echo "$(date): Scheduler started with PID $PID" >> "$LOGFILE"
```

**2. Make it executable:**
```bash
chmod +x scripts/run_scheduler.sh
```

**3. Add to crontab:**
```bash
# Edit crontab
crontab -e

# Add this line to check every 5 minutes
*/5 * * * * /Users/anandsoni/Desktop/Project\ Better\ French/scripts/run_scheduler.sh

# Add daily restart at 3 AM (optional)
0 3 * * * pkill -f scheduler_main.py && sleep 10 && /Users/anandsoni/Desktop/Project\ Better\ French/scripts/run_scheduler.sh
```

**✅ Benefits:**
- ✅ Simple setup
- ✅ Automatic restart if crashed
- ✅ Works on any Unix system
- ✅ Easy monitoring and control

---

## ☁️ **Option 4 - Cloud Deployment**

### **4a. AWS EC2 + CloudWatch**
```bash
# Install on EC2 instance
sudo yum update -y
sudo yum install -y python3 python3-pip git

# Clone your project
git clone [your-repo]
cd project-better-french

# Install dependencies
pip3 install -r requirements.txt

# Create CloudWatch log group
aws logs create-log-group --log-group-name better-french-max

# Run with CloudWatch logging
python3 scripts/scheduler_main.py 2>&1 | aws logs put-log-events --log-group-name better-french-max --log-stream-name scheduler
```

### **4b. Google Cloud Run (Serverless)**
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/better-french-max', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/better-french-max']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'better-french-max'
      - '--image=gcr.io/$PROJECT_ID/better-french-max'
      - '--platform=managed'
      - '--region=europe-west1'
      - '--allow-unauthenticated'
```

---

## 📊 **Monitoring & Management**

### **Health Check Script**
```bash
#!/bin/bash
# File: scripts/health_check.sh

PROJECT_DIR="/Users/anandsoni/Desktop/Project Better French"
HEALTH_URL="http://localhost:8001/health"

# Check if scheduler is running
if ! pgrep -f "scheduler_main.py" > /dev/null; then
    echo "❌ Scheduler not running"
    # Send alert email/Slack notification here
    exit 1
fi

# Check if website is responding
if ! curl -s "$HEALTH_URL" > /dev/null; then
    echo "⚠️ Website not responding"
    exit 1
fi

# Check log for recent errors
if tail -100 "$PROJECT_DIR/logs/automation.log" | grep -q "ERROR"; then
    echo "⚠️ Recent errors detected in logs"
    exit 1
fi

echo "✅ System healthy"
```

### **Management Commands**
```bash
# Status check
python3 scripts/scheduler_main.py --status

# Stop gracefully
pkill -SIGTERM -f scheduler_main.py

# Force stop
pkill -SIGKILL -f scheduler_main.py

# View real-time logs
tail -f logs/automation.log

# Check system performance
python3 scripts/monitoring.py --report
```

---

## 🎯 **RECOMMENDED SETUP FOR YOU**

Based on your macOS environment, I recommend **Option 1 (System Service)** with the following setup:

### **Quick Setup Script**
```bash
#!/bin/bash
# File: deploy/quick_setup.sh

echo "🚀 Setting up Better French Max Automated System..."

PROJECT_DIR="/Users/anandsoni/Desktop/Project Better French"
cd "$PROJECT_DIR"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data/live data/processed data/archive

# Set up environment
echo "⚙️ Setting up environment..."
export PYTHONPATH="$PROJECT_DIR"
export OPENROUTER_API_KEY="your_api_key_here"

# Create launchd plist for macOS (instead of systemd)
echo "🍎 Creating macOS service..."
cat > ~/Library/LaunchAgents/com.betterfrenchmax.scheduler.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.betterfrenchmax.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$PROJECT_DIR/scripts/scheduler_main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/scheduler_out.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/scheduler_err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>$PROJECT_DIR</string>
        <key>OPENROUTER_API_KEY</key>
        <string>your_api_key_here</string>
    </dict>
</dict>
</plist>
EOF

# Load the service
launchctl load ~/Library/LaunchAgents/com.betterfrenchmax.scheduler.plist

echo "✅ Setup complete!"
echo "📊 Service status: launchctl list | grep betterfrenchmax"
echo "📋 View logs: tail -f logs/automation.log"
echo "🛑 Stop service: launchctl unload ~/Library/LaunchAgents/com.betterfrenchmax.scheduler.plist"
```

---

## 🚨 **Emergency Procedures**

### **If Scheduler Stops:**
```bash
# Check what happened
tail -50 logs/automation.log

# Restart service (macOS)
launchctl unload ~/Library/LaunchAgents/com.betterfrenchmax.scheduler.plist
launchctl load ~/Library/LaunchAgents/com.betterfrenchmax.scheduler.plist

# Manual start (testing)
cd "/Users/anandsoni/Desktop/Project Better French"
python3 scripts/scheduler_main.py
```

### **Fallback to Manual System:**
```bash
# The scheduler automatically falls back to manual system if needed
# You can also force it:
python3 scripts/scheduler_main.py --manual-fallback
```

---

## 📈 **Scaling & Performance**

### **For High Traffic:**
- Use **Docker with multiple containers**
- Add **load balancer** for website
- Use **Redis** for caching
- Deploy on **cloud with auto-scaling**

### **For Cost Optimization:**
- Use **scheduled cloud functions** (AWS Lambda, Google Cloud Functions)
- **Turn off during low-usage hours**
- Use **spot instances** for processing

---

## ✅ **Quick Start Command**

**To get started immediately:**

```bash
# Navigate to your project
cd "/Users/anandsoni/Desktop/Project Better French"

# Install dependencies
pip3 install -r requirements.txt

# Start the scheduler (will run 24/7)
python3 scripts/scheduler_main.py
```

**The scheduler will:**
- ✅ Run **24/7** automatically
- ✅ Check for **breaking news every 30 minutes**
- ✅ Do **regular updates every 2 hours**
- ✅ Process **AI enhancement daily at 2 AM**
- ✅ Update **website every 5 minutes**
- ✅ **Restart automatically** if it crashes
- ✅ **Monitor system health** continuously

**You can leave it running and it will handle everything automatically!** 🚀 