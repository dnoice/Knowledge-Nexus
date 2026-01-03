#!/usr/bin/env python3
"""
✒ Metadata
    - Title: Knowledge Nexus Launcher (Knowledge Nexus Edition - v1.0)
    - File Name: run.py
    - Relative Path: run.py
    - Artifact Type: script
    - Version: 1.0.0
    - Date: 2025-01-03
    - Update: Friday, January 03, 2025
    - Author: Dennis 'dnoice' Smaltz
    - A.I. Acknowledgement: Anthropic - Claude Opus 4.5
    - Signature: ︻デ═─── ✦ ✦ ✦ | Aim Twice, Shoot Once!

✒ Description:
    Quick-start script for the Knowledge Nexus application.
    Handles virtual environment setup and launches the FastAPI server.

✒ Key Features:
    - Feature 1: Automatic dependency installation
    - Feature 2: Development server with hot-reload
    - Feature 3: Production-ready configuration
    - Feature 4: Cross-platform support

✒ Usage Instructions:
    Development mode:
        python run.py

    Production mode:
        python run.py --prod

    With custom port:
        python run.py --port 8080
"""

import subprocess
import sys
import os
from pathlib import Path


def check_dependencies() -> bool:
    """Check if required packages are installed."""
    try:
        import uvicorn
        import fastapi
        import pydantic_settings
        import yaml
        import whoosh
        import networkx
        import markdown
        return True
    except ImportError:
        return False


def install_dependencies():
    """Install required packages from requirements.txt."""
    requirements_path = Path(__file__).parent / "requirements.txt"

    if not requirements_path.exists():
        print("Error: requirements.txt not found!")
        sys.exit(1)

    print("Installing dependencies from requirements.txt...")
    print("This may take a minute on first run...\n")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r",
            str(requirements_path)
        ])
        print("\nDependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\nError installing dependencies: {e}")
        print("Try running manually: pip install -r requirements.txt")
        sys.exit(1)


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Run the FastAPI server."""
    import uvicorn
    import sys
    import io

    # Handle Unicode output on Windows
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    mode_str = "Development" if reload else "Production"
    print(f"""
+============================================================+
|                                                            |
|     _  __ _   _  _____        ___     _____ ____   ____    |
|    | |/ /| \\ | |/ _ \\ \\      / / |   | ____|  _ \\ / ___|   |
|    | ' / |  \\| | | | \\ \\ /\\ / /| |   |  _| | | | | |  _    |
|    | . \\ | |\\  | |_| |\\ V  V / | |___| |___| |_| | |_| |   |
|    |_|\\_\\|_| \\_|\\___/  \\_/\\_/  |_____|_____|____/ \\____|   |
|                                                            |
|                      N E X U S                             |
|                                                            |
|             Aim Twice, Shoot Once!                         |
|                                                            |
+============================================================+
|  Server: http://{host}:{port:<5}                              |
|  Docs:   http://{host}:{port}/docs                            |
|  Mode:   {mode_str:<12}                              |
+============================================================+
    """)

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Nexus Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--prod", action="store_true", help="Production mode (no reload)")
    args = parser.parse_args()

    # Ensure we're in the project directory
    os.chdir(Path(__file__).parent)

    # Check and install dependencies if needed
    if not check_dependencies():
        install_dependencies()

    # Run the server
    run_server(
        host=args.host,
        port=args.port,
        reload=not args.prod
    )


if __name__ == "__main__":
    main()
