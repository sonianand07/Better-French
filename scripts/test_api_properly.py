#!/usr/bin/env python3
"""
Test OpenRouter API key properly with all required headers.
This helps avoid triggering security flags.
"""

import requests
import json
import time
import os

def test_api_key_properly(api_key):
    """Test API key with proper headers and reasonable delay."""
    
    print("🔑 Testing API key with proper identification...")
    time.sleep(2)  # Reasonable delay
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/sonianand07/Better-French",
            "X-Title": "Better French - Educational Platform",
            "Content-Type": "application/json",
            "User-Agent": "BetterFrench/1.0 (https://betterfrench.io)"
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": "Testing Better French integration"}],
            "max_tokens": 10
        }
    )
    
    if response.status_code == 200:
        print("✅ API key works properly!")
        print(f"Response: {response.json()['choices'][0]['message']['content']}")
        return True
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        return False

if __name__ == "__main__":
    api_key = os.getenv("OPENROUTER_API_KEY") or input("Enter API key: ")
    test_api_key_properly(api_key) 