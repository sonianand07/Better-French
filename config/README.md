# Configuration Management

## 🚨 CRITICAL: API Key Security

### The Problem
OpenRouter automatically scans GitHub repositories for exposed API keys and **disables them immediately**. This has happened multiple times to this project.

### Root Cause
The `config.ini` file was being tracked in git, and every time someone committed an API key update, it became publicly visible and got auto-disabled.

## ✅ Current Security Setup

### 1. Local Development
- `config.ini` - Contains real API keys (⚠️ NEVER COMMIT)
- `config.ini.template` - Safe template (✅ can commit)
- `config.ini` is in `.gitignore` and should never appear in `git status`

### 2. Production/CI
- API keys stored in **GitHub Secrets** only
- Workflows use `${{ secrets.OPENROUTER_API_KEY }}`
- No keys in code or config files

### 3. Safety Measures
- **Pre-commit hook** - Blocks commits containing API keys
- **Template system** - Prevents accidental key exposure
- **Documentation** - Clear security guidelines

## 🔧 Setup Instructions

### For New Developers:
```bash
# 1. Copy template to create local config
cp config/config.ini.template config/config.ini

# 2. Edit with your real API key
nano config/config.ini

# 3. Verify it's not tracked (should show nothing)
git status config/config.ini

# 4. Enable pre-commit hooks
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

### For Production Deployment:
```bash
# Store API key in GitHub Secrets (one time setup)
gh secret set OPENROUTER_API_KEY --repo sonianand07/Better-French
```

## 🛡️ Security Rules

### ✅ DO:
- Store keys in GitHub Secrets for production
- Use local `config.ini` for development (ignored by git)
- Run pre-commit hooks to catch accidents
- Use environment variables in code: `os.getenv("OPENROUTER_API_KEY")`

### ❌ NEVER:
- Commit API keys to any file tracked by git
- Put keys in code comments or documentation
- Share keys in chat/email/screenshots
- Disable the pre-commit hooks

## 🚨 If a Key Gets Exposed:

1. **OpenRouter will auto-disable it** (usually within minutes)
2. **Generate a new key** from OpenRouter dashboard
3. **Update GitHub Secrets** with new key
4. **Update local config.ini** with new key
5. **Never commit the new key** to git

## 📋 Verification Checklist

Before any commit:
- [ ] `git status` doesn't show `config/config.ini`
- [ ] Pre-commit hook is enabled and running
- [ ] No API keys in staged files
- [ ] New keys stored in GitHub Secrets only

---

**Remember: A single exposed API key can break the entire pipeline!** 