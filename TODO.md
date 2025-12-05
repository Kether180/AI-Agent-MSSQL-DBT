# DataMigrate AI - TODO List

## Priority: High

### Email Setup for support@datamigrate.ai
- [ ] Set up email forwarding from `support@datamigrate.ai` to Gmail
- **Options:**
  1. **Cloudflare Email Routing** (Free) - If domain is on Cloudflare
  2. **ImprovMX** (Free tier available) - Simple email forwarding
  3. **Zoho Mail** (Free tier) - Full email hosting
  4. **Google Workspace** ($6/user/month) - Professional email with Gmail interface
- **Current Contact Info in App:**
  - Phone: +45 6127 5393
  - Email: support@datamigrate.ai

---

## Priority: Medium

### Production Deployment
- [ ] Set up production environment variables
- [ ] Configure HTTPS/SSL certificates
- [ ] Set up domain DNS for datamigrate.ai
- [ ] Deploy Go backend to production server
- [ ] Deploy Python AI service
- [ ] Deploy Vue frontend (consider Vercel, Netlify, or custom server)
- [ ] Set up PostgreSQL production database

### Security
- [ ] Change JWT_SECRET to a secure production value
- [ ] Review and rotate API keys
- [ ] Set up rate limiting for production
- [ ] Configure CORS for production domains only

---

## Priority: Low

### Features
- [ ] Add callback request form (collect user details and save to database)
- [ ] Send email notification when callback is requested
- [ ] Add chat history persistence (save conversations)
- [ ] Add user satisfaction rating after chat

### Documentation
- [ ] Update API documentation
- [ ] Create user guide for the platform
- [ ] Document deployment process

---

## Completed
- [x] Integrate Claude AI for chat support
- [x] Add markdown rendering in chat widget
- [x] Add "Request Callback" and "Email Us" buttons
- [x] Set up SMTP for password reset emails
- [x] Create lightweight Python chat API (agents/chat_api.py)

---

## Notes

### Services Architecture
```
Frontend (Vue.js)     → http://localhost:5173
Go Backend            → http://localhost:8080
Python AI Service     → http://localhost:8081
PostgreSQL            → localhost:5432
```

### Start All Services
```powershell
.\scripts\start-services.ps1
```

### Environment Files
- `backend/.env` - Go backend config (DB, JWT, SMTP, Anthropic API)
- `.env` - Root env for Python agents
