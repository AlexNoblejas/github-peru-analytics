import os
import sys

# Test basic imports to ensure requirements are loaded correctly
try:
    import pandas as pd
    import streamlit as st
    import openai
    import langchain
    import tenacity
    print("Environment is correctly configured.")
except Exception as e:
    print(f"Environment error: {e}")

# Check local files footprint
print("\nProject Structure Check:")
for root, dirs, files in os.walk("."):
    # Skip noisy directories
    if ".git" in root or "__pycache__" in root or "venv" in root or ".envs" in root:
        continue
    level = root.replace(".", "").count(os.sep)
    indent = " " * 4 * (level)
    print(f"{indent}{os.path.basename(root)}/")
    subindent = " " * 4 * (level + 1)
    for f in files:
        if not f.endswith('.pyc'):
            print(f"{subindent}{f}")
