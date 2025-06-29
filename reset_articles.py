#!/usr/bin/env python3
"""
URGENT FIX: Reset articles that were falsely marked as processed
by the failed V5 workflow run from 2025-06-29 18:14 UTC.

These 30 articles never got proper V3+V4 enhancement due to import errors,
but were marked as processed anyway. This script resets them.
"""

import json
from pathlib import Path
from datetime import datetime

def reset_falsely_processed_articles():
    """Reset the 30 articles that failed processing but were marked as processed."""
    
    print("🔧 RESETTING FALSELY PROCESSED ARTICLES")
    print("=" * 60)
    
    data_file = Path('ai_engine_v5/data/scraper_data.json')
    
    if not data_file.exists():
        print("❌ Data file not found!")
        return False
    
    # Load scraper data
    with open(data_file, 'r', encoding='utf-8') as f:
        scraper_data = json.load(f)
    
    # Target timestamps from the failed workflow (based on logs)
    # These are the runs that were processed around 2025-06-29 18:14 UTC
    target_timestamps = {
        "2025-06-29T18:57:53.946747",  # From the logs
        "2025-06-29T18:11:10.332718",  # From the logs (appears twice)
    }
    
    print(f"🎯 Target timestamps to reset: {target_timestamps}")
    
    reset_count = 0
    total_articles_reset = 0
    
    for run in scraper_data.get('scraper_runs', []):
        timestamp = run.get('timestamp', '')
        
        # Check if this run was in the failed batch
        # Also check recent runs from today that might have been marked processed
        if (timestamp in target_timestamps or 
            (timestamp.startswith('2025-06-29T18:') and 
             run.get('processed_by_website', False))):
            
            print(f"\n📅 Resetting run: {timestamp}")
            print(f"   📊 Articles: {run.get('articles_selected', 0)}")
            print(f"   🔄 Current status: processed_by_website = {run.get('processed_by_website', False)}")
            
            # Reset the processing flag
            run['processed_by_website'] = False
            reset_count += 1
            total_articles_reset += run.get('articles_selected', 0)
            
            print(f"   ✅ Reset to: processed_by_website = False")
            
            # Show some article titles being reset
            if 'selected_articles' in run and run['selected_articles']:
                print("   📰 Sample articles being reset:")
                for i, article in enumerate(run['selected_articles'][:3], 1):
                    title = article.get('title', 'No title')[:50] + '...'
                    print(f"      {i}. {title}")
                if len(run['selected_articles']) > 3:
                    remaining = len(run['selected_articles']) - 3
                    print(f"      ... and {remaining} more")
    
    print(f"\n✅ RESET SUMMARY:")
    print(f"   🔄 Runs reset: {reset_count}")
    print(f"   📄 Total articles available for processing: {total_articles_reset}")
    print(f"   🎯 These articles will now be processed in the next workflow run")
    
    # Save the updated data
    backup_file = data_file.with_suffix('.backup.json')
    print(f"\n💾 Creating backup: {backup_file}")
    
    # Create backup
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(scraper_data, f, indent=2, ensure_ascii=False)
    
    # Save updated data
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(scraper_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Updated data saved to: {data_file}")
    print(f"🔒 Backup created at: {backup_file}")
    
    return True

if __name__ == "__main__":
    success = reset_falsely_processed_articles()
    
    if success:
        print(f"\n🎉 ARTICLES SUCCESSFULLY RESET!")
        print(f"🚀 The next V5 workflow run will now process these articles properly")
        print(f"🎯 With the import fix, V3+V4 enhancement should work correctly")
    else:
        print(f"\n❌ Reset failed!") 