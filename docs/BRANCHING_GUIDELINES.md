# Branching Guidelines - DataMigrate AI

**Author:** Alexander Garcia Angus
**Property of:** OKO Investments
**Last Updated:** December 2025

---

## ⚠️ Important Rules

> **NEVER push directly to `main` or `production` branches.**
> **ALWAYS create a Pull Request for code review.**
> **NEVER use `--force` push unless explicitly approved by the lead.**

---

## 🌳 Branch Structure

```
production     ← Deployed to production servers (PROTECTED)
     ↑
   main        ← Stable releases (PROTECTED)
     ↑
  staging      ← Pre-production testing / QA
     ↑
  develop      ← Integration branch for features
     ↑
feature/*      ← Individual feature development
```

### Branch Descriptions

| Branch | Purpose | Who Can Merge | Protection |
|--------|---------|---------------|------------|
| `production` | Live deployed code | Lead only | 🔒 Protected |
| `main` | Stable, tested releases | Lead only | 🔒 Protected |
| `staging` | QA and pre-production testing | Senior devs | 🔒 Protected |
| `develop` | Feature integration | All devs (via PR) | ⚠️ PR Required |
| `feature/*` | New feature development | Feature owner | None |
| `bugfix/*` | Bug fixes | Bug owner | None |
| `hotfix/*` | Emergency production fixes | Lead only | None |

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Kether180/AI-Agent-MSSQL-DBT.git
cd AI-Agent-MSSQL-DBT
```

### 2. Set Up Your Local Environment

```bash
# Fetch all branches
git fetch --all

# See all available branches
git branch -a

# Switch to develop branch
git checkout develop

# Pull latest changes
git pull origin develop
```

---

## 📝 Daily Workflow

### Starting a New Feature

```bash
# 1. Make sure you're on develop and up-to-date
git checkout develop
git pull origin develop

# 2. Create your feature branch
git checkout -b feature/your-feature-name

# Example:
git checkout -b feature/add-postgres-support
git checkout -b feature/improve-sql-parser
git checkout -b feature/add-batch-processing
```

### Working on Your Feature

```bash
# Make your changes, then stage them
git add .

# Commit with a clear message
git commit -m "Add: description of what you added"

# Push your branch to remote
git push -u origin feature/your-feature-name
```

### Commit Message Format

Use these prefixes for clear commit history:

| Prefix | Use For |
|--------|---------|
| `Add:` | New features |
| `Fix:` | Bug fixes |
| `Update:` | Changes to existing features |
| `Remove:` | Deleted code/files |
| `Refactor:` | Code restructuring (no behavior change) |
| `Docs:` | Documentation only |
| `Test:` | Adding/updating tests |

**Examples:**
```bash
git commit -m "Add: PostgreSQL connection pooling"
git commit -m "Fix: SQL injection vulnerability in query builder"
git commit -m "Update: Model router to support GPT-4 Turbo"
git commit -m "Refactor: Split large agent file into modules"
```

---

## 🔄 Merging Your Work

### Step 1: Update Your Branch

Before creating a PR, sync with develop:

```bash
# Switch to develop and get latest
git checkout develop
git pull origin develop

# Switch back to your feature branch
git checkout feature/your-feature-name

# Merge develop into your branch (NOT the other way!)
git merge develop

# Resolve any conflicts, then push
git push origin feature/your-feature-name
```

### Step 2: Create a Pull Request

1. Go to GitHub repository
2. Click "Pull requests" → "New pull request"
3. Set **base**: `develop` ← **compare**: `feature/your-feature-name`
4. Add a clear title and description
5. Request review from a team member
6. Wait for approval before merging

### Step 3: After PR is Merged

```bash
# Switch to develop
git checkout develop

# Pull the merged changes
git pull origin develop

# Delete your local feature branch
git branch -d feature/your-feature-name

# Delete remote feature branch (optional)
git push origin --delete feature/your-feature-name
```

---

## 🐛 Bug Fixes

### For Non-Urgent Bugs

```bash
# Create bugfix branch from develop
git checkout develop
git pull origin develop
git checkout -b bugfix/describe-the-bug

# Fix, commit, push, create PR to develop
```

### For Urgent Production Bugs (Hotfix)

> ⚠️ **Only use hotfix for critical production issues!**

```bash
# Create hotfix from main (NOT develop)
git checkout main
git pull origin main
git checkout -b hotfix/critical-issue-name

