# Agent Selling Checklist - Quick Reference

## ✅ DONE
- [x] 7 agents extracted as standalone packages
- [x] Each has: Dockerfile, docker-compose.yml, requirements.txt
- [x] Each has: API endpoints, README, .env.example
- [x] Deployment scripts ready (Railway/Render)
- [x] Client demo script ready
- [x] Selling guide created

---

## 📋 TODO - Step by Step

### Step 1: GitHub Repos (15 minutes)

```
For each agent:
1. Go to github.com/new
2. Name: cs-agent, inventory-agent, etc.
3. Public
4. Create repository
5. Push code:
   cd cs-agent
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/Ismail-2001/cs-agent.git
   git push -u origin main
```

### Step 2: Deploy to Railway (10 minutes each)

```
1. Go to railway.app
2. Login with GitHub
3. New Project > Deploy from GitHub repo
4. Select cs-agent repo
5. Add environment variable: GOOGLE_API_KEY=your_key
6. Deploy
7. Copy the URL (e.g., cs-agent.up.railway.app)
```

### Step 3: Test (2 minutes)

```bash
# Health check
curl https://cs-agent.up.railway.app/health

# Analyze ticket
curl -X POST https://cs-agent.up.railway.app/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "T-1234",
    "customer_email": "test@example.com",
    "subject": "Where is my order?",
    "body": "I ordered 5 days ago and haven'\''t received it."
  }'
```

### Step 4: Demo Video (20 minutes)

```
1. Open Loom (loom.com)
2. Record screen + camera
3. Show:
   - API docs (/docs)
   - Health endpoint
   - Analyze ticket
   - Response quality
4. Save and get link
```

### Step 5: Outreach (Daily)

```
Daily Routine:
- 10-20 cold emails
- 5-10 LinkedIn connections
- Follow up on replies

Email Template:
Subject: Shopify brands like [Brand] are replacing support reps with AI

Hi [Name],

I noticed [Brand] is scaling fast.

I help Shopify brands replace 60-80% of support volume with AI.
One client saved $38,000/year.

Worth a quick demo?

[Your Name]
```

---

## 🔗 Quick Links

| Item | Link |
|------|------|
| GitHub Repos | https://github.com/Ismail-2001?tab=repositories |
| Railway | https://railway.app |
| Render | https://render.com |
| Wise | https://wise.com |
| Apollo.io | https://apollo.io |
| Loom | https://loom.com |

---

## 💰 Revenue Targets

| Month | Clients | MRR | Action |
|-------|---------|-----|--------|
| 1 | 0 | $0 | Build + Outreach |
| 2 | 0 | $0 | Calls + Proposals |
| 3 | 1 | $1,500 | First Client |
| 4-5 | 3 | $4,500 | Case Study |
| 6 | 4 | $6,000 | Inbound Leads |
| 12 | 10 | $24,000 | Referrals |

---

## 📞 Support

- Guide: AGENT_SELLING_GUIDE.md
- Scripts: scripts/ folder
- Quick Start: python quick-start.py
