# Intellectual Property Protection Checklist

**DataMigrate AI - Project Security Guide**

This document outlines steps to protect your intellectual property when bringing collaborators onto the project.

---

## ✅ IMMEDIATE ACTIONS (Do This NOW)

### 1. **Sign Legal Agreements BEFORE Sharing Code**

- [ ] **NDA (Non-Disclosure Agreement)** - Sign BEFORE any technical discussions
- [ ] **Contractor Agreement** OR **Employment Agreement** - Sign BEFORE they write any code
- [ ] Use DocuSign, HelloSign, or PandaDoc for legally binding electronic signatures

**⚠️ CRITICAL:** If someone writes code without a signed agreement, they may own the copyright!

---

### 2. **Private GitHub Repository**

- [ ] Ensure repository is set to **Private** (not Public)
- [ ] Review who has access: Settings → Collaborators
- [ ] Use **Branch Protection Rules** on main branch (require PR reviews)
- [ ] Enable **Two-Factor Authentication (2FA)** for all collaborators
- [ ] Use **SSH keys** instead of passwords

```bash
# Check if repo is private
git remote -v
# Should show github.com/your-private-org/repo (not public)

# Enable branch protection
# Go to: Settings → Branches → Add rule
# ✓ Require pull request reviews before merging
# ✓ Require status checks to pass
# ✓ Include administrators
```

---

### 3. **Environment Variables and Secrets**

- [ ] **Never commit** `.env` files, API keys, or passwords to git
- [ ] Use `.gitignore` to exclude sensitive files
- [ ] Store secrets in environment variables or secret managers
- [ ] Rotate all API keys if accidentally committed
- [ ] Use GitHub Secrets for CI/CD

```bash
# Check if secrets were committed
git log --all --full-history -- .env
git log --all --full-history -- *credentials*

# If secrets were committed, rotate them immediately!
# Then use BFG Repo Cleaner to remove from history:
# https://rtyley.github.io/bfg-repo-cleaner/
```

**Add to `.gitignore`:**
```
.env
.env.*
*.key
*.pem
credentials.json
secrets.yaml
config/local.yaml
```

---

### 4. **Copyright Notice**

- [ ] Add copyright notice to all source files
- [ ] Add LICENSE file to repository (choose: MIT, Apache 2.0, or Proprietary)
- [ ] Update README.md with copyright and license info

**Add to every source file:**

```python
# Copyright (c) 2025 Alexander Garcia Angus / OKO Investments
# All rights reserved.
# Proprietary and confidential.
```

```go
// Copyright (c) 2025 Alexander Garcia Angus / OKO Investments
// All rights reserved.
// Proprietary and confidential.
```

```javascript
// Copyright (c) 2025 Alexander Garcia Angus / OKO Investments
// All rights reserved.
// Proprietary and confidential.
```

---

### 5. **Access Control**

- [ ] **Principle of Least Privilege** - Give minimum access needed
- [ ] Separate repos for frontend/backend if needed
- [ ] Use **Protected Branches** - Require PR approval for main
- [ ] Monitor **Audit Logs** - Review who accessed what
- [ ] Revoke access immediately when someone leaves

**GitHub Access Levels:**
- **Read:** View code only (use for advisors, investors)
- **Write:** Can push to branches (most collaborators)
- **Admin:** Full control (only you and trusted co-founders)

---

## 🛡️ SECURITY BEST PRACTICES

### 6. **Code Reviews**

- [ ] **Never merge without review** - Require at least 1 approval
- [ ] Review for:
  - Malicious code (backdoors, data exfiltration)
  - Hardcoded credentials
  - Security vulnerabilities
  - IP leakage (comments with your business logic)

### 7. **Document Everything**

- [ ] Keep records of:
  - Who worked on what (git commits show this)
  - When agreements were signed (DocuSign timestamps)
  - What information was shared and when
  - All communications (emails, Slack messages)

### 8. **Watermarking (Advanced)**

- [ ] Consider adding **code fingerprints** to track leaks
- [ ] Use unique identifiers in different versions shared with different people
- [ ] Example: Add unique comments or variable names per collaborator

```python
# Version shared with Contractor A
# Tracker: A-2025-11-27-XY4K

# Version shared with Contractor B
# Tracker: B-2025-11-27-ZP9M
```

If code leaks, you can identify the source.

---

## 📋 LEGAL DOCUMENTS CHECKLIST

### For Contractors/Freelancers:

