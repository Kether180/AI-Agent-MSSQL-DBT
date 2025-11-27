# Co-Founder Setup Guide for DataMigrate AI

**Your Situation:**
- **You (Alexander):** CEO/CTO + Machine Learning Engineer
- **Co-Founder:** Software Developer → Future Engineering Representative
- **Partnership Type:** Co-founders (not contractor/employee)

---

## 🎯 **Recommended Structure**

### **Equity Split: 60/40**

**Alexander Garcia Angus: 60%**
- CEO/CTO role
- Machine learning and AI expertise
- Built initial prototype (6+ months work)
- LangGraph agent development
- Strategic vision and fundraising

**Co-Founder: 40%**
- Head of Engineering / Engineering Representative
- Backend/frontend development (Go, Python, Vue.js)
- Sales engineering and customer demos
- Team building and recruiting
- Technical partnerships

**Why 60/40 is fair:**
- ✅ Values your prior work and specialized ML skills
- ✅ Keeps co-founder highly motivated (40% is substantial)
- ✅ You retain control as CEO (60% = majority shareholder)
- ✅ Standard in startup world for this scenario
- ✅ Investors will view this as reasonable

### **Vesting Schedule: 4-Year with 1-Year Cliff**

**Everyone vests equally (you AND co-founder):**

```
Year 0 → Year 1: 0% vested (cliff period)
Year 1: 25% vests (cliff milestone)
Month 13-48: 1/48 per month (remaining 75%)
Year 4: 100% vested (fully vested)
```

**Example for your 60%:**
- Month 12: 15% vests (25% of 60%)
- Month 24: 30% vested (50% through)
- Month 48: 60% vested (done!)

**Why vesting matters:**
- Protects you if co-founder leaves after 6 months
- Standard requirement from investors
- Ensures long-term commitment
- You ALSO vest (shows fairness to investors)

---

## 📋 **What You Need to Do (Step-by-Step)**

### **Week 1: Legal Setup**

**Day 1-2: Sign NDA**
- [ ] Fill out [NDA_TEMPLATE.md](NDA_TEMPLATE.md)
- [ ] Both sign via DocuSign or HelloSign
- [ ] **Then and only then** show them the codebase

**Day 3-5: Draft Founders' Agreement**
- [ ] Fill out [FOUNDERS_AGREEMENT_TEMPLATE.md](FOUNDERS_AGREEMENT_TEMPLATE.md)
- [ ] Decide on equity split (recommend 60/40)
- [ ] Decide on roles and responsibilities
- [ ] **CRITICAL:** Have a startup lawyer review ($1,000-2,000)

**Day 6-7: Sign Founders' Agreement**
- [ ] Both sign the final version
- [ ] Store signed copy securely (encrypted cloud + local backup)

### **Week 2: Company Formation**

**Incorporate the Business:**
- [ ] Form Delaware C-Corporation (most VC-friendly)
  - Use **Stripe Atlas** ($500) - easiest for tech startups
  - Or **Clerky** ($599) - DIY option
  - Or local attorney ($2,000-3,000)

- [ ] File **83(b) Election** within 30 days (CRITICAL for tax!)
  - Google "83(b) election IRS form"
  - File with IRS within 30 days of signing Founders' Agreement
  - Saves thousands in future taxes

- [ ] Get **EIN** (Employer Identification Number) - Free from IRS
- [ ] Open **Business Bank Account** (Mercury, Brex, or local bank)
- [ ] Set up **Cap Table** software (Carta or Pulley) - $0-50/month

### **Week 3: Operations Setup**

**GitHub and Code Access:**
- [ ] Add co-founder to private GitHub repo
- [ ] Set up **branch protection** on main branch
- [ ] Enable **2FA** for both accounts
- [ ] Add copyright notices to code files

**Tools and Access:**
- [ ] Company email addresses (Google Workspace: $6/user/month)
- [ ] Project management (Linear, Jira, or Notion)
- [ ] Communication (Slack: free for 2 people)
- [ ] Password manager (1Password Teams: $20/month)

**Define Responsibilities:**
- [ ] Document who owns what (technical decisions vs sales)
- [ ] Set up weekly co-founder sync meeting
- [ ] Agree on decision-making process

---

## 💰 **Compensation Strategy**

### **Option 1: Sweat Equity Only (Recommended for Now)**

