#!/usr/bin/env python3
"""
Fix display_format inconsistencies in V4 articles.

This script standardizes all display_format fields to the pattern: **English:** _French_
which is what the JavaScript tooltip system expects.
"""

import json
import pathlib
import re

def fix_display_format(display_format, original_word):
    """
    Fix a display_format field to match the expected pattern: **English:** _French_
    """
    if not display_format:
        return f"**{original_word}:** _{original_word}_"
    
    # Already in correct format
    if re.match(r'\*\*[^:]+:\*\* _[^_]+_', display_format):
        return display_format
    
    # Extract English and French parts from various patterns
    patterns = [
        r'\*\*([^:*]+)\*\*:\s*([^*_]+)',  # **English**: French
        r'\*\*([^:*]+):\*\*\s*([^*_]+)',  # **English:** French
        r'\*\*([^:*]+)\*\*\s*([^*_]+)',   # **English** French
    ]
    
    for pattern in patterns:
        match = re.match(pattern, display_format)
        if match:
            english, french = match.groups()
            return f"**{english.strip()}:** _{french.strip()}_"
    
    # Try splitting on colon
    if ':' in display_format:
        clean = display_format.replace('*', '').replace('_', '')
        parts = clean.split(':', 1)
        if len(parts) == 2:
            english = parts[0].strip()
            french = parts[1].strip()
            return f"**{english}:** _{french}_"
    
    # Fallback
    return f"**Translation:** _{original_word}_"

def main():
    """Fix display_format fields in V4 articles."""
    
    pending_path = pathlib.Path('ai_engine_v4/data/live/pending_articles.json')
    if not pending_path.exists():
        print("❌ No pending articles file found")
        return
    
    data = json.loads(pending_path.read_text('utf-8'))
    articles = data.get('articles', data)
    
    fixed_count = 0
    
    for article in articles:
        explanations = article.get('contextual_title_explanations', {})
        for word, explanation in explanations.items():
            if 'display_format' in explanation:
                old_format = explanation['display_format']
                new_format = fix_display_format(old_format, word)
                
                if old_format != new_format:
                    explanation['display_format'] = new_format
                    fixed_count += 1
                    print(f"Fixed: '{old_format}' → '{new_format}'")
    
    # Save back
    pending_path.write_text(json.dumps({'articles': articles}, ensure_ascii=False, indent=2))
    
    # Also fix rolling articles
    rolling_path = pathlib.Path('ai_engine_v4/website/rolling_articles.json')
    if rolling_path.exists():
        rolling_data = json.loads(rolling_path.read_text('utf-8'))
        rolling_articles = rolling_data.get('articles', rolling_data)
        
        for article in rolling_articles:
            explanations = article.get('contextual_title_explanations', {})
            for word, explanation in explanations.items():
                if 'display_format' in explanation:
                    old_format = explanation['display_format']
                    new_format = fix_display_format(old_format, word)
                    
                    if old_format != new_format:
                        explanation['display_format'] = new_format
        
        rolling_path.write_text(json.dumps({'articles': rolling_articles}, ensure_ascii=False, indent=2))
    
    print(f"✅ Fixed {fixed_count} display_format fields")
    print("🎉 All tooltips should now display correctly!")

if __name__ == "__main__":
    main() 