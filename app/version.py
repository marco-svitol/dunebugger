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
from dunebugger_settings import settings

def _load_from_version_file():
    """
    Try to load version from VERSION file.
    This file should be created during deployment/release.
    
    Returns a dict with version info or None if file doesn't exist.
    """
    try:
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            content = version_file.read_text().strip()
            # VERSION file can be JSON or simple text
            try:
                data = json.loads(content)
                # New format with semantic-release alignment
                if "full_version" in data:
                    return {
                        "version": data.get("version", "0.0.0"),
                        "prerelease": data.get("prerelease"),
                        "build_type": data.get("build_type", "unknown"),
                        "build_number": data.get("build_number", 0),
                        "commit": data.get("commit", "unknown"),
                        "full_version": data.get("full_version")
                    }
                # Legacy format
                else:
                    return {
                        "version": data.get("version", "0.0.0"),
                        "build_type": data.get("build", "unknown"),
                        "commit": data.get("commit", "unknown"),
                        "full_version": f"{data.get('version', '0.0.0')}-{data.get('build', 'unknown')}"
                    }
            except json.JSONDecodeError:
                # Simple text format: just version number
                return {
                    "version": content,
                    "build_type": "release",
                    "commit": "unknown",
                    "full_version": content
                }
    except Exception:
        pass
    return None


def _get_git_version():
    """
    Get version information from git tags (fallback for development).
    
    Returns a dict with version info or None if git is not available.
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
            
            # Get build number (total commit count)
            build_number_result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            build_number = int(build_number_result.stdout.strip()) if build_number_result.returncode == 0 else 0
            
            # Determine version and build type
            prerelease = None
            if '-' in version_tag:
                # Pre-release version like 1.0.0-beta.5
                version_parts = version_tag.split('-', 1)
                version = version_parts[0]
                prerelease = version_parts[1]
                
                if commits_since:
                    # Development version with commits since tag
                    build_type = "prerelease-dev"
                    build_suffix = f".dev{commits_since}"
                else:
                    # Exact pre-release tag
                    build_type = "prerelease"
                    build_suffix = ""
            else:
                # Release version like 1.0.0
                version = version_tag
                if commits_since:
                    build_type = "development"
                    build_suffix = f".dev{commits_since}"
                else:
                    build_type = "release"
                    build_suffix = ""
            
            if is_dirty:
                build_suffix = f"{build_suffix}.dirty" if build_suffix else ".dirty"
            
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
            
            # Construct full version string
            if prerelease:
                full_version = f"{version}-{prerelease}{build_suffix}"
            elif build_suffix:
                full_version = f"{version}{build_suffix}"
            else:
                full_version = version
            
            return {
                "version": version,
                "prerelease": prerelease,
                "build_type": build_type,
                "build_number": build_number,
                "commit": commit,
                "full_version": full_version
            }
        
        # Fallback: use git describe output directly
        return {
            "version": git_describe,
            "build_type": "unknown",
            "commit": "unknown",
            "full_version": git_describe
        }
        
    except (subprocess.SubprocessError, FileNotFoundError, Exception):
        return None


# Try to get version from VERSION file first (production)
_version_info = _load_from_version_file()

# Fall back to git for development
if not _version_info:
    _version_info = _get_git_version()

if _version_info:
    __version__ = _version_info.get("version", "0.0.0")
    __prerelease__ = _version_info.get("prerelease")
    __build_type__ = _version_info.get("build_type", "unknown")
    __build_number__ = _version_info.get("build_number", 0)
    __commit__ = _version_info.get("commit", "unknown")
    __full_version__ = _version_info.get("full_version", __version__)
else:
    # Final fallback when neither VERSION file nor git is available
    __version__ = "0.0.0"
    __prerelease__ = None
    __build_type__ = "unknown"
    __build_number__ = 0
    __commit__ = "unknown"
    __full_version__ = "0.0.0-unknown"


def get_version_info():
    """Return a dictionary with complete version information."""
    info = {
        "component": settings.mQueueClientID,
        "version": __version__,
        "build_type": __build_type__,
        "build_number": __build_number__,
        "commit": __commit__,
        "full_version": __full_version__
    }
    if __prerelease__:
        info["prerelease"] = __prerelease__
    return info