- [ ] **NDA** (Non-Disclosure Agreement) - Signed FIRST
- [ ] **Contractor Agreement** with:
  - [ ] IP Assignment Clause (they don't own the code)
  - [ ] Work-for-Hire Clause
  - [ ] Non-compete Clause (12-24 months)
  - [ ] Confidentiality obligations
  - [ ] Payment terms
  - [ ] Termination clause

### For Employees:

- [ ] **Employment Agreement** with:
  - [ ] IP Assignment Clause
  - [ ] Proprietary Information and Inventions Agreement (PIIA)
  - [ ] Non-compete / Non-solicitation
  - [ ] Confidentiality

### For Co-founders:

- [ ] **Founders' Agreement** with:
  - [ ] Equity split (recommend equal or based on contribution)
  - [ ] Vesting schedule (4-year with 1-year cliff is standard)
  - [ ] IP Assignment (all prior work belongs to company)
  - [ ] Roles and responsibilities
  - [ ] Decision-making authority
  - [ ] Exit provisions (what happens if someone leaves)

---

## 🚨 RED FLAGS - What to Watch For

### Technical Red Flags:

- [ ] Collaborator asking for more access than needed
- [ ] Copying entire codebase to personal laptop
- [ ] Pushing to personal GitHub repos
- [ ] Taking screenshots of sensitive architecture diagrams
- [ ] Asking about business strategy beyond their role
- [ ] Working on competing projects simultaneously

### Behavioral Red Flags:

- [ ] Refusing to sign NDA or IP assignment
- [ ] Vague about past projects or employment
- [ ] Already working on similar tools
- [ ] Asking unusual questions about monetization or customers
- [ ] Trying to negotiate ownership of code they write

**If you see these, STOP immediately and consult a lawyer.**

---

## 🔐 TECHNICAL SECURITY MEASURES

### 1. **Database Security**

```python
# Use connection pooling with limited permissions
# Create separate DB users for different services

# Example: Read-only user for analytics
CREATE USER 'analytics_readonly' IDENTIFIED BY 'strong_password';
GRANT SELECT ON datamigrate.* TO 'analytics_readonly';

# Example: Limited user for API
CREATE USER 'api_user' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE ON datamigrate.migrations TO 'api_user';
GRANT SELECT ON datamigrate.users TO 'api_user';
```

### 2. **API Key Rotation**

```python
# Rotate API keys regularly
# Store in environment variables, not code

import os
from datetime import datetime

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')

# Log API key usage
def log_api_usage(user_id, endpoint):
    print(f"[{datetime.now()}] User {user_id} accessed {endpoint}")
```

### 3. **Audit Logging**

```python
# Track all sensitive operations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def track_code_access(user, file_path):
    logger.info(f"User {user} accessed {file_path} at {datetime.now()}")

def track_deployment(user, environment):
    logger.info(f"User {user} deployed to {environment} at {datetime.now()}")
```

### 4. **Git Hooks for Security**

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Prevent committing secrets

# Check for common secret patterns
if git diff --cached | grep -E "(api_key|password|secret|token).*=.*['\"]"; then
    echo "ERROR: Possible secret detected in commit!"
    echo "Remove secrets before committing."
    exit 1
fi

# Check for .env files
if git diff --cached --name-only | grep -E "\.env$"; then
    echo "ERROR: .env file detected in commit!"
    exit 1
fi

exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## 💼 BUSINESS CONSIDERATIONS

### 1. **Incorporate Your Business**

- [ ] **Form an LLC or Corporation** (protects personal assets)
- [ ] Register in startup-friendly state (Delaware, Wyoming)
- [ ] Get an EIN (Employer Identification Number)
- [ ] Open business bank account

**Why:** If you don't have a legal entity, YOU personally own the IP, not a company. This makes it harder to raise funding or sell the business later.

### 2. **Trademark Your Name**

- [ ] Search USPTO database: https://www.uspto.gov/trademarks
- [ ] File trademark for "DataMigrate AI" (costs ~$250-350)
- [ ] Register domain: datamigrate.ai, datamigrate.com
- [ ] Register social media handles

### 3. **Copyright Registration**

- [ ] Register copyright for codebase with US Copyright Office
- [ ] Costs $65 per registration
- [ ] Not required (you own copyright automatically), but gives stronger legal protection
- [ ] File at: https://www.copyright.gov/registration/

### 4. **Patent (Optional)**

- [ ] Consider provisional patent if you have novel AI/ML algorithms
- [ ] Costs $70-300 for provisional, $10,000+ for full patent
- [ ] Only worth it if you have truly novel invention
- [ ] Software patents are expensive and hard to enforce

**For DataMigrate AI:** Probably not worth patenting unless you have breakthrough AI technique.

---

## 📊 MONITORING AND ENFORCEMENT

### 1. **Regular Audits**

- [ ] **Weekly:** Review git commits and access logs
- [ ] **Monthly:** Review GitHub audit log
- [ ] **Quarterly:** Review all collaborator access levels
- [ ] **When someone leaves:** Immediately revoke all access

### 2. **Track Competing Products**

- [ ] Set up Google Alerts for competing products
- [ ] Monitor GitHub for similar repositories
- [ ] Use tools like:
  - GitGuardian (scan for leaked secrets)
  - Snyk (security vulnerabilities)
  - CodeClimate (code quality)

### 3. **If You Detect a Breach**

1. **Document everything** - Take screenshots, save emails
2. **Revoke access immediately** - GitHub, AWS, databases
3. **Consult a lawyer** - Send cease and desist letter
4. **Consider legal action** - Breach of contract, theft of trade secrets
5. **Rotate all credentials** - API keys, passwords, SSH keys

---

## ⚖️ JURISDICTION CONSIDERATIONS

### United States:

- **Non-competes:** Mostly enforceable (except California, North Dakota, Oklahoma)
- **IP assignment:** Strongly enforceable if in writing
- **At-will employment:** Easy to terminate, but must have IP assignment first
- **Recommended state for incorporation:** Delaware (best legal framework for startups)

### California-Specific:

- **Non-competes are VOID** - Can't prevent someone from working for competitor
- **Trade secret protection:** Strong (California Uniform Trade Secrets Act)
- **Workaround:** Use non-solicitation and confidentiality clauses instead

### International:

- **EU (GDPR):** Add data protection clauses if handling EU user data
- **UK:** Non-competes are enforceable if "reasonable in scope and duration"
- **India:** IP assignment clauses are enforceable
- **Remote workers in other countries:** Use agreements governed by YOUR jurisdiction

---

## 📝 SAMPLE ONBOARDING CHECKLIST

When bringing on a new collaborator:

- [ ] Day -7: Send NDA for signature
- [ ] Day -3: Once NDA signed, share high-level overview (no code yet)
- [ ] Day -1: Send Contractor/Employment Agreement for signature
- [ ] Day 0: Once agreements signed, grant GitHub access
- [ ] Day 0: Add to Slack/communication channels
- [ ] Day 0: Share credentials (use 1Password, LastPass, or similar)
- [ ] Day 1: Explain security policies and expectations
- [ ] Day 7: First code review - check for any issues
- [ ] Day 30: Review performance and access levels

**When someone leaves:**

- [ ] Hour 0: Revoke GitHub access
- [ ] Hour 0: Revoke AWS/database access
- [ ] Hour 0: Change any shared passwords
- [ ] Hour 0: Revoke SSH keys
- [ ] Day 1: Rotate API keys they had access to
- [ ] Day 1: Review all code they contributed recently
- [ ] Day 7: Send reminder email about confidentiality obligations

---

## 🎯 FINAL RECOMMENDATIONS

### Minimum Protection (Must Have):

1. ✅ **NDA signed** before any discussions
2. ✅ **Contractor Agreement** with IP assignment before any coding
3. ✅ **Private GitHub repo** with 2FA enabled
4. ✅ **No secrets in code** (use environment variables)
5. ✅ **Copyright notices** in all files

### Recommended Protection (Strongly Advised):

6. ✅ Form an LLC/Corporation
7. ✅ Branch protection rules on GitHub
8. ✅ Regular access audits
9. ✅ Trademark registration
10. ✅ Detailed documentation of contributions

### Advanced Protection (For High-Value IP):

11. ✅ Code watermarking/fingerprinting
12. ✅ Separate repos with limited access
13. ✅ Copyright registration
14. ✅ Security monitoring tools (GitGuardian, etc.)
15. ✅ Legal counsel on retainer

---

## 📞 RESOURCES

### Legal Templates:
- **Rocket Lawyer** - $39.99/month for legal docs
- **LegalZoom** - Incorporation services
- **Clerky** - Startup-specific legal docs ($599+)
- **FAST Agreements** (YC) - Free for US startups

### Security Tools:
- **GitGuardian** - Scan for leaked secrets
- **Snyk** - Security vulnerability scanning
- **1Password** - Team password management
- **LastPass** - Alternative password manager

### Incorporation:
- **Stripe Atlas** - $500 (Delaware C-corp + legal docs)
- **Clerky** - $599+ (DIY incorporation)
- **IncFile** - $0 + state fees (budget option)

### Find a Lawyer:
- **UpCounsel** - Freelance lawyers
- **Rocket Lawyer** - On-demand legal advice
- **Local startup incubators** - Often have free/discounted legal help

---

**⚠️ DISCLAIMER:** This is educational information, not legal advice. Consult a licensed attorney in your jurisdiction for specific legal guidance.

---

**Created for DataMigrate AI Project**
**Author:** Alexander Garcia Angus
**Date:** November 27, 2025
