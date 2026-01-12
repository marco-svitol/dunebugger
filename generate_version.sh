#!/bin/bash
# Generate VERSION file for production deployment
# This creates a JSON file with version information that doesn't require git

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="${SCRIPT_DIR}/VERSION"

echo "Generating VERSION file..."

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "Error: git is required to generate VERSION file"
    exit 1
fi

# Get version from git
VERSION=$(git describe --tags --always 2>/dev/null || echo "0.0.0-unknown")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Parse version
if [[ "$VERSION" =~ ^v?([0-9]+\.[0-9]+\.[0-9]+)(-beta\.([0-9]+))?(-([0-9]+)-g([0-9a-f]+))?(-dirty)?$ ]]; then
    BASE_VERSION="${BASH_REMATCH[1]}"
    BETA="${BASH_REMATCH[3]}"
    COMMITS_SINCE="${BASH_REMATCH[5]}"
    COMMIT_HASH="${BASH_REMATCH[6]}"
    DIRTY="${BASH_REMATCH[7]}"
    
    # Determine build type
    if [ -n "$BETA" ]; then
        if [ -n "$COMMITS_SINCE" ]; then
            BUILD="beta.${BETA}.dev${COMMITS_SINCE}"
        else
            BUILD="beta.${BETA}"
        fi
    elif [ -n "$COMMITS_SINCE" ]; then
        BUILD="dev${COMMITS_SINCE}"
    else
        BUILD="release"
    fi
    
    if [ -n "$DIRTY" ]; then
        BUILD="${BUILD}.dirty"
    fi
    
    if [ -n "$COMMIT_HASH" ]; then
        COMMIT="$COMMIT_HASH"
    fi
else
    # Fallback
    BASE_VERSION="$VERSION"
    BUILD="unknown"
fi

# Create JSON VERSION file
cat > "$VERSION_FILE" <<EOF
{
  "version": "$BASE_VERSION",
  "build": "$BUILD",
  "commit": "$COMMIT"
}
EOF

echo "VERSION file created:"
cat "$VERSION_FILE"
echo ""
echo "Version: $BASE_VERSION-$BUILD+$COMMIT"
