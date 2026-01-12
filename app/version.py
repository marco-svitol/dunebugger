"""
Version information for dunebugger.

Version is read from a VERSION file if it exists (production deployment),
otherwise falls back to git tags (development).
The version follows semantic versioning (MAJOR.MINOR.PATCH).
"""

import subprocess
import re
import json
from pathlib import Path


def _load_from_version_file():
    """
    Try to load version from VERSION file.
    This file should be created during deployment/release.
    
    Returns a tuple of (version, build, commit) or None if file doesn't exist.
    """
    try:
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            content = version_file.read_text().strip()
            # VERSION file can be JSON or simple text
            try:
                data = json.loads(content)
                return (
                    data.get("version", "0.0.0"),
                    data.get("build", "unknown"),
                    data.get("commit", "unknown")
                )
            except json.JSONDecodeError:
                # Simple text format: just version number
                return (content, "release", "unknown")
    except Exception:
        pass
    return None


def _get_git_version():
    """
    Get version information from git tags (fallback for development).
    
    Returns a tuple of (version, build, commit) or None if git is not available.
    """
    try:
        # Get the git repository root (go up from app/ to repo root)
        repo_root = Path(__file__).parent.parent
        
        # Run git describe to get version information
        result = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return None
            
        git_describe = result.stdout.strip()
        
        # Parse the output
        # Format: v1.0.0-beta.5 or v1.0.0-beta.5-3-g2a4b8c9 or v1.0.0-beta.5-dirty
        # Pattern: (tag)-(commits_since)-(commit_hash)-(dirty)
        
        # Check if dirty
        is_dirty = git_describe.endswith("-dirty")
        if is_dirty:
            git_describe = git_describe[:-6]  # Remove -dirty suffix
        
        # Try to parse structured tag format
        match = re.match(r'^v?(.+?)(?:-(\d+)-g([0-9a-f]+))?$', git_describe)
        
        if match:
            version_tag = match.group(1)
            commits_since = match.group(2)
            commit_hash = match.group(3)
            
            # Determine version and build type
            if '-' in version_tag:
                # Pre-release version like 1.0.0-beta.5
                version_parts = version_tag.split('-', 1)
                version = version_parts[0]
                prerelease = version_parts[1]
                
                if commits_since:
                    # Development version with commits since tag
                    build = f"{prerelease}.dev{commits_since}"
                else:
                    # Exact pre-release tag
                    build = prerelease
            else:
                # Release version like 1.0.0
                version = version_tag
                if commits_since:
                    build = f"dev{commits_since}"
                else:
                    build = "release"
            
            if is_dirty:
                build = f"{build}.dirty"
            
            # Get short commit hash
            if commit_hash:
                commit = commit_hash
            else:
                # Get current commit if we're exactly on a tag
                commit_result = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "unknown"
            
            return (version, build, commit)
        
        # Fallback: use git describe output directly
        return (git_describe, "unknown", "unknown")
        
    except (subprocess.SubprocessError, FileNotFoundError, Exception):
        return None


# Try to get version from VERSION file first (production)
_version_info = _load_from_version_file()

# Fall back to git for development
if not _version_info:
    _version_info = _get_git_version()

if _version_info:
    __version__, __build__, __commit__ = _version_info
else:
    # Final fallback when neither VERSION file nor git is available
    __version__ = "0.0.0"
    __build__ = "unknown"
    __commit__ = "unknown"


def get_version_info():
    """Return a dictionary with complete version information."""
    return {
        "version": __version__,
        "build": __build__,
        "commit": __commit__,
        "full_version": f"{__version__}-{__build__}+{__commit__[:7]}" if __commit__ != "unknown" else f"{__version__}-{__build__}"
    }