# Fix the issue
git add .
git commit -m "Fix: critical issue description"
git push -u origin hotfix/critical-issue-name

# Create PR to BOTH main AND develop
```

---

## ⚠️ Common Mistakes to Avoid

### ❌ DON'T Do This

```bash
# NEVER push directly to protected branches
git push origin main          # ❌ BLOCKED
git push origin production    # ❌ BLOCKED

# NEVER force push to shared branches
git push --force origin develop  # ❌ DANGEROUS

# NEVER merge develop into main yourself
git checkout main
git merge develop             # ❌ USE PR INSTEAD

# NEVER work directly on develop
git checkout develop
# ... make changes ...
git commit                    # ❌ CREATE A FEATURE BRANCH
```

### ✅ DO This Instead

```bash
# Always create a feature branch
git checkout develop
git checkout -b feature/my-work

# Always use Pull Requests for merging

# Always pull before starting work
git pull origin develop

# Always sync your branch before PR
git merge develop
```

---

## 🔧 Useful Commands

### Check Status

```bash
# See current branch and changes
git status

# See all branches (local and remote)
git branch -a

# See commit history
git log --oneline -10

# See what branch you're on
git branch --show-current
```

### Undo Mistakes

```bash
# Undo last commit (keep changes staged)
git reset --soft HEAD~1

# Undo last commit (keep changes unstaged)
git reset HEAD~1

# Discard all local changes (CAREFUL!)
git checkout -- .

# Discard changes to a specific file
git checkout -- path/to/file.py
```

### Stash Changes

```bash
# Save current changes temporarily
git stash

# See stashed changes
git stash list

# Restore stashed changes
git stash pop

# Restore specific stash
git stash apply stash@{0}
```

### Sync with Remote

```bash
# Fetch all remote changes (doesn't merge)
git fetch --all

# Pull changes for current branch
git pull

# Pull specific branch
git pull origin develop
```

---

## 📋 Release Process

### Promoting to Staging

1. All features merged to `develop`
2. Create PR: `develop` → `staging`
3. QA team tests on staging environment
4. Fix any issues found (bugfix branches to staging)

### Promoting to Main

1. Staging tests pass
2. Create PR: `staging` → `main`
3. Lead reviews and approves
4. Tag the release: `git tag -a v1.0.0 -m "Release 1.0.0"`

### Deploying to Production

1. Main is stable and tagged
2. Create PR: `main` → `production`
3. Lead approves and merges
4. Automated deployment triggers

---

## 🆘 Emergency Procedures

### I Accidentally Committed to the Wrong Branch

```bash
# Save your commit hash
git log -1  # Copy the commit hash

# Switch to correct branch
git checkout feature/correct-branch

# Cherry-pick the commit
git cherry-pick <commit-hash>

# Go back and remove from wrong branch
git checkout wrong-branch
git reset --hard HEAD~1
```

### I Have Merge Conflicts

```bash
# See conflicted files
git status

# Open each conflicted file and look for:
# <<<<<<< HEAD
# (your changes)
# =======
# (their changes)
# >>>>>>> branch-name

# Edit the file to resolve, then:
git add <resolved-file>
git commit -m "Resolve merge conflicts"
```

### I Need to Undo a Pushed Commit

```bash
# Create a revert commit (safe for shared branches)
git revert <commit-hash>
git push
```

---

## 📞 Getting Help

- **Stuck on git?** Ask a senior developer before using any `--force` commands
- **Merge conflicts?** Don't panic - ask for help if unsure
- **Accidentally broke something?** Tell the team immediately

---

## 📝 Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY WORKFLOW                           │
├─────────────────────────────────────────────────────────────┤
│  1. git checkout develop                                    │
│  2. git pull origin develop                                 │
│  3. git checkout -b feature/my-feature                      │
│  4. ... make changes ...                                    │
│  5. git add .                                               │
│  6. git commit -m "Add: feature description"                │
│  7. git push -u origin feature/my-feature                   │
│  8. Create Pull Request on GitHub                           │
│  9. Wait for review and approval                            │
│ 10. Merge PR and delete branch                              │
└─────────────────────────────────────────────────────────────┘
```

---

**Copyright:** © 2025 OKO Investments. All rights reserved.
