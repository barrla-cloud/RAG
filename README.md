# RAG
# RAG Project Deployment Guide
 
This guide provides step-by-step instructions to deploy the **Next.js frontend** and **FastAPI backend** on an **Ubuntu EC2 instance** with **PM2 (for Next.js) and Systemd (for FastAPI)**.
 
---
 
## 📌 Project Structure
 
```
/RAG                   # Root directory
│── /frontend          # Next.js frontend
│   ├── package.json   # Next.js dependencies
│   ├── next.config.js # Next.js configuration
│   ├── /public        # Static assets
│   ├── /pages         # Frontend pages (React)
│   ├── /components    # Reusable components
│   ├── /styles        # CSS styles
│   ├── /node_modules  # Installed dependencies (after npm install)
│   ├── .next          # Build files (after npm run build)
│── /backend           # FastAPI backend
│   ├── app.py         # FastAPI main entry point
│   ├── requirements.txt  # Python dependencies
│   ├── /static        # Static files (if needed)
│   ├── /templates     # HTML templates (if needed)
```
 
---
 
## 🚀 Deployment Environment
 
- **EC2 Instance Type:** t2.micro (Ubuntu 22.04 LTS)
- **Frontend:** Next.js (Node.js 20)
- **Backend:** FastAPI (Python 3.10)
- **Process Manager:** PM2 (Next.js), Systemd (FastAPI)
- **Reverse Proxy:** Nginx (Optional, recommended for production)
 
---
 
## ✅ Prerequisites
 
Before proceeding, ensure you have:
- A **running EC2 Ubuntu 22.04 instance** (`t2.micro` recommended for testing)
- **SSH access** to the instance
- **Domain name (optional)** if using Nginx
- Installed dependencies:
  ```sh
  sudo apt update && sudo apt upgrade -y
  sudo apt install -y python3-pip python3-venv nginx
  ```
 
---
 
## ⚙️ Step 1: Install Node.js (Version 20)
 
```sh
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node -v  # Verify Node.js version
npm -v   # Verify NPM version
```
 
---
 
## ⚙️ Step 2: Set Up Next.js Frontend
 
### 2.1 Navigate to the frontend directory and install dependencies:
```sh
cd /RAG/frontend
npm install
```
 
### 2.2 Build the Next.js application:
```sh
npm run build
```
 
### 2.3 Start the Next.js app in the background using PM2:
```sh
npm install -g pm2
pm run start  # Test if Next.js runs successfully
pm2 start "npm run start" --name "nextjs"
pm2 save
pm2 startup
```
 
---
 
## ⚙️ Step 3: Set Up FastAPI Backend
 
### 3.1 Navigate to the backend directory:
```sh
cd /RAG/backend
```
 
### 3.2 Create a Python virtual environment and activate it:
```sh
python3 -m venv venv
source venv/bin/activate
```
 
### 3.3 Install FastAPI dependencies:
```sh
pip install --upgrade pip
pip install -r requirements.txt
```
 
### 3.4 Test if FastAPI runs successfully:
```sh
uvicorn app:app --host 0.0.0.0 --port 8000
```
 
If it works, stop the process (`CTRL + C`).
 
### 3.5 Create a Systemd Service for FastAPI
 
Create a new systemd service file:
```sh
sudo nano /etc/systemd/system/fastapi.service
```
 
Paste the following:
```ini
[Unit]
Description=FastAPI service
After=network.target
 
[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/RAG/backend
ExecStart=/home/ubuntu/RAG/backend/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
 
[Install]
WantedBy=multi-user.target
```
 
### 3.6 Start and Enable FastAPI Service
```sh
sudo systemctl daemon-reload
sudo systemctl start fastapi
sudo systemctl enable fastapi
```
 
Check status:
```sh
sudo systemctl status fastapi
```
 
---
 
## ⚙️ Step 4: Configure Nginx (Optional, for Reverse Proxy)
 
### 4.1 Install Nginx:
```sh
sudo apt install nginx -y
```
 
### 4.2 Create an Nginx Configuration File
```sh
sudo nano /etc/nginx/sites-available/rag
```
 
Paste the following:
```nginx
server {
    listen 80;
    server_name your_domain_or_ip;
 
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
 
    location /api/ {
        rewrite ^/api(/.*)$ $1 break;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
 
### 4.3 Enable Nginx Configuration
```sh
sudo ln -s /etc/nginx/sites-available/rag /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```
 
---
 
## 🔥 Final Steps
 
1. **Reboot the server**:
   ```sh
   sudo reboot
   ```
2. **Check if the services are running**:
   ```sh
   pm2 list  # Should show Next.js running
   sudo systemctl status fastapi  # Should show FastAPI running
   ```
3. **Access your app**:
   - **Frontend:** `http://your_domain_or_ip`
   - **Backend API:** `http://your_domain_or_ip/api/docs`
 
---
 
## 🚀 Automate Deployment with Git
 
If deploying via Git:
```sh
cd /RAG
sudo apt install git -y
git clone <repo_url> .
```
 
To pull latest changes and restart services:
```sh
git pull
pm run build && pm2 restart nextjs
sudo systemctl restart fastapi
```
 
---
 
## 🎯 Troubleshooting
 
- **Frontend Not Loading?**
  ```sh
  pm2 logs nextjs
  ```
- **Backend Not Working?**
  ```sh
  sudo journalctl -u fastapi --no-pager | tail -n 50
  ```
- **Check Running Processes**
  ```sh
  ps aux | grep node
  ps aux | grep uvicorn
  ```
- **Restart Services**
  ```sh
  pm2 restart nextjs
  sudo systemctl restart fastapi
  sudo systemctl restart nginx
  ```
 
---
 
## 🎉 Congratulations!
Your **Next.js + FastAPI** application is now running on **Ubuntu EC2** with **PM2 and Systemd** for process management. 🚀
