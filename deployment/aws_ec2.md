# AWS EC2 Deployment

## Prerequisites
- AWS Account
- EC2 instance (t3.medium or larger recommended)
- Security group allowing port 8501

## Deployment Steps

1. **Launch EC2 Instance**
   ```bash
   # Connect to your EC2 instance
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip git -y
   
   # Clone your repository
   git clone https://github.com/yourusername/kerala-flood-prediction.git
   cd kerala-flood-prediction
   
   # Install Python packages
   pip3 install -r requirements.txt
   ```

3. **Run with PM2 (Recommended)**
   ```bash
   # Install PM2
   sudo npm install -g pm2
   
   # Create ecosystem file
   cat > ecosystem.config.js << EOF
   module.exports = {
     apps: [{
       name: 'flood-prediction',
       script: 'streamlit',
       args: 'run app.py --server.port 8501 --server.address 0.0.0.0',
       interpreter: 'python3',
       cwd: '/home/ubuntu/kerala-flood-prediction',
       env: {
         STREAMLIT_SERVER_PORT: 8501,
         STREAMLIT_SERVER_ADDRESS: '0.0.0.0'
       }
     }]
   }
   EOF
   
   # Start the app
   pm2 start ecosystem.config.js
   pm2 save
   pm2 startup
   ```

4. **Configure Nginx (Optional)**
   ```bash
   sudo apt install nginx -y
   
   cat > /etc/nginx/sites-available/flood-prediction << EOF
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_set_header Host \$host;
           proxy_set_header X-Real-IP \$remote_addr;
           proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto \$scheme;
       }
   }
   EOF
   
   sudo ln -s /etc/nginx/sites-available/flood-prediction /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

## Security Group Settings
- Type: Custom TCP
- Port: 8501
- Source: 0.0.0.0/0 (or your specific IPs)

## Cost Estimation
- t3.medium: ~$30-40/month
- t3.large: ~$60-80/month (recommended for production)