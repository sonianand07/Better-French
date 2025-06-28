#!/usr/bin/env python3
"""
Auto-update cache-busting timestamps for V3 and V4 websites.

This script updates the cache-busting query parameters in both websites
to force browsers to reload fresh content.
"""

import re
import time
import pathlib

def update_cache_busting(engine_path):
    """Update cache-busting timestamp for a specific engine."""
    index_path = pathlib.Path(f'{engine_path}/website/index.html')
    
    if not index_path.exists():
        print(f"   ❌ No index.html found for {engine_path}")
        return False
    
    # Generate new timestamp
    timestamp = str(int(time.time() * 1000))
    
    # Read current content
    content = index_path.read_text('utf-8')
    
    # Update cache-busting parameters in fetch calls
    # Pattern: fetch('file.ext?v=1234567890&cache=1234567890')
    content = re.sub(
        r'(\?v=\d+&cache=)\d+',
        f'\\g<1>{timestamp}',
        content
    )
    
    # Also update any standalone ?v= parameters
    content = re.sub(
        r'(\?v=)\d+',
        f'\\g<1>{timestamp}',
        content
    )
    
    # Write back
    index_path.write_text(content, 'utf-8')
    print(f"   ✅ Updated {engine_path}/website/index.html")
    return True

def main():
    """Update cache-busting for all engines."""
    timestamp = str(int(time.time() * 1000))
    
    print(f"🔄 Updating cache-busting timestamps to: {timestamp}")
    
    # Update V3
    print("   📝 Updating V3...")
    v3_updated = update_cache_busting('ai_engine_v3')
    
    # Update V4  
    print("   📝 Updating V4...")
    v4_updated = update_cache_busting('ai_engine_v4')
    
    if v3_updated or v4_updated:
        print(f"🎉 Cache-busting update complete! New timestamp: {timestamp}")
        print("   🚀 Website will now force-load fresh content on every visit!")
    else:
        print("❌ No index.html files were updated")

if __name__ == "__main__":
    main() 