#!/usr/bin/env python3
"""
Demo: Contextual Learning Example
Shows how French word explanations work for the title:
"Boris Vallaud : « Je voterai pour Olivier Faure, mais ce n'est ni un chèque en blanc ni une ardoise magique »"
"""

import json
import sys
import os

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

def demo_contextual_learning():
    """Demonstrate what contextual learning would look like"""
    
    # Example title
    title = "Boris Vallaud : « Je voterai pour Olivier Faure, mais ce n'est ni un chèque en blanc ni une ardoise magique »"
    
    print("🎯 DEMO: Contextual French Learning")
    print("=" * 60)
    print(f"📰 Original Title: {title}")
    print()
    
    # This is what the AI would generate for contextual learning
    contextual_explanations = [
        {
            "original_word": "Je voterai",
            "display_format": "**Je voterai:** I will vote",
            "explanation": "Future tense of 'voter' (to vote). In French politics, public declarations of voting intentions are common. Simple future tense: je + verb stem + -ai ending",
            "cultural_note": "Public voting declarations are standard practice in French political discourse"
        },
        {
            "original_word": "chèque en blanc",
            "display_format": "**Chèque en blanc:** Blank check",
            "explanation": "Literal: 'blank check'. Figurative: unconditional support without conditions. Fixed expression - always 'chèque en blanc', never changes",
            "cultural_note": "French political expression meaning giving someone complete freedom to act"
        },
        {
            "original_word": "ardoise magique",
            "display_format": "**Ardoise magique:** Magic slate/Etch-a-Sketch",
            "explanation": "Literal: 'magic slate' (toy where you can erase and start over). Figurative: wiping the slate clean, starting fresh. Feminine noun: 'une ardoise magique'",
            "cultural_note": "French political metaphor for ignoring past mistakes or positions"
        },
        {
            "original_word": "ce n'est ni... ni...",
            "display_format": "**Ce n'est ni... ni...:** It is neither... nor...",
            "explanation": "Double negative construction meaning 'it is neither X nor Y'. Both parts must be included - common way to deny two things at once in French political discourse",
            "cultural_note": ""
        }
    ]
    
    print("🎓 CONTEXTUAL WORD EXPLANATIONS:")
    print("=" * 40)
    
    for exp in contextual_explanations:
        print(f"📝 {exp['display_format']}")
        print(f"   💡 Explanation: {exp['explanation']}")
        if exp.get('cultural_note'):
            print(f"   🇫🇷 Cultural Context: {exp['cultural_note']}")
        print()
    
    print("🌟 LEARNING EXPERIENCE:")
    print("=" * 30)
    print("On the website, each of these words/phrases would be:")
    print("• ✨ Highlighted in the title")
    print("• 🖱️  Interactive (hover/click to see explanation)")
    print("• 📱 Touch-friendly on mobile")
    print("• 🎯 Contextually relevant to French politics/culture")
    print()
    
    # Show what the simplified versions would look like
    print("📖 SIMPLIFIED VERSIONS:")
    print("=" * 25)
    print("🇫🇷 Simplified French: Boris Vallaud dit qu'il votera pour Olivier Faure, mais avec des conditions")
    print("🇺🇸 English Version: Boris Vallaud says he'll vote for Olivier Faure, but with conditions")
    print()
    
    print("💡 This transforms a complex French political statement into an interactive learning experience!")

if __name__ == "__main__":
    demo_contextual_learning() 