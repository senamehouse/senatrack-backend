#!/usr/bin/env python3
"""
Build script for creating Senatrack executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """Build the executable using PyInstaller"""
    
    print("Building Senatrack executable...")
    
    # Get the current directory
    current_dir = Path(__file__).parent
    app_dir = current_dir / "app"
    launcher_file = current_dir / "launcher.py"
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Don't show console window
        "--name", "SenatrackLauncher",
        "--icon", "icon.ico",  # Add icon if available
        "--add-data", f"{app_dir};app",  # Include the app directory
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "firebase_admin",
        "--hidden-import", "sqlite3",
        "--hidden-import", "tkinter",
        "--hidden-import", "requests",
        launcher_file
    ]
    
    # Remove icon parameter if icon file doesn't exist
    if not (current_dir / "icon.ico").exists():
        cmd = [arg for arg in cmd if arg != "--icon" and arg != "icon.ico"]
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, cwd=current_dir, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Executable created in: {current_dir / 'dist' / 'SenatrackLauncher.exe'}")
        
        # Create a simple installer script
        create_installer_script(current_dir)
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

def create_installer_script(build_dir):
    """Create a simple installer script"""
    
    installer_content = '''@echo off
echo Installing Senatrack Local Server...

REM Create installation directory
if not exist "%PROGRAMFILES%\\Senatrack" mkdir "%PROGRAMFILES%\\Senatrack"

REM Copy executable
copy "SenatrackLauncher.exe" "%PROGRAMFILES%\\Senatrack\\"

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\Senatrack Launcher.lnk'); $Shortcut.TargetPath = '%PROGRAMFILES%\\Senatrack\\SenatrackLauncher.exe'; $Shortcut.Save()"

echo Installation completed!
echo You can now run Senatrack from your desktop or Start menu.
pause
'''
    
    installer_file = build_dir / "install.bat"
    with open(installer_file, 'w') as f:
        f.write(installer_content)
    
    print(f"Installer script created: {installer_file}")

def create_portable_package(build_dir):
    """Create a portable package"""
    
    print("Creating portable package...")
    
    portable_dir = build_dir / "SenatrackPortable"
    portable_dir.mkdir(exist_ok=True)
    
    # Copy executable
    exe_file = build_dir / "dist" / "SenatrackLauncher.exe"
    if exe_file.exists():
        shutil.copy2(exe_file, portable_dir)
    
    # Create README
    readme_content = """# Senatrack Portable

This is a portable version of Senatrack Local Server.

## How to use:

1. Run SenatrackLauncher.exe
2. Click "Start Server" to start the local API server
3. Use the sync buttons to synchronize with online database
4. Share the local URL with other devices on your network

## Features:

- Local SQLite database for offline use
- Network sharing for team access
- Bidirectional sync with online Firestore database
- Easy-to-use GUI interface

## Requirements:

- Windows 10 or later
- Internet connection for sync operations
- Firewall may need to allow the application

## Support:

For support, visit: https://api.senatrack.app
"""
    
    readme_file = portable_dir / "README.txt"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    print(f"Portable package created in: {portable_dir}")

def main():
    """Main build function"""
    
    print("Senatrack Executable Builder")
    print("=" * 40)
    
    # Check if PyInstaller is installed
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build executable
    if build_executable():
        print("\nBuild completed successfully!")
        
        # Ask if user wants to create portable package
        response = input("\nCreate portable package? (y/n): ").lower().strip()
        if response == 'y':
            create_portable_package(Path(__file__).parent)
        
        print("\nYou can now distribute the executable or portable package!")
    else:
        print("\nBuild failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

