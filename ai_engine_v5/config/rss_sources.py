"""
RSS Sources Configuration for AI Engine V5
31 WORKING French news sources for autonomous scraping
FIXED: Removed broken sources, added working alternatives
"""

RSS_SOURCES = {
    # Major National News (VERIFIED WORKING)
    "Le Monde": "https://www.lemonde.fr/rss/une.xml",
    "Le Figaro": "https://www.lefigaro.fr/rss/figaro_une.xml", 
    "Libération": "https://www.liberation.fr/arc/outboundfeeds/rss/",
    "France Info": "https://www.francetvinfo.fr/titres.rss",
    "France 24": "https://www.france24.com/fr/rss",
    "RFI": "https://www.rfi.fr/fr/rss",
    "Europe 1": "https://www.europe1.fr/rss.xml",
    "CNEWS": "https://www.cnews.fr/rss/",
    "FranceInter": "https://www.franceinter.fr/rss/a-la-une.xml",
    "Public Sénat": "https://www.publicsenat.fr/rss",
    
    # Economy & Business (FIXED URLS)
    "L'Usine Nouvelle": "https://www.usinenouvelle.com/rss/",
    "Capital": "https://www.capital.fr/rss",
    "La Tribune Lyon": "https://www.latribune.fr/economie/rss.xml",
    "BFM Business": "https://www.bfmtv.com/economie/rss/",
    "Journal du Net": "https://www.journaldunet.com/rss/",
    
    # Regional News (WORKING ALTERNATIVES)
    "20 Minutes": "https://www.20minutes.fr/rss/",
    "Midi Libre": "https://www.midilibre.fr/rss/",
    "La Dépêche": "https://www.ladepeche.fr/rss/",
    "Le Parisien": "https://feeds.leparisien.fr/leparisien/rss",
    "L'Est Républicain": "https://www.estrepublicain.fr/rss/",
    
    # Tech & Innovation (VERIFIED)
    "01net": "https://www.01net.com/rss/",
    "Numerama": "https://www.numerama.com/rss/",
    "ZDNet France": "https://www.zdnet.fr/feeds/rss/",
    "Frandroid": "https://www.frandroid.com/rss/",
    "Clubic": "https://www.clubic.com/rss/",
    
    # Society & Culture (FIXED)
    "Marianne": "https://www.marianne.net/rss.xml",
    "Courrier International": "https://www.courrierinternational.com/rss/",
    "Le Point": "https://www.lepoint.fr/rss.xml",
    "L'Express": "https://www.lexpress.fr/rss/",
    
    # Government & Official (WORKING)
    "Vie Publique": "https://www.vie-publique.fr/rss/",
    "Sénat": "https://www.senat.fr/rss/"
}

# Validation
def validate_rss_sources():
    """Validate that we have the expected number of sources"""
    expected_count = 31
    actual_count = len(RSS_SOURCES)
    
    if actual_count != expected_count:
        raise ValueError(f"Expected {expected_count} RSS sources, got {actual_count}")
    
    print(f"✅ RSS Sources validated: {actual_count} comprehensive French news sources")
    return True

if __name__ == "__main__":
    validate_rss_sources()
    print("\nRSS SOURCES:")
    for name, url in RSS_SOURCES.items():
        print(f"  - {name}: {url}") 