**No salaries until funding or revenue**
- Both co-founders work for equity only
- Standard for pre-seed startups
- Shows commitment to investors
- Keeps burn rate at $0

**Expenses covered by company:**
- AWS/hosting costs
- Software licenses (GitHub, tools)
- Domain registration
- Essential business expenses

### **Option 2: Deferred Salary**

**Accrue salaries, pay later:**
- Each co-founder accrues $60K-80K/year
- Recorded as debt on balance sheet
- Paid when you raise Series A or become profitable
- Shows fairness but doesn't drain cash

### **Option 3: Minimal Salary (If you have revenue)**

**Pay $2K-3K/month each:**
- Once you have paying customers
- Cover basic living expenses
- Still mostly equity-driven

**Recommendation for DataMigrate AI:** Start with Option 1 (sweat equity) until you get first paying customers or raise pre-seed funding.

---

## 🔐 **Protecting Your IP (Critical Steps)**

### **Before Co-Founder Sees Any Code:**

1. ✅ **NDA signed** - Prevents sharing your idea
2. ✅ **Founders' Agreement signed** - Company owns all code

### **In the Founders' Agreement:**

**IP Assignment Clause:**
> "All work product, code, designs, inventions, and intellectual property created by Founders during employment belongs exclusively to Company. Founders assign all past, present, and future IP related to Company business."

**This protects you because:**
- Company owns everything (not individual founders)
- If co-founder leaves, they can't take code with them
- Clean IP ownership for investors
- Can sell company without complications

### **GitHub Security:**

```bash
# Make repo private
# Settings → General → Change visibility → Private

# Enable branch protection
# Settings → Branches → Add rule
# ✓ Require pull request reviews
# ✓ Require status checks to pass
# ✓ Include administrators

# Enable 2FA for all collaborators
# Settings → Security → Two-factor authentication
```

### **Add Copyright to All Files:**

**Python files:**
```python
# Copyright (c) 2025 [Your Company Name]
# All rights reserved.
# Proprietary and confidential.
```

**Go files:**
```go
// Copyright (c) 2025 [Your Company Name]
// All rights reserved.
// Proprietary and confidential.
```

---

## 🚨 **Common Mistakes to Avoid**

### **❌ DON'T:**

1. **Start working before signing agreements**
   - Without Founders' Agreement, ownership is unclear
   - Could lose 50% or more in disputes

2. **Give equal equity if contributions aren't equal**
   - You did 6+ months of ML work already
   - 60/40 fairly values your prior contribution

3. **Skip vesting**
   - If co-founder leaves after 3 months with 40%, you're screwed
   - Investors REQUIRE vesting schedules

4. **Incorporate as LLC instead of C-Corp**
   - LLCs are tax pass-throughs (complicated for investors)
   - VCs strongly prefer Delaware C-Corps
   - Can convert later but it's expensive

5. **Forget 83(b) election**
   - Must file within 30 days or pay HUGE taxes later
   - This is the #1 mistake founders make

6. **Handshake agreements**
   - "We trust each other" is not enough
   - 50% of startups have co-founder disputes
   - Get everything in writing

### **✅ DO:**

1. **Sign agreements BEFORE any work**
2. **Use standard 4-year vesting for EVERYONE**
3. **Incorporate as Delaware C-Corp**
4. **File 83(b) election within 30 days**
5. **Have a lawyer review everything** ($1K-2K)
6. **Set up cap table software** (Carta/Pulley)
7. **Document ALL decisions** (meeting notes, emails)
8. **Communicate openly** (co-founder disputes start small)

---

## 📊 **Equity Breakdown Over Time**

### **Day 1: Founding**

| Stakeholder | Ownership |
|-------------|-----------|
| You (Alexander) | 60% |
| Co-Founder | 40% |
| **TOTAL** | **100%** |

### **Year 1: Create Option Pool (15%)**

| Stakeholder | Ownership |
|-------------|-----------|
| You (Alexander) | 51% (60% × 85%) |
| Co-Founder | 34% (40% × 85%) |
| Option Pool | 15% |
| **TOTAL** | **100%** |

### **Year 2: Seed Round ($500K at $2M pre-money)**

| Stakeholder | Ownership | $ Value @ $2.5M post |
|-------------|-----------|---------------------|
| You (Alexander) | 40.8% | $1,020,000 |
| Co-Founder | 27.2% | $680,000 |
| Option Pool | 12% | $300,000 |
| Investors | 20% | $500,000 |
| **TOTAL** | **100%** | **$2,500,000** |

