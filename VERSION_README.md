# Dunebugger Versioning

## Quick Start

### For Production Deployment (No Git Required)

```bash
# Step 1: On your build/CI machine (with git)
cd /path/to/dunebugger
git checkout v1.2.3  # or main
./generate_version.sh

# Step 2: Deploy to production (without .git)
tar czf dunebugger.tar.gz --exclude='.git' --exclude='__pycache__' .
scp dunebugger.tar.gz production:/tmp/

# Step 3: On production (no git needed!)
ssh production
cd /opt/dunebugger
tar xzf /tmp/dunebugger.tar.gz
python3 -c "from app.version import get_version_info; print(get_version_info())"
sudo systemctl restart dunebugger
```

### For Development

```bash
# No setup needed - automatically uses git
python3 -c "from app.version import get_version_info; print(get_version_info())"
```

## How It Works

### Two-Tier Version Detection

1. **Production Path** (Preferred)
   - Reads from `VERSION` file
   - Generated once during deployment prep
   - **No git dependency**
   - **No internet required**
   - **Works offline**

2. **Development Path** (Fallback)
   - Reads from git tags using `git describe`
   - **Local operation only** (no network calls)
   - Shows current development state
   - Automatically detects dirty/dev state

### Benefits

✅ **Production-Friendly**
- No git binary required in production
- No .git directory needed
- Smaller deployment packages
- Faster startup (no git subprocess)
- Works in restricted environments

✅ **Developer-Friendly**
- Automatic version detection in development
- Shows dirty/dev state
- No manual version file maintenance

✅ **Completely Offline**
- VERSION file approach: no dependencies
- Git approach: local only, no network
- Both work without internet

## Files

- `app/version.py` - Version detection module
- `generate_version.sh` - Creates VERSION file from git
- `VERSION` - Static version file (generated, not committed)
- `VERSIONING.md` - Complete documentation

## See Also

Read [VERSIONING.md](VERSIONING.md) for complete documentation.
