"""
Version information for dunebugger.

Version is read from a VERSION file.
Generate the VERSION file using ./generate_version.sh before running the application.
The version follows semantic versioning (MAJOR.MINOR.PATCH).
"""

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


# Load version from VERSION file
_version_info = _load_from_version_file()

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
