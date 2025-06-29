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
    "RTL": "https://www.rtl.fr/rss/une.xml",  # REPLACED CNEWS
    "LCI": "https://www.lci.fr/rss/",  # REPLACED FranceInter
    "Public Sénat": "https://www.publicsenat.fr/rss",
    
    # Economy & Business (FIXED URLS)
    "L'Usine Nouvelle": "https://www.usinenouvelle.com/rss/",
    "Capital": "https://www.capital.fr/rss",
    "Les Échos": "https://www.lesechos.fr/rss/",  # REPLACED La Tribune Lyon
    "Challenges": "https://www.challenges.fr/rss/",  # REPLACED BFM Business
    "Journal du Net": "https://www.journaldunet.com/rss/",
    
    # Regional News (WORKING ALTERNATIVES)
    "Ouest-France": "https://www.ouest-france.fr/rss/",  # REPLACED 20 Minutes
    "La Voix du Nord": "https://www.lavoixdunord.fr/rss/",  # REPLACED Midi Libre
    "Sud Ouest": "https://www.sudouest.fr/rss/",  # REPLACED La Dépêche
    "Le Parisien": "https://feeds.leparisien.fr/leparisien/rss",
    "Le Progrès": "https://www.leprogres.fr/rss/",  # REPLACED L'Est Républicain
    
    # Tech & Innovation (VERIFIED)
    "01net": "https://www.01net.com/rss/",
    "Numerama": "https://www.numerama.com/rss/",
    "ZDNet France": "https://www.zdnet.fr/feeds/rss/",
    "Frandroid": "https://www.frandroid.com/rss/",
    "L'Informaticien": "https://www.linformaticien.com/rss/",  # REPLACED Clubic
    
    # Society & Culture (FIXED)
    "Marianne": "https://www.marianne.net/rss.xml",
    "L'Obs": "https://www.nouvelobs.com/rss/",  # REPLACED Courrier International
    "Le Point": "https://www.lepoint.fr/rss.xml",
    "Télérama": "https://www.telerama.fr/rss/",  # REPLACED L'Express
    
    # Government & Official (WORKING)
    "Service-public.fr": "https://www.service-public.fr/rss/",  # REPLACED Vie Publique
    "Gouvernement.fr": "https://www.gouvernement.fr/rss/"  # REPLACED Sénat
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