### **Year 5: Series A ($5M at $20M pre-money)**

| Stakeholder | Ownership | $ Value @ $25M post |
|-------------|-----------|---------------------|
| You (Alexander) | 32.6% | $8,150,000 |
| Co-Founder | 21.8% | $5,450,000 |
| Option Pool | 15% | $3,750,000 |
| Seed Investors | 16% | $4,000,000 |
| Series A Investors | 20% | $5,000,000 |
| **TOTAL** | **100%** | **$25,000,000** |

**Key Insight:** Even after dilution, you still own significant percentage and dollar value grows substantially.

---

## 🤝 **Roles and Responsibilities**

### **You (Alexander) - CEO/CTO/ML Engineer:**

**Technical:**
- LangGraph agent architecture and optimization
- Machine learning models and training
- Claude API integration and prompt engineering
- System architecture and infrastructure decisions
- Database design and optimization

**Business:**
- Company strategy and vision
- Fundraising and investor relations
- Financial planning and budgeting
- Board representation
- Final decision authority on tech and strategy

**Time Commitment:** Full-time (40+ hours/week)

---

### **Co-Founder - Head of Engineering / Engineering Rep:**

**Technical:**
- Backend API development (Go + Python)
- Frontend development (Vue.js)
- Database queries and optimization
- Testing and CI/CD pipeline
- Code reviews and quality assurance
- Technical documentation

**Business:**
- Sales engineering (product demos, customer calls)
- Customer-facing technical presentations
- Developer relations and partnerships
- Technical recruiting and team building
- Support and onboarding for technical users

**Time Commitment:** Full-time (40+ hours/week)

**Growth Path:**
- Year 1: Senior Engineer / Engineering Lead
- Year 2: VP of Engineering (as you hire team)
- Year 3+: CTO (you transition to CEO role)

---

## 🎯 **Decision-Making Framework**

### **You Decide (CEO/CTO Authority):**

- ML model architecture and training
- LangGraph agent design
- Infrastructure and cloud provider choices
- Technology stack decisions
- Fundraising strategy and terms
- Financial decisions over $10K
- Hiring C-level executives

### **Co-Founder Decides (Engineering Authority):**

- API endpoint design and implementation
- Frontend architecture and UI/UX
- Code quality standards and practices
- Development tools and workflows
- Technical hiring (engineers)
- Customer demo strategies

### **Decide Together (Unanimous):**

- Company strategy and pivots
- Equity grants to employees
- Major partnerships or contracts
- Selling the company
- Adding new co-founders
- Changing compensation structure
- Office location (if applicable)

### **Dispute Resolution:**

1. Discuss openly (30 days)
2. If no agreement, you have tiebreaker vote (60% shareholder)
3. Co-founder can exit with vested equity if fundamentally disagrees

---

## 💼 **Compensation Examples**

### **Scenario 1: Pre-Seed (Now → First Customers)**

**Your comp:**
- Equity: 60% ownership
- Salary: $0 (sweat equity)
- Expenses: AWS, software covered by company

**Co-Founder comp:**
- Equity: 40% ownership
- Salary: $0 (sweat equity)
- Expenses: Software, equipment covered

**Company expenses:**
- AWS/hosting: ~$500/month
- Software licenses: ~$200/month
- Domain/SSL: ~$50/month
- Total burn: ~$750/month

---

### **Scenario 2: Early Customers ($10K MRR)**

**Your comp:**
- Equity: 60% ownership
- Salary: $3,000/month
- Total: $36K/year + equity

**Co-Founder comp:**
- Equity: 40% ownership
- Salary: $3,000/month
- Total: $36K/year + equity

**Company finances:**
- Revenue: $10K/month ($120K/year)
- Salaries: $6K/month ($72K/year)
- Expenses: $3K/month ($36K/year)
- Profit: $1K/month ($12K/year)

---

### **Scenario 3: Post-Seed Round ($500K raised)**

**Your comp:**
- Equity: 40.8% ownership (diluted but higher value)
- Salary: $80,000/year (below-market CEO salary)
- Total: $80K + equity worth ~$1M

**Co-Founder comp:**
- Equity: 27.2% ownership
- Salary: $70,000/year (below-market engineer salary)
- Total: $70K + equity worth ~$680K

