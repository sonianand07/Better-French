#!/usr/bin/env python3
"""Check for accidentally exposed API keys in git commits.

This script prevents OpenRouter API keys from being committed to the repository.
"""
import re
import sys
import subprocess
from pathlib import Path

def check_staged_files():
    """Check staged files for API key patterns."""
    try:
        # Get list of staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], 
            capture_output=True, text=True, check=True
        )
        staged_files = result.stdout.strip().split('\n')
        
        if not staged_files or staged_files == ['']:
            return True
            
        # Check each staged file for API key patterns
        api_key_pattern = r'sk-or-v1-[a-f0-9]{64}'
        
        for file_path in staged_files:
            if not Path(file_path).exists():
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if re.search(api_key_pattern, content):
                    print(f"🚨 ERROR: API key detected in staged file: {file_path}")
                    print("❌ Commit blocked to prevent key exposure!")
                    print("\n💡 To fix:")
                    print("1. Remove the API key from the file")
                    print("2. Store it in GitHub Secrets instead")
                    print("3. Use environment variables in your code")
                    return False
                    
            except (UnicodeDecodeError, IOError):
                # Skip binary files or files we can't read
                continue
                
        return True
        
    except subprocess.CalledProcessError:
        # If git command fails, allow commit (git might not be initialized)
        return True

if __name__ == "__main__":
    if not check_staged_files():
        sys.exit(1)
    print("✅ No API keys detected in staged files") 