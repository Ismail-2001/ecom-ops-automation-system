# Oracle Cloud Always Free Deployment Guide

## Overview
Deploy all 7 AI Agents on Oracle Cloud Always Free tier (4 OCPU ARM, 24GB RAM, Always Free).

---

## Step 1: Create Oracle Cloud Account

1. Go to: https://cloud.oracle.com/free
2. Click "Start for Free"
3. Fill in:
   - Country: Pakistan
   - Name: Ismail Sajid
   - Email: ismailsajid0617@gmail.com
4. Verify email
5. Add phone number
6. Add address (use any Pakistani address)
7. Add payment method (Visa/Mastercard — won't be charged)
8. Complete signup

---

## Step 2: Create VM Instance

1. Login to Oracle Cloud Console
2. Click hamburger menu → Compute → Instances
3. Click "Create Instance"
4. Settings:
   - Name: `ai-agents`
   - Image: Ubuntu 22.04 (or Oracle Linux)
   - Shape: VM.Standard.A1.Flex (ARM)
   - OCPUs: 4
   - RAM: 24 GB
   - VCN: Create new VCN
   - Public IP: Assign public IP
5. Add SSH Keys:
   - Click "Save Private Key" to download
6. Click "Create"

---

## Step 3: Connect to VM

```bash
# Windows (use Git Bash or PowerShell)
ssh -i ~/Downloads/your-key.pem ubuntu@PUBLIC_IP

# Mac/Linux
chmod 400 ~/Downloads/your-key.pem
ssh -i ~/Downloads/your-key.pem ubuntu@PUBLIC_IP
```

---

## Step 4: Run Deployment Script

Once connected to VM:

```bash
# Clone the deployment files
git clone https://github.com/Ismail-2001/ai-agents-deployment.git
cd ai-agents-deployment

# Run setup
chmod +x setup.sh
./setup.sh
```

---

## Step 5: Access Your Agents

After deployment, access agents at:
- Customer Support: http://PUBLIC_IP:8001
- Inventory: http://PUBLIC_IP:8002
- Pricing: http://PUBLIC_IP:8003
- Reviews: http://PUBLIC_IP:8004
- Marketing: http://PUBLIC_IP:8005
- Cart Recovery: http://PUBLIC_IP:8006
- Fraud Detection: http://PUBLIC_IP:8007

---

## Firewall Setup (Oracle Cloud Console)

1. Go to: Networking → Virtual Cloud Networks → your VCN
2. Click on your subnet
3. Click on your security list
4. Add Ingress Rules:
   - Source CIDR: 0.0.0.0/0
   - Destination Port: 8001-8007
5. Click "Add Ingress Rules"

---

## Cost

| Item | Cost |
|------|------|
| VM (Always Free) | $0/month |
| Storage (20GB) | $0/month |
| Network | $0/month |
| **Total** | **$0/month forever** |

---

## Resources Used

| Agent | Port | RAM |
|-------|------|-----|
| Customer Support | 8001 | 512MB |
| Inventory | 8002 | 512MB |
| Pricing | 8003 | 512MB |
| Reviews | 8004 | 512MB |
| Marketing | 8005 | 512MB |
| Cart Recovery | 8006 | 512MB |
| Fraud Detection | 8007 | 512MB |
| **Total** | - | **3.5GB** |

Free tier has 24GB RAM — plenty of room!

---

## Troubleshooting

### VM won't start
- Check ARM shape availability in your region
- Try a different availability domain

### Can't SSH
- Check security group allows SSH (port 22)
- Verify SSH key is correct

### Agents not accessible
- Check firewall rules (ports 8001-8007)
- Verify Docker is running: `docker ps`
- Check logs: `docker compose logs`
