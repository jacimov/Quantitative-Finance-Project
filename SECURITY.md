# Security Policy

## Protecting API Keys and Sensitive Information

This project requires API keys and secrets for various trading platforms. **Never commit these credentials to version control.**

### Best Practices

1. **Use Environment Variables**
   - Store all API keys and secrets in environment variables
   - Use a `.env` file for local development (already gitignored)
   - Copy `.env.example` to `.env` and fill in your credentials

2. **Verify .gitignore**
   - The `.gitignore` file already excludes:
     - `.env` and related files
     - `kalshi_private_key.pem`
     - Local configuration files (`config/*.local.yaml`)
   
3. **Never Hardcode Credentials**
   - ❌ Bad: `api_key = "pk_12345678"`
   - ✅ Good: `api_key = os.getenv('ALPACA_API_KEY')`

4. **Example Code**
   - Placeholder values like `YOUR_API_KEY` are safe and used only for documentation
   - Always replace with environment variable access in production

### Setting Up Credentials

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your actual credentials:
   ```bash
   ALPACA_API_KEY=your_actual_key_here
   ALPACA_API_SECRET=your_actual_secret_here
   ```

3. For Kalshi, place your private key file in the project root:
   ```bash
   # This file is already in .gitignore
   kalshi_private_key.pem
   ```

4. Load environment variables in your code:
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()  # Load from .env file
   
   api_key = os.getenv('ALPACA_API_KEY')
   api_secret = os.getenv('ALPACA_API_SECRET')
   ```

### What's Already Protected

✅ **Good Security Practices in This Repository:**
- `.gitignore` properly excludes sensitive files
- All production code uses `os.getenv()` for credentials
- Example code uses clear placeholders (`YOUR_API_KEY`)
- Private key files are excluded from version control
- No hardcoded secrets found in git history

### Reporting Security Issues

If you discover a security vulnerability, please email the maintainer directly rather than opening a public issue.

### Additional Recommendations

1. **Use Different Keys for Development and Production**
   - Use paper trading accounts for testing
   - Keep production API keys separate and more restricted

2. **Rotate Keys Regularly**
   - Change API keys periodically
   - Immediately rotate any keys that may have been exposed

3. **Limit API Key Permissions**
   - Use the minimum required permissions for each key
   - Enable IP whitelisting where available

4. **Enable Two-Factor Authentication**
   - Enable 2FA on all trading platform accounts
   - Use strong, unique passwords

5. **Consider Using Secret Management Tools**
   - For production deployments, consider using:
     - AWS Secrets Manager
     - HashiCorp Vault
     - Azure Key Vault
     - GitHub Secrets (for CI/CD)

### Pre-commit Hook (Optional)

To prevent accidentally committing secrets, consider using a pre-commit hook with secret scanning:

```bash
pip install pre-commit detect-secrets
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

Run:
```bash
pre-commit install
detect-secrets scan > .secrets.baseline
```
