#!/usr/bin/env python3
"""
Auto Cache-Busting Script
Automatically updates version timestamps in HTML files to force fresh content loading.
"""

import os
import re
from datetime import datetime
import pathlib

def update_cache_busting_timestamps(website_dir="ai_engine_v4/website"):
    """Update all cache-busting timestamps in website files."""
    
    # Generate new timestamp
    timestamp = int(datetime.now().timestamp())
    print(f"🔄 Updating cache-busting timestamps to: {timestamp}")
    
    # Update HTML files
    html_files = pathlib.Path(website_dir).glob("*.html")
    
    for html_file in html_files:
        print(f"   📝 Updating {html_file.name}...")
        
        content = html_file.read_text(encoding='utf-8')
        
        # Replace timestamp placeholders
        updated_content = content.replace('TIMESTAMP_PLACEHOLDER', str(timestamp))
        
        # Also update any existing timestamps in URLs
        updated_content = re.sub(
            r'(\.(css|js)\?v=)\d+(&cb=[^"]*)?', 
            rf'\g<1>{timestamp}\g<3>', 
            updated_content
        )
        
        html_file.write_text(updated_content, encoding='utf-8')
        print(f"   ✅ Updated {html_file.name}")
    
    print(f"🎉 Cache-busting update complete! New timestamp: {timestamp}")
    print("   🚀 Website will now force-load fresh content on every visit!")

if __name__ == "__main__":
    update_cache_busting_timestamps() 