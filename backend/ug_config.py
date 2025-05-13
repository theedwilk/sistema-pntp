# ug_config.py

def get_ug_link(ug, tipo="site_oficial"):
    """
    Retorna o link conhecido para uma UG específica.
    
    Args:
        ug (str): Sigla da unidade gestora
        tipo (str): Tipo de link (site_oficial ou portal_transparencia)
        
    Returns:
        str or None: URL se conhecida, None caso contrário
    """
    # Dicionário de links conhecidos
    links = {
        "tce": {
            "site_oficial": "https://www2.tce.am.gov.br/",
            "portal_transparencia": "https://transparencia.tce.am.gov.br/"
        },
        "sefaz": {
            "site_oficial": "https://www.sefaz.am.gov.br/",
            "portal_transparencia": "http://sistemas.sefaz.am.gov.br/transparencia/"
        }
        # Adicione mais UGs conforme necessário
    }
    
    ug = ug.lower()
    if ug in links and tipo in links[ug]:
        return links[ug][tipo]
    
    return None