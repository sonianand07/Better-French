"""
RSS Sources Configuration for AI Engine V5
31 comprehensive French news sources for autonomous scraping
"""

RSS_SOURCES = {
    # Major National News
    "Le Monde": "https://www.lemonde.fr/rss/une.xml",
    "Le Figaro": "https://www.lefigaro.fr/rss/figaro_une.xml", 
    "Libération": "https://www.liberation.fr/arc/outboundfeeds/rss/",
    "France Info": "https://www.francetvinfo.fr/titres.rss",
    "BFM TV": "https://www.bfmtv.com/rss/",
    "France 24": "https://www.france24.com/fr/rss",
    "RFI": "https://www.rfi.fr/fr/rss",
    "LCI": "https://www.tf1info.fr/rss/",
    "Europe 1": "https://www.europe1.fr/rss.xml",
    "RTL": "https://www.rtl.fr/rss/",
    
    # Economy & Business
    "Les Échos": "https://www.lesechos.fr/rss.xml",
    "La Tribune": "https://www.latribune.fr/rss/",
    "L'Usine Nouvelle": "https://www.usinenouvelle.com/rss/",
    "Challenges": "https://www.challenges.fr/rss/",
    "Capital": "https://www.capital.fr/rss",
    
    # Regional News
    "Ouest-France": "https://www.ouest-france.fr/rss/",
    "La Voix du Nord": "https://www.lavoixdunord.fr/rss/",
    "Sud Ouest": "https://www.sudouest.fr/rss/",
    "Le Progrès": "https://www.leprogres.fr/rss/",
    "Nice-Matin": "https://www.nicematin.com/rss/",
    
    # Tech & Innovation
    "01net": "https://www.01net.com/rss/",
    "Numerama": "https://www.numerama.com/rss/",
    "ZDNet France": "https://www.zdnet.fr/feeds/rss/",
    "Frandroid": "https://www.frandroid.com/rss/",
    
    # Society & Culture
    "Marianne": "https://www.marianne.net/rss.xml",
    "L'Obs": "https://www.nouvelobs.com/rss/",
    "Télérama": "https://www.telerama.fr/rss/",
    "Rue89": "https://www.rue89lyon.fr/feed/",
    
    # Government & Official
    "Service-public.fr": "https://www.service-public.fr/rss/",
    "Vie Publique": "https://www.vie-publique.fr/rss/",
    "Gouvernement.fr": "https://www.gouvernement.fr/rss/"
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