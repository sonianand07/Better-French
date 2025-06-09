#!/usr/bin/env python3
"""
API Configuration for Better French Max - Automated System
Contains API keys and external service configurations
"""

import os
import sys

# ⚠️ SECURITY NOTE: This file contains sensitive API keys
# - Never commit this file to public repositories
# - Secure file permissions appropriately
# - Consider using environment variables in production

# 🔑 OPENROUTER API CONFIGURATION
# Load API key from environment variable if available, otherwise use the hardcoded key for demo purposes
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

if OPENROUTER_API_KEY == "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":
    print("⚠️ WARNING: Using hardcoded demo API key. For production, please set the OPENROUTER_API_KEY environment variable.")

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"

# 🤖 AI MODEL CONFIGURATION
# Using proven models from the manual system
PRIMARY_MODEL = "anthropic/claude-3.5-sonnet"  # Primary model for AI processing
FALLBACK_MODEL = "nousresearch/nous-hermes-2-mixtral-8x7b-dpo"  # Fallback if primary fails

# 📊 API LIMITS AND SETTINGS
API_CONFIG = {
    'openrouter': {
        'api_key': OPENROUTER_API_KEY,
        'base_url': OPENROUTER_API_BASE,
        'primary_model': PRIMARY_MODEL,
        'fallback_model': FALLBACK_MODEL,
        'timeout': 30,
        'max_retries': 3,
        'retry_delay': 5,
        'rate_limit_delay': 2.0,
        'max_tokens': 1000,
        'temperature': 0.3,
        'top_p': 0.9
    }
}

# 🌐 HTTP HEADERS FOR API REQUESTS
DEFAULT_HEADERS = {
    'User-Agent': 'Better-French-Max-Automated-System/1.0',
    'Content-Type': 'application/json',
    'HTTP-Referer': 'https://better-french-max.com',
    'X-Title': 'Better French Max - Automated AI Processing'
}

def setup_environment_variables():
    """Set up environment variables for API access"""
    os.environ['OPENROUTER_API_KEY'] = OPENROUTER_API_KEY
    print("✅ OpenRouter API key configured in environment")

def validate_api_configuration():
    """Validate API configuration"""
    issues = []
    
    # Check API key format
    if not OPENROUTER_API_KEY or "your_openrouter_api_key_here" in OPENROUTER_API_KEY:
        issues.append("❌ OpenRouter API key not properly configured. Please set the OPENROUTER_API_KEY environment variable.")
    elif not OPENROUTER_API_KEY.startswith("sk-or-v1-"):
        issues.append("⚠️ OpenRouter API key format seems incorrect")
    else:
        issues.append("✅ OpenRouter API key properly configured")
    
    # Check model configuration
    if PRIMARY_MODEL and FALLBACK_MODEL:
        issues.append("✅ Primary and fallback models configured")
    else:
        issues.append("⚠️ Model configuration incomplete")
    
    # Check base URL
    if OPENROUTER_API_BASE == "https://openrouter.ai/api/v1":
        issues.append("✅ OpenRouter API base URL configured")
    else:
        issues.append("⚠️ API base URL may be incorrect")
    
    return issues

def get_api_headers(additional_headers=None):
    """Get complete headers for API requests"""
    headers = DEFAULT_HEADERS.copy()
    if additional_headers:
        headers.update(additional_headers)
    return headers

# Set up environment variables when module is imported
setup_environment_variables()

# 🧪 TESTING CONFIGURATION
def test_api_configuration():
    """Test API configuration for development"""
    print("🧪 Testing API Configuration...")
    print("=" * 40)
    
    validation_results = validate_api_configuration()
    for result in validation_results:
        print(f"  {result}")
    
    print(f"📊 Configuration Summary:")
    print(f"  API Key: {'Set' if OPENROUTER_API_KEY and len(OPENROUTER_API_KEY) > 10 else 'Missing'}")
    print(f"  Primary Model: {PRIMARY_MODEL}")
    print(f"  Fallback Model: {FALLBACK_MODEL}")
    print(f"  Environment Variable: {'Set' if os.getenv('OPENROUTER_API_KEY') else 'Not Set'}")
    
    return all("✅" in result for result in validation_results)

if __name__ == "__main__":
    # Run tests when executed directly
    test_success = test_api_configuration()
    if test_success:
        print("\n🎉 API configuration is ready for use!")
    else:
        print("\n❌ API configuration has issues - please review")
        sys.exit(1) 