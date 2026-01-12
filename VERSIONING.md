# Versioning and Release Guide

## Overview

This project uses automated semantic versioning with a **production-friendly approach**:
- **Production**: Uses a `VERSION` file (no git dependency)
- **Development**: Falls back to git tags if VERSION file doesn't exist

## Versioning System

### Semantic Versioning

The project follows [Semantic Versioning 2.0.0](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

### Version Resolution Priority

The `version.py` module checks for version information in this order:

1. **VERSION file** (preferred for production)
   - JSON format with version, build, and commit info
   - Created during deployment
   - No dependencies required

2. **Git tags** (fallback for development)
   - Requires git installed
   - Reads from local repository only (no network)
   - Automatically detects current version

3. **Fallback** → `0.0.0-unknown` if neither available

## Production Deployment

### Recommended: Deploy with VERSION File

This approach requires **NO git in production**:

```bash
# On your development/CI machine (where git is available)
cd /path/to/dunebugger
./generate_version.sh

# This creates a VERSION file like:
# {
#   "version": "1.2.3",
#   "build": "release",
#   "commit": "abc1234"
# }

# Copy the code INCLUDING the VERSION file to production
rsync -av --exclude='.git' /path/to/dunebugger/ production-host:/opt/dunebugger/

# On production host (no git required!)
ssh production-host
cd /opt/dunebugger
python3 -c "from app.version import get_version_info; print(get_version_info())"
sudo systemctl restart dunebugger
```

### Alternative: Deploy with Git

If you prefer to use git in production:

```bash
# On production host (requires git)
cd /opt/dunebugger
git fetch --tags
git checkout v1.2.3  # or main/develop
git pull
sudo systemctl restart dunebugger
```

## Development Workflow

### For Developers

No VERSION file needed - git is used automatically:

```bash
cd /path/to/dunebugger
python3 -c "from app.version import get_version_info; print(get_version_info())"
# Automatically reads from git tags
```

### Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Commit Types and Version Impact

##### On Stable Branches (`main`)

| Type | Description | Version Bump | Example |
|------|-------------|--------------|---------|
| `feat` | New feature | MINOR | `1.0.0` → `1.1.0` |
| `fix` | Bug fix | PATCH | `1.0.0` → `1.0.1` |
| `perf` | Performance improvement | PATCH | `1.0.0` → `1.0.1` |
| `docs` | Documentation changes | PATCH | `1.0.0` → `1.0.1` |
| `style` | Code style changes | PATCH | `1.0.0` → `1.0.1` |
| `refactor` | Code refactoring | PATCH | `1.0.0` → `1.0.1` |
| `test` | Test additions/changes | PATCH | `1.0.0` → `1.0.1` |
| `build` | Build system changes | PATCH | `1.0.0` → `1.0.1` |
| `ci` | CI/CD changes | PATCH | `1.0.0` → `1.0.1` |
| `chore` | Other changes | No release | - |
| `feat!` or `BREAKING CHANGE` | Breaking changes | MAJOR | `1.0.0` → `2.0.0` |

##### On Prerelease Branches (`develop`)

| Type | Description | Version Bump | Example |
|------|-------------|--------------|---------|
| `feat` | New feature | PRERELEASE | `1.0.0-beta.4` → `1.0.0-beta.5` |
| `fix` | Bug fix | PRERELEASE | `1.0.0-beta.4` → `1.0.0-beta.5` |
| Any other type | Any change | PRERELEASE | `1.0.0-beta.4` → `1.0.0-beta.5` |
| `chore` | Other changes | No release | - |

## Release Workflow

### 1. Semantic Release (Automated)

When code is merged to `main` or `develop`:
- GitHub Actions analyzes commits
- Creates git tag (e.g., `v1.2.3`)
- Updates CHANGELOG.md
- Creates GitHub release

### 2. Prepare Production Deployment

After a release is created:

```bash
# Clone/pull the release
git clone https://github.com/marco-svitol/dunebugger.git
cd dunebugger
git checkout v1.2.3  # or main

# Generate VERSION file
./generate_version.sh

# Verify
cat VERSION
# Output: {"version": "1.2.3", "build": "release", "commit": "abc1234"}

# Package for deployment (excluding .git)
tar czf dunebugger-v1.2.3.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    .
```

### 3. Deploy to Production

```bash
# Copy package to production
scp dunebugger-v1.2.3.tar.gz production-host:/tmp/

# On production host
ssh production-host
cd /opt
sudo tar xzf /tmp/dunebugger-v1.2.3.tar.gz -C dunebugger
cd dunebugger

# Verify version (no git required!)
python3 -c "from app.version import get_version_info; import json; print(json.dumps(get_version_info(), indent=2))"

# Restart service
sudo systemctl restart dunebugger
```

## Querying Version

### Via Message Queue

Send a message with subject `get_version`:

```python
# Request
{
  "subject": "core.command.get_version",
  "body": {}
}

# Response
{
  "subject": "core.reply.version_info",
  "body": {
    "version": "1.2.3",
    "build": "release",
    "commit": "abc1234",
    "full_version": "1.2.3-release+abc1234"
  }
}
```

### Programmatic Access

```python
from version import get_version_info

info = get_version_info()
print(f"Running version: {info['full_version']}")
```

### Command Line

```bash
# Check version
python3 -c "from app.version import get_version_info; print(get_version_info()['full_version'])"

# Or during startup (check logs)
journalctl -u dunebugger -n 50 | grep -i version
```

## VERSION File Format

### JSON Format (Recommended)

```json
{
  "version": "1.2.3",
  "build": "release",
  "commit": "abc1234"
}
```

### Simple Text Format (Also Supported)

```
1.2.3
```

The version module supports both formats.

## Troubleshooting

### Version Shows 0.0.0-unknown

**Problem**: Application can't determine version.

**Solution**:
1. **Production**: Ensure VERSION file exists and is valid JSON
2. **Development**: Ensure git is installed and tags exist
3. Generate VERSION file: `./generate_version.sh`

### VERSION File vs Git Mismatch

**Problem**: VERSION file shows different version than git.

**Solution**: This is expected! VERSION file is static (deployment snapshot), git shows current checkout. To sync:
```bash
./generate_version.sh  # Regenerate from current git state
```

### Can't Generate VERSION File

**Problem**: `generate_version.sh` fails.

**Solution**:
1. Ensure git is installed
2. Ensure you're in a git repository
3. Ensure at least one tag exists: `git tag -l`

### Production Without Git or VERSION

**Problem**: Production host has neither git nor VERSION file.

**Solution**: 
- **Recommended**: Use `generate_version.sh` before deployment
- **Alternative**: Manually create VERSION file:
  ```bash
  echo '{"version": "1.2.3", "build": "release", "commit": "abc1234"}' > VERSION
  ```

## Best Practices

### ✅ Recommended for Production
- Generate VERSION file during deployment preparation
- Deploy without .git directory
- No git required on production hosts
- Smaller deployment package
- Clear version tracking

### ⚠️ Acceptable for Development/Staging
- Use git directly
- Automatic version detection
- Shows development state (dirty, dev commits)

## System Requirements

### Production (with VERSION file)
- Python 3.x
- No other dependencies!

### Development (with git)
- Python 3.x
- Git installed
- Git repository with tags

## Initial Setup

### GitHub Repository Permissions

For semantic-release workflow:
- Go to Settings → Actions → General → Workflow permissions
- Select "Read and write permissions"
- Check "Allow GitHub Actions to create and approve pull requests"

### First Release

```bash
# Create initial tag
git tag -a v0.1.0 -m "Initial version"
git push origin v0.1.0
```

## References

- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [semantic-release](https://github.com/semantic-release/semantic-release)
