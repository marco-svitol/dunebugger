#!/usr/bin/env python3
"""
Example demonstrating version comparison logic for update checking.

This shows how to compare local version with GitHub releases without
relying on build numbers (which are not in the release tag).
"""

import sys
import json
sys.path.insert(0, 'app')

from update_checker import parse_semver


def demo_version_comparison():
    """Demonstrate version comparison logic."""
    
    print("=" * 70)
    print("DUNEBUGGER UPDATE CHECKER - Version Comparison Demo")
    print("=" * 70)
    print()
    
    # Simulate scenarios
    scenarios = [
        {
            "description": "New prerelease available",
            "local": {"version": "1.0.0", "prerelease": "beta.2", "build_number": 79},
            "remote": {"version": "1.0.0", "prerelease": "beta.3", "build_number": 0},
        },
        {
            "description": "Release available (upgrading from prerelease)",
            "local": {"version": "1.0.0", "prerelease": "beta.3", "build_number": 85},
            "remote": {"version": "1.0.0", "prerelease": None, "build_number": 0},
        },
        {
            "description": "Already on latest",
            "local": {"version": "1.0.0", "prerelease": "beta.3", "build_number": 85},
            "remote": {"version": "1.0.0", "prerelease": "beta.3", "build_number": 0},
        },
        {
            "description": "Local is newer (dev build ahead of release)",
            "local": {"version": "1.0.1", "prerelease": None, "build_number": 95},
            "remote": {"version": "1.0.0", "prerelease": None, "build_number": 0},
        },
        {
            "description": "Same version, different build (GitHub has VERSION.json)",
            "local": {"version": "1.0.0", "prerelease": "beta.3", "build_number": 85},
            "remote": {"version": "1.0.0", "prerelease": "beta.3", "build_number": 90},
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"Scenario {i}: {scenario['description']}")
        print("-" * 70)
        
        local = scenario['local']
        remote = scenario['remote']
        
        # Build semantic version strings
        def make_semver(info):
            if info.get('prerelease'):
                return f"{info['version']}-{info['prerelease']}"
            return info['version']
        
        local_semver = make_semver(local)
        remote_semver = make_semver(remote)
        
        print(f"  Local:  {local_semver:20} (build #{local['build_number']})")
        print(f"  Remote: {remote_semver:20} (build #{remote['build_number']})")
        
        # Compare
        local_parsed = parse_semver(local_semver)
        remote_parsed = parse_semver(remote_semver)
        
        if local_parsed < remote_parsed:
            print(f"  Result: ✅ UPDATE AVAILABLE - Remote is newer")
        elif local_parsed > remote_parsed:
            print(f"  Result: ⚠️  LOCAL IS NEWER - Remote is older")
        else:
            # Check build numbers if available
            if remote['build_number'] > 0 and local['build_number'] < remote['build_number']:
                print(f"  Result: ✅ UPDATE AVAILABLE - Same version, newer build")
            else:
                print(f"  Result: ✓ UP TO DATE - Versions match")
        
        print()
    
    print("=" * 70)
    print()
    print("KEY INSIGHTS:")
    print("-" * 70)
    print("1. Comparison is based on SEMANTIC VERSION only (not build number)")
    print("2. Build numbers are tracked locally for debugging/CI purposes")
    print("3. GitHub releases include VERSION.json with build_number starting")
    print("   from the next release (after you merge these changes)")
    print("4. Prerelease versions (beta.X) are always < release versions")
    print("5. If same semantic version, build numbers can break ties")
    print()


if __name__ == "__main__":
    demo_version_comparison()
