# HifzDefend Developer Security Guide

Comprehensive security guide for developers using HifzDefend to protect their development workflow, tools, and supply chain.

## Table of Contents

- [Overview](#overview)
- [Package Manager Security](#package-manager-security)
- [Docker Security](#docker-security)
- [IDE & Code Editor Security](#ide--code-editor-security)
- [Git & GitHub Security](#git--github-security)
- [Development Environment Hardening](#development-environment-hardening)
- [Supply Chain Attack Prevention](#supply-chain-attack-prevention)
- [Best Practices](#best-practices)

---

## Overview

Developers are **prime targets** for supply chain attacks. HifzDefend provides specialized protection for:

- **Package Managers** (npm, pip, yarn, pnpm)
- **Docker** containers and images
- **IDEs** (VS Code, JetBrains, etc.)
- **Git** operations and repositories
- **Development tools** (compilers, build systems)

### Threat Landscape for Developers

1. **Supply Chain Attacks**: Malicious npm/pip packages
2. **Typosquatting**: Packages with similar names to popular libraries
3. **Dependency Confusion**: Internal package names matching public packages
4. **Malicious Extensions**: VS Code extensions with backdoors
5. **Docker Image Vulnerabilities**: Base images with known CVEs
6. **Credential Theft**: Stealing GitHub tokens, AWS keys, SSH keys
7. **Code Injection**: Malicious code in pull requests or dependencies

---

## Package Manager Security

### npm Security

#### How HifzDefend Protects npm

1. **Installation Monitoring**: Detects `npm install`, `npm i`, `yarn add`, `pnpm add`
2. **Typosquatting Detection**: Compares package names against popular packages
3. **Malicious Package Database**: Checks against Snyk, Socket.dev databases
4. **Signature Verification**: Validates package checksums from npmjs.org
5. **Dependency Analysis**: Scans `package.json` for suspicious dependencies

#### Example Detections

```bash
# Typosquatting attempt
$ npm install reqeusts  # Typo: "reqeusts" instead of "requests"

→ HifzDefend: ⚠️ Possible typosquatting detected!
→ Package: reqeusts
→ Did you mean: requests (Levenshtein distance: 2)
→ Threat Score: 70 (HIGH)
→ Action: Installation paused
→ Recommendation: Run "npm install requests" instead

# Malicious package
$ npm install malicious-logger

→ HifzDefend: 🚨 MALICIOUS PACKAGE DETECTED!
→ Package: malicious-logger
→ Reason: Flagged by Snyk (CVE-2024-12345)
→ Description: Contains credential-stealing code
→ Threat Score: 95 (CRITICAL)
→ Action: Installation blocked
→ Details: https://snyk.io/vuln/npm:malicious-logger
```

#### Whitelisting Trusted Packages

```toml
# config/hifzdefend.toml
[monitoring.package_manager.npm]
# Trusted packages (no alerts)
trusted_packages = [
    "react",
    "express",
    "lodash",
    "axios",
]

# Trusted package scopes
trusted_scopes = [
    "@types/*",           # TypeScript definitions
    "@my-company/*",      # Internal packages
]

# Skip typosquatting check for these (if you intentionally use similar names)
typosquat_exceptions = [
    "color",    # Don't alert for "colour" vs "color"
]
```

#### Manual Package Checking

```bash
# Check package before installing
hifzdefend check-package npm lodash

# Output:
# Package: lodash
# Latest Version: 4.17.21
# Downloads/Week: 28,000,000
# Security Issues: 0
# Snyk Rating: ✓ Clean
# Socket.dev Rating: ✓ Clean
# Recommendation: Safe to install

# Check specific version
hifzdefend check-package npm lodash@4.17.20

# Check package.json file
hifzdefend check-packages package.json
```

#### npm Audit Integration

```bash
# Auto-run npm audit after install
[monitoring.package_manager.npm]
run_audit_after_install = true

# Alert on vulnerabilities
alert_on_moderate = false
alert_on_high = true
alert_on_critical = true
```

---

### pip Security (Python)

#### How HifzDefend Protects pip

1. **Installation Monitoring**: Detects `pip install`, `pip3 install`, `poetry add`
2. **PyPI Validation**: Verifies packages exist on official PyPI
3. **Checksum Verification**: Validates SHA256 hashes
4. **Malicious Package Database**: Checks against known malicious Python packages
5. **Dependency Scanner**: Analyzes `requirements.txt`, `Pipfile`, `pyproject.toml`

#### Example Detections

```bash
# Typosquatting
$ pip install reqeusts

→ HifzDefend: ⚠️ Possible typosquatting detected!
→ Package: reqeusts
→ Did you mean: requests (Levenshtein distance: 2)
→ Threat Score: 70 (HIGH)

# Malicious package
$ pip install python-malware

→ HifzDefend: 🚨 MALICIOUS PACKAGE!
→ Package: python-malware
→ Reason: Contains obfuscated code that steals environment variables
→ Threat Score: 95 (CRITICAL)
→ Action: Installation blocked
```

#### Whitelisting Python Packages

```toml
[monitoring.package_manager.pip]
trusted_packages = [
    "requests",
    "numpy",
    "pandas",
    "flask",
    "django",
]

# Allow packages from private PyPI
trusted_registries = [
    "https://pypi.my-company.com",
]
```

#### Checking Python Packages

```bash
# Check package before install
hifzdefend check-package pip requests

# Check requirements.txt
hifzdefend check-packages requirements.txt

# Output:
# Scanning requirements.txt...
# ✓ requests==2.31.0 (clean)
# ✓ numpy==1.24.3 (clean)
# ⚠️ old-package==0.1.0 (deprecated, last update: 2015)
# 🚨 malicious-lib==1.0.0 (MALICIOUS - blocked)
```

---

## Docker Security

### Image Scanning

#### How HifzDefend Protects Docker

1. **Pre-Run Scanning**: Scans images before containers start (Trivy integration)
2. **Base Image Validation**: Checks base images for CVEs
3. **Dockerfile Analysis**: Detects suspicious commands
4. **Secrets Detection**: Scans layers for API keys, passwords
5. **Privileged Container Alerts**: Warns on `--privileged` flag

#### Example Detections

```bash
# Vulnerable image
$ docker pull nginx:1.10

→ HifzDefend: ⚠️ Vulnerable Docker image detected
→ Image: nginx:1.10
→ Vulnerabilities: 23 total (5 critical, 8 high, 10 medium)
→ Threat Score: 75 (HIGH)
→ Recommendation: Use nginx:latest or nginx:1.25
→ Details: Run "docker scan nginx:1.10" for full report

# Privileged container
$ docker run --privileged suspicious-image

→ HifzDefend: ⚠️ Privileged container detected!
→ Image: suspicious-image
→ Risk: Container has full access to host system
→ Threat Score: 85 (HIGH)
→ Action: User confirmation required
→ Continue? (y/N)

# Secrets in image
$ docker build -t myapp .

→ HifzDefend: 🚨 SECRETS DETECTED IN IMAGE!
→ Image: myapp
→ Findings:
→   - AWS Access Key: AKIA... (layer 3)
→   - Private SSH Key (layer 5)
→ Threat Score: 100 (CRITICAL)
→ Action: Build blocked
→ Recommendation: Use Docker secrets or environment variables
```

#### Docker Security Configuration

```toml
[monitoring.docker]
enabled = true

# Scan before running containers
scan_before_run = true

# Block privileged containers
block_privileged = true

# Scan for secrets
scan_for_secrets = true

# Trivy scanner settings
trivy_enabled = true
trivy_severity_threshold = "HIGH"  # Block on HIGH or CRITICAL

# Maximum image age (alert if older)
max_image_age_days = 30

# Trusted registries
trusted_registries = [
    "docker.io",
    "ghcr.io",
    "my-company.azurecr.io",
]

# Whitelisted images (skip scanning)
whitelisted_images = [
    "nginx:latest",
    "postgres:15",
]
```

#### Manual Docker Scanning

```bash
# Scan specific image
hifzdefend scan-docker nginx:1.10

# Output:
# Scanning nginx:1.10...
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Vulnerabilities Summary:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CRITICAL: 5
# HIGH:     8
# MEDIUM:   10
# LOW:      15
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Details:
# CVE-2024-12345 (CRITICAL): OpenSSL vulnerability
# CVE-2024-12346 (HIGH): glibc buffer overflow
# ...

# Scan Dockerfile
hifzdefend scan-dockerfile Dockerfile

# Scan all images
docker images --format "{{.Repository}}:{{.Tag}}" | xargs -I {} hifzdefend scan-docker {}
```

#### Dockerfile Best Practices

**Secure Dockerfile Template**:

```dockerfile
# Use specific version (not :latest)
FROM node:18.17.1-alpine AS builder

# Run as non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Don't include secrets
# ❌ BAD: COPY .env .
# ✓ GOOD: Use Docker secrets or environment variables

# Minimal layers
COPY package*.json ./
RUN npm ci --only=production

COPY --chown=nodejs:nodejs . .

# Run as non-root
USER nodejs

EXPOSE 3000
CMD ["node", "server.js"]
```

---

## IDE & Code Editor Security

### VS Code Extension Security

#### How HifzDefend Protects VS Code

1. **Extension Monitoring**: Watches `~/.vscode/extensions` directory
2. **Manifest Analysis**: Checks `package.json` for excessive permissions
3. **Reputation Check**: Validates extensions against VS Code Marketplace
4. **Update Monitoring**: Alerts on extension updates with new permissions

#### Example Detections

```bash
# Suspicious extension installed
→ HifzDefend: ⚠️ VS Code extension with suspicious permissions
→ Extension: random-formatter v1.0.0
→ Publisher: unknown-dev (0 installs)
→ Permissions:
→   - workspace.fs.readWrite (reads/writes all files)
→   - network.sendRequest (sends data to internet)
→ Threat Score: 75 (HIGH)
→ Recommendation: Review extension before enabling

# Malicious extension
→ HifzDefend: 🚨 MALICIOUS EXTENSION DETECTED!
→ Extension: evil-linter
→ Reason: Extension steals workspace files and sends to remote server
→ Threat Score: 95 (CRITICAL)
→ Action: Extension disabled and quarantined
```

#### VS Code Configuration

```toml
[monitoring.ide.vscode]
enabled = true

# Check extension permissions
check_extension_permissions = true

# Trusted extensions (no alerts)
whitelist_extensions = [
    "ms-python.python",
    "GitHub.copilot",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
]

# Trusted publishers
whitelist_publishers = [
    "Microsoft",
    "GitHub",
    "Atlassian",
]

# Alert on new permissions after update
alert_on_permission_changes = true
```

#### Manual Extension Checking

```bash
# Check extension before installing
hifzdefend check-extension "publisher.extension-name"

# Output:
# Extension: prettier-vscode
# Publisher: esbenp
# Rating: 4.8/5 (12M installs)
# Permissions:
#   - workspace.fs.readWrite (read/format files)
# Last Updated: 2025-12-15
# Security Issues: 0
# Recommendation: ✓ Safe to install

# List all installed extensions
hifzdefend list-extensions

# Audit extensions
hifzdefend audit-extensions
```

---

### Claude Code CLI Security

#### How HifzDefend Protects Claude CLI

1. **Command Monitoring**: Tracks all Claude CLI executions
2. **Injection Detection**: Detects command injection attempts
3. **File Access Tracking**: Monitors which files Claude accesses
4. **Prompt Validation**: Scans prompts for malicious patterns

#### Configuration

```toml
[monitoring.ide.claude_code_cli]
enabled = true

# Monitor Claude activity
monitor_commands = true
monitor_file_access = true

# Alert on suspicious patterns
alert_on_system_modification = true
alert_on_credential_access = true

# Trusted commands (no alerts)
whitelist_patterns = [
    "read file:*",
    "write file:src/*",
]
```

---

## Git & GitHub Security

### Repository Monitoring

#### How HifzDefend Protects Git

1. **Clone Monitoring**: Tracks all `git clone` operations
2. **Remote Repository Validation**: Checks repository URLs for suspicious domains
3. **Credential Theft Prevention**: Monitors for credential-stealing scripts
4. **Commit Scanning**: Scans commits for secrets (API keys, passwords)

#### Example Detections

```bash
# Suspicious repository clone
$ git clone https://evil-repo.com/malware.git

→ HifzDefend: ⚠️ Repository from untrusted domain
→ URL: https://evil-repo.com/malware.git
→ Domain: evil-repo.com (not in trusted list)
→ Threat Score: 60 (WARNING)
→ Action: Repository will be scanned after clone
→ Continue? (y/N)

# Secrets in commit
$ git commit -m "Add API keys"

→ HifzDefend: 🚨 SECRETS DETECTED IN COMMIT!
→ Findings:
→   - AWS Access Key: AKIA... (config.js:12)
→   - Private Key: -----BEGIN (keys/private.key)
→ Threat Score: 100 (CRITICAL)
→ Action: Commit blocked
→ Recommendation: Remove secrets, use environment variables
```

#### Git Security Configuration

```toml
[monitoring.git]
enabled = true

# Monitor repository clones
monitor_clone = true
alert_on_untrusted_domain = true

# Scan commits for secrets
scan_commits = true
block_commits_with_secrets = true

# Trusted domains
trusted_domains = [
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "dev.azure.com",
]

# Patterns to detect as secrets
secret_patterns = [
    "AKIA[0-9A-Z]{16}",              # AWS Access Key
    "-----BEGIN (RSA |EC )?PRIVATE KEY-----",  # Private keys
    "sk_live_[0-9a-zA-Z]{24}",       # Stripe keys
    "ghp_[0-9a-zA-Z]{36}",           # GitHub tokens
]
```

#### Git Hooks Integration

**Pre-commit Hook** (`.git/hooks/pre-commit`):

```bash
#!/bin/bash
# HifzDefend pre-commit hook

# Scan staged files for secrets
hifzdefend scan-commit

if [ $? -ne 0 ]; then
    echo "❌ Commit blocked by HifzDefend (secrets detected)"
    echo "Run: git diff --staged to review changes"
    exit 1
fi

echo "✓ HifzDefend: Commit clean"
exit 0
```

Install hook:
```bash
hifzdefend install-git-hooks
```

---

## Development Environment Hardening

### Environment Variable Protection

```toml
[monitoring.environment]
enabled = true

# Monitor .env file access
monitor_env_files = true

# Alert if .env accessed by unknown process
alert_on_env_access = true

# Trusted processes that can read .env
whitelist_processes = [
    "node.exe",
    "python.exe",
    "Code.exe",
]

# Encrypt .env files at rest
encrypt_env_files = true
```

### SSH Key Protection

```toml
[monitoring.credentials.ssh]
enabled = true

# Monitor SSH key directory
monitor_ssh_dir = true

# Alert on SSH key access
alert_on_key_access = true
alert_on_key_copy = true

# Trusted SSH key consumers
whitelist_ssh_access = [
    "ssh.exe",
    "git.exe",
    "Code.exe",  # VS Code Remote
]
```

### API Key Protection

```bash
# Scan directory for exposed API keys
hifzdefend scan-secrets "C:\Projects\myapp"

# Output:
# Scanning C:\Projects\myapp...
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚨 SECRETS FOUND:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# File: config.js:12
# Type: AWS Access Key
# Value: AKIA****************ABCD
# Severity: CRITICAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# File: .env
# Type: Stripe Secret Key
# Value: sk_live_********************1234
# Severity: CRITICAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Recommendation: Move secrets to environment variables or secret manager
```

---

## Supply Chain Attack Prevention

### Dependency Confusion Prevention

#### What is Dependency Confusion?

Attack where internal package names (e.g., `@mycompany/utils`) match public packages on npm/PyPI, causing package managers to download malicious public versions.

#### How HifzDefend Prevents Dependency Confusion

```toml
[monitoring.package_manager.dependency_confusion]
enabled = true

# Internal package scopes (only install from private registry)
internal_scopes = [
    "@mycompany",
    "@internal",
]

# Private registry URLs
private_registries = {
    "@mycompany" = "https://npm.my-company.com",
    "@internal" = "https://registry.internal.com",
}

# Block public packages matching internal names
block_public_internal_names = true

# Alert on confusion attempts
alert_on_confusion_attempt = true
```

#### Example Detection

```bash
# Dependency confusion attempt
$ npm install @mycompany/utils

→ HifzDefend: 🚨 DEPENDENCY CONFUSION DETECTED!
→ Package: @mycompany/utils
→ Issue: Public package found with internal company scope
→ Expected: https://npm.my-company.com/@mycompany/utils
→ Actual: https://registry.npmjs.org/@mycompany/utils (MALICIOUS)
→ Threat Score: 100 (CRITICAL)
→ Action: Installation blocked
→ Recommendation: Configure .npmrc to use private registry
```

---

### Lockfile Integrity

```toml
[monitoring.package_manager.lockfile]
# Detect unauthorized lockfile changes
monitor_lockfile = true

# Alert on hash mismatches
alert_on_hash_mismatch = true

# Files to monitor
monitored_lockfiles = [
    "package-lock.json",
    "yarn.lock",
    "Pipfile.lock",
    "poetry.lock",
]
```

#### Example Detection

```bash
# Lockfile tampering detected
→ HifzDefend: ⚠️ Lockfile integrity violation
→ File: package-lock.json
→ Change: lodash@4.17.21 hash changed
→ Expected: sha512-abc123...
→ Actual:   sha512-def456... (MISMATCH)
→ Threat Score: 80 (HIGH)
→ Action: Installation blocked
→ Recommendation: Review changes with "git diff package-lock.json"
```

---

## Best Practices

### Daily Development Workflow

1. **Morning Check**:
   ```bash
   hifzdefend monitor status
   hifzdefend alerts list --since yesterday
   ```

2. **Before Installing Packages**:
   ```bash
   # npm
   hifzdefend check-package npm <package-name>

   # pip
   hifzdefend check-package pip <package-name>
   ```

3. **Before Pulling Docker Images**:
   ```bash
   hifzdefend scan-docker <image>:<tag>
   ```

4. **Before Installing VS Code Extensions**:
   ```bash
   hifzdefend check-extension <extension-id>
   ```

5. **Before Committing Code**:
   ```bash
   hifzdefend scan-commit
   ```

6. **End of Day**:
   ```bash
   hifzdefend audit-environment
   hifzdefend check-for-updates
   ```

---

### Security Checklist for New Projects

- [ ] Initialize HifzDefend for project directory
- [ ] Install git hooks: `hifzdefend install-git-hooks`
- [ ] Configure `.npmrc` / `pip.conf` for private registries
- [ ] Add `.env` to `.gitignore`
- [ ] Scan project for existing secrets: `hifzdefend scan-secrets .`
- [ ] Whitelist trusted development tools
- [ ] Configure Docker scanning
- [ ] Enable commit scanning
- [ ] Set up automated package audits

---

### Recommended Configuration for Developers

```toml
# ~/.config/hifzdefend/hifzdefend.toml

[monitoring]
enabled = true
check_interval = 30  # More frequent checks for active development

# Package manager security (HIGH priority)
[monitoring.package_manager]
enabled = true
npm = true
pip = true
typosquat_threshold = 2  # Sensitive to typos
verify_signatures = true

# Docker security
[monitoring.docker]
enabled = true
scan_before_run = true
block_privileged = true

# IDE security
[monitoring.ide]
enabled = true
vscode = true
claude_code_cli = true

# Git security
[monitoring.git]
enabled = true
scan_commits = true
block_commits_with_secrets = true

# Less noisy monitors (MEDIUM priority)
[monitoring.registry]
enabled = false  # Not needed for development

[monitoring.ransomware]
enabled = true
monitored_directories = [
    "C:\\Users\\richa\\Projects",  # Only monitor project directories
]

# Automated responses
[rules.automated_responses]
auto_quarantine_critical = true
auto_backup_on_ransomware = true
desktop_notification_critical = true
desktop_notification_high = true
desktop_notification_warning = false  # Too noisy for development
```

---

**Last Updated**: 2026-01-25
**Version**: Phase 1.5
