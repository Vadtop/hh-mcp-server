"""
Wrapper script to launch HH MCP Server from the correct directory.
This ensures Python can find the 'src' package.
"""
import sys
import os

# Add the project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Change working directory to project root
os.chdir(project_root)

# Now import and run the main module
from src.main import mcp

if __name__ == "__main__":
    mcp.run()