**Company finances:**
- Cash: $500K in bank
- Runway: 18-24 months
- Hiring: 2-3 engineers ($80-100K each)
- Burn rate: $20-25K/month

---

## 📅 **Timeline: First 90 Days**

### **Week 1-2: Legal Foundation**
- [ ] Day 1: Sign NDA
- [ ] Day 3: Share codebase and business plan
- [ ] Day 5: Draft Founders' Agreement
- [ ] Day 7: Hire lawyer to review ($1K-2K)
- [ ] Day 10: Both sign Founders' Agreement
- [ ] Day 12: Incorporate Delaware C-Corp

### **Week 3-4: Company Setup**
- [ ] Day 15: File 83(b) election with IRS (CRITICAL!)
- [ ] Day 17: Get EIN from IRS
- [ ] Day 20: Open business bank account
- [ ] Day 22: Set up cap table software (Carta/Pulley)
- [ ] Day 25: Company email addresses
- [ ] Day 28: GitHub access and security setup

### **Week 5-8: Product Development**
- [ ] Week 5: Co-founder ramps up on codebase
- [ ] Week 6: Define first sprint (2-week cycles)
- [ ] Week 7: Ship first features together
- [ ] Week 8: First customer demo or pilot

### **Week 9-12: Go-to-Market**
- [ ] Week 9: Finalize MVP features
- [ ] Week 10: Create sales materials and demos
- [ ] Week 11: First customer pilots
- [ ] Week 12: Fundraising preparation (if applicable)

---

## 🚀 **Success Metrics**

### **Month 3 Goals:**
- [ ] Product: MVP complete and stable
- [ ] Customers: 2-3 pilot users
- [ ] Team: Co-founder fully onboarded
- [ ] Legal: All agreements signed and filed
- [ ] Fundraising: Deck ready (if raising)

### **Month 6 Goals:**
- [ ] Product: 5-10 paying customers
- [ ] Revenue: $5K-10K MRR
- [ ] Team: Consider first hire
- [ ] Fundraising: Pre-seed or seed round (optional)

### **Month 12 Goals:**
- [ ] Product: 20-50 paying customers
- [ ] Revenue: $20K-50K MRR
- [ ] Team: 2-3 employees
- [ ] Fundraising: Seed round ($500K-1M)

---

## 📞 **Resources**

### **Legal:**
- **Clerky** - Startup incorporation and documents ($599)
- **Stripe Atlas** - Delaware C-corp formation ($500)
- **UpCounsel** - Find startup lawyers
- **YC SAFE/FAST** - Free fundraising documents

### **Cap Table:**
- **Carta** - Industry standard ($0-50/month)
- **Pulley** - Simpler alternative ($0-30/month)
- **Capshare** - Free for small teams

### **Banking:**
- **Mercury** - Startup-focused banking
- **Brex** - Corporate cards + banking
- **SVB** - Silicon Valley Bank (if you raise VC)

### **Accounting:**
- **Pilot** - Bookkeeping for startups ($500-2K/month)
- **Bench** - Alternative bookkeeping
- **QuickBooks** - DIY option ($30/month)

### **Legal Forms:**
- **83(b) Election:** https://www.irs.gov/pub/irs-pdf/i83b.pdf
- **IRS EIN:** https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online

---

## ⚠️ **Final Checklist Before Co-Founder Starts**

- [ ] ✅ NDA signed
- [ ] ✅ Founders' Agreement signed (lawyer reviewed)
- [ ] ✅ Delaware C-Corp incorporated
- [ ] ✅ 83(b) election filed (within 30 days!)
- [ ] ✅ EIN obtained
- [ ] ✅ Business bank account opened
- [ ] ✅ Cap table set up (Carta/Pulley)
- [ ] ✅ GitHub private repo with 2FA
- [ ] ✅ Copyright notices in code files
- [ ] ✅ Company email addresses
- [ ] ✅ Roles and responsibilities documented
- [ ] ✅ Weekly sync meeting scheduled

**If all boxes are checked, you're ready to build together! 🚀**

---

**Created for DataMigrate AI Project**
**Author:** Alexander Garcia Angus
**Date:** November 27, 2025

**Next Steps:**
1. Read this entire document
2. Discuss equity split with co-founder (60/40 recommended)
3. Fill out Founders' Agreement template
4. Hire lawyer to review ($1K-2K)
5. Sign and incorporate!

Good luck! 🎉