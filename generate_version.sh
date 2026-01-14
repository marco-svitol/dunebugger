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
    
    # Get build number (total commit count)
    BUILD_NUMBER=$(git rev-list --count HEAD 2>/dev/null || echo "0")
    
    # Determine build type and prerelease identifier
    PRERELEASE=""
    if [ -n "$BETA" ]; then
        PRERELEASE="beta.${BETA}"
        if [ -n "$COMMITS_SINCE" ]; then
            BUILD_TYPE="prerelease-dev"
            BUILD_SUFFIX=".dev${COMMITS_SINCE}"
        else
            BUILD_TYPE="prerelease"
            BUILD_SUFFIX=""
        fi
    elif [ -n "$COMMITS_SINCE" ]; then
        BUILD_TYPE="development"
        BUILD_SUFFIX=".dev${COMMITS_SINCE}"
    else
        BUILD_TYPE="release"
        BUILD_SUFFIX=""
    fi
    
    if [ -n "$DIRTY" ]; then
        BUILD_SUFFIX="${BUILD_SUFFIX}.dirty"
    fi
    
    if [ -n "$COMMIT_HASH" ]; then
        COMMIT="$COMMIT_HASH"
    fi
else
    # Fallback
    BASE_VERSION="$VERSION"
    BUILD_TYPE="unknown"
    BUILD_SUFFIX=""
    BUILD_NUMBER="0"
fi

# Construct the build identifier (semantic-release compatible)
if [ -n "$PRERELEASE" ]; then
    # Prerelease: e.g., "beta.1" or "beta.1.dev2"
    BUILD="${PRERELEASE}${BUILD_SUFFIX}"
    FULL_VERSION="${BASE_VERSION}-${BUILD}"
else
    # Release or development: e.g., "release" or "dev2"
    if [ "$BUILD_TYPE" = "development" ]; then
        BUILD="dev${COMMITS_SINCE}${BUILD_SUFFIX}"
        FULL_VERSION="${BASE_VERSION}-${BUILD}"
    else
        BUILD="release${BUILD_SUFFIX}"
        if [ "$BUILD_SUFFIX" = "" ]; then
            FULL_VERSION="${BASE_VERSION}"
        else
            FULL_VERSION="${BASE_VERSION}-${BUILD}"
        fi
    fi
fi

# Create JSON VERSION file
cat > "$VERSION_FILE" <<EOF
{
  "version": "$BASE_VERSION",
  "prerelease": "${PRERELEASE:-null}",
  "build_type": "$BUILD_TYPE",
  "build_number": $BUILD_NUMBER,
  "commit": "$COMMIT",
  "full_version": "$FULL_VERSION"
}
EOF

echo "VERSION file created:"
cat "$VERSION_FILE"
echo ""
echo "Full version: $FULL_VERSION (build #$BUILD_NUMBER)"
