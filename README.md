# **NeXeonDash Full Setup**

This guide includes all steps from directory structure setup to Nginx configuration, and systemd service for full deployment of **NeXeonDash**. 

### **1. Directory Structure**

**Step 1.2:** Clone the NeXeonDash repository in `/var/www`:

```bash
cd /var/www
sudo git clone https://gitlab.com/NeXeonDash/NeXeonDash.git
cd NeXeonDash
```

### **2. Environment Setup**

**Step 2.1:** Install dependencies:

```bash
pip install -r requirements.txt
```

**Step 2.3:** Edit `.env` or set environment variables:

Create or edit the `.env` file and set the following environment variables:

```
PTERO_API_KEY="Your Pterodactyl API key"
PTERO_DOMAIN="https://panel.yourdomain.com"
```

(If needed, modify the application code to run on port 5000, but it's better to use systemd for this.)

### **3. Systemd Service**

**Step 3.1:** Create a systemd service file at `/etc/systemd/system/NeXeonDash.service`:

```bash
sudo nano /etc/systemd/system/NeXeonDash.service
```

Add the following content to the service file:

```ini
[Unit]
Description=NeXeonDash
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/NeXeonDash
ExecStart=/usr/bin/python3 /var/www/NeXeonDash/run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Step 3.2:** Enable and start the systemd service:

```bash
sudo systemctl enable NeXeonDash
sudo systemctl start NeXeonDash
```

This will start NeXeonDash on port 5000. If you want to run it on port 80, modify `run.py` or set up Nginx as a reverse proxy.

### **4. Nginx Configuration**

Now, we’ll configure Nginx to act as a reverse proxy for NeXeonDash.

#### **Step 4.1: HTTP Only (No SSL)**

**Step 4.1.1:** Create a new Nginx configuration file in `/etc/nginx/sites-available/`:

```bash
sudo nano /etc/nginx/sites-available/NeXeonDash
```

**Step 4.1.2:** Add the following HTTP-only configuration:

```nginx
server {
    listen 80;
    server_name dash.yourdomain.com;  # Replace with your actual domain

    location / {
        proxy_pass http://127.0.0.1:5000;  # Proxy to the NeXeonDash service running on port 5000
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

#### **Step 4.2: HTTPS (with SSL using Certbot)**

If you want to use HTTPS, follow these steps:

**Step 4.2.1:** Create another Nginx configuration file (or modify the one from above):

```bash
sudo nano /etc/nginx/sites-available/NeXeonDash
```

**Step 4.2.2:** Add the following HTTPS configuration with SSL using Certbot:

```nginx
server {
    listen 80;
    server_name dash.yourdomain.com;  # Replace with your actual domain
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name dash.yourdomain.com;
    ssl_certificate /etc/letsencrypt/live/dash.yourdomain.com/fullchain.pem;  # Replace with your certificate path
    ssl_certificate_key /etc/letsencrypt/live/dash.yourdomain.com/privkey.pem;  # Replace with your certificate path

    location / {
        proxy_pass http://127.0.0.1:5000;  # Proxy to NeXeonDash
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

#### **Step 4.3: Enable the Site**

**Step 4.3.1:** Create a symbolic link from `sites-available` to `sites-enabled` to enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/NeXeonDash /etc/nginx/sites-enabled/
```

**Step 4.3.2:** Test the Nginx configuration:

```bash
sudo nginx -t
```

**Step 4.3.3:** Restart Nginx:

```bash
sudo systemctl restart nginx
```

### **5. Certbot for SSL**

If you are using HTTPS, you can automatically generate an SSL certificate with Certbot.

**Step 5.1:** Install Certbot:

```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

**Step 5.2:** Run Certbot to automatically configure SSL:

```bash
sudo certbot --nginx -d dash.yourdomain.com
```

Follow the prompts to configure SSL for your domain.

### **6. Usage**

1. **Check the systemd service status:**

   ```bash
   sudo systemctl status NeXeonDash
   ```

   This will show the status of the NeXeonDash service.

2. **Access the Dashboard:**

   Visit your NeXeonDash by going to `http://dash.yourdomain.com` (for HTTP) or `https://dash.yourdomain.com` (for HTTPS) in your browser.

### **7. Update Notes**
**January 18, 2025**:
- New modern CSS.
- Server creation.
- Bug fixes.
- Security patches.
- Coded in Python using Flask.

**January 29, 2025**:
- Fixed security issues
- Fixed resource limits not updating in "create_server.html".
- Added custom disk on server_limits.json.
- Fixed databases not showing in "create_server.html".

**January 30, 2025**:
- Added servers.html, so users can see how many servers they have or users can delete them.

### **8. Warning**

- **Change the password in `admin_accounts.json`** to secure your Admin Dashboard.
- **Change `SECRET_KEY`** in `.env` for security to prevent unauthorized server creation.

---

### **Final Notes**

- The **Nginx** configuration is now set up to reverse proxy traffic from port 80 (or 443 with SSL) to the NeXeonDash running on port 5000.
- Your systemd service will automatically restart the application if it crashes.
- Make sure to follow security best practices, including changing default passwords and securing your server with SSL.
