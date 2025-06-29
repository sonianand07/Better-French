# Configuration Management

## IMPORTANT: API Key Security

**NEVER commit API keys to the repository!**

OpenRouter automatically scans public repositories and disables any exposed API keys.

### Local Development

1. Copy the template: `cp config/config.ini.template config/config.ini`
2. Add your API key to `config/config.ini`
3. The file is now gitignored and won't be committed

### GitHub Actions

API keys should ONLY be stored in GitHub Secrets:
1. Go to Settings → Secrets and variables → Actions
2. Add/Update `OPENROUTER_API_KEY`
3. Workflows will access it via `${{ secrets.OPENROUTER_API_KEY }}`

### Why This Matters

- OpenRouter scans all public GitHub repos
- Any exposed key is immediately disabled
- This protects your account from unauthorized use 