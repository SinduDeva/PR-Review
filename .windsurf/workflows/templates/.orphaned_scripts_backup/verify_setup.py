#!/usr/bin/env python3
"""
Verify Python setup for PR Code Review Workflow
"""

import sys

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python version is compatible (3.8+)")
        return True
    else:
        print("❌ Python version too old. Need 3.8+")
        return False

def check_dependencies():
    """Check required dependencies"""
    print("\n" + "="*50)
    print("Checking Required Dependencies")
    print("="*50 + "\n")
    
    required = {
        'jinja2': 'Template rendering for HTML reports',
        'networkx': 'Dependency graph analysis',
        'bs4': 'HTML/XML parsing (beautifulsoup4)',
        'lxml': 'XML processing'
    }
    
    optional = {
        'pygraphviz': 'Advanced graph visualization'
    }
    
    all_ok = True
    
    # Check required packages
    for package, description in required.items():
        try:
            if package == 'bs4':
                __import__(package)
                print(f"✅ beautifulsoup4       - {description}")
            else:
                __import__(package)
                print(f"✅ {package:20} - {description}")
        except ImportError:
            print(f"❌ {package:20} - {description} - MISSING!")
            all_ok = False
    
    # Check optional packages
    print("\nOptional Packages:")
    for package, description in optional.items():
        try:
            __import__(package)
            print(f"✅ {package:20} - {description}")
        except ImportError:
            print(f"⚠️  {package:20} - {description} - Not installed (OK)")
    
    return all_ok

def main():
    """Main verification"""
    print("="*50)
    print("PR Code Review Workflow - Setup Verification")
    print("="*50 + "\n")
    
    # Check Python version
    version_ok = check_python_version()
    
    if not version_ok:
        print("\n❌ Python version incompatible")
        print("Please install Python 3.8 or higher")
        sys.exit(1)
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    print("\n" + "="*50)
    if deps_ok:
        print("🎉 All required dependencies installed!")
        print("="*50)
        print("\n✅ You can now run the PR Code Review workflow from Windsurf!")
        print("\nNext Steps:")
        print("  1. Copy workflow files to .windsurf/workflows/")
        print("  2. Checkout your feature branch")
        print("  3. Run workflow from Windsurf")
    else:
        print("❌ Some dependencies are missing")
        print("="*50)
        print("\nInstall missing dependencies with:")
        print("  py -m pip install jinja2 networkx beautifulsoup4 lxml")
        print("\nOr run: install_dependencies.bat")
        sys.exit(1)

if __name__ == '__main__':
    main()
