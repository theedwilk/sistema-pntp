# known_urls.py (versão atualizada)
from amazonas_portals import get_amazonas_url

# Dicionário de URLs conhecidas para órgãos importantes
KNOWN_URLS = {
    "Tribunal de Contas do Estado do Amazonas": {
        "site_oficial": "https://www.tce.am.gov.br/",
        "portal_transparencia": "https://transparencia.tce.am.gov.br/"
    },
    "TCE-AM": {
        "site_oficial": "https://www.tce.am.gov.br/",
        "portal_transparencia": "https://transparencia.tce.am.gov.br/"
    },
    "Governo do Estado do Amazonas": {
        "site_oficial": "https://www.am.gov.br/",
        "portal_transparencia": "http://www.transparencia.am.gov.br/"
    },
    "Assembleia Legislativa do Estado do Amazonas": {
        "site_oficial": "https://www.aleam.gov.br/",
        "portal_transparencia": "https://www.aleam.gov.br/transparencia/"
    },
    "Tribunal de Justiça do Amazonas": {
        "site_oficial": "https://www.tjam.jus.br/",
        "portal_transparencia": "https://www.tjam.jus.br/index.php/transparencia"
    },
    "Ministério Público do Estado do Amazonas": {
        "site_oficial": "https://www.mpam.mp.br/",
        "portal_transparencia": "https://www.mpam.mp.br/transparencia"
    },
    "Defensoria Pública do Estado do Amazonas": {
        "site_oficial": "https://defensoria.am.def.br/",
        "portal_transparencia": "https://defensoria.am.def.br/portal-da-transparencia/"
    },
    "Prefeitura de Manaus": {
        "site_oficial": "https://www.manaus.am.gov.br/",
        "portal_transparencia": "https://transparencia.manaus.am.gov.br/"
    }
}

def get_known_url(orgao, tipo="site_oficial"):
    """
    Retorna a URL conhecida para um órgão específico.
    
    Args:
        orgao (str): Nome do órgão
        tipo (str): Tipo de URL (site_oficial ou portal_transparencia)
        
    Returns:
        str or None: URL se conhecida, None caso contrário
    """
    # Normalizar o nome do órgão para comparação
    orgao_norm = orgao.lower().strip()
    
    # 1. Primeiro, verificar no dicionário de URLs conhecidas
    # Verificar correspondências exatas
    for nome, urls in KNOWN_URLS.items():
        if orgao_norm == nome.lower():
            return urls.get(tipo)
    
    # Verificar correspondências parciais
    for nome, urls in KNOWN_URLS.items():
        if orgao_norm in nome.lower() or nome.lower() in orgao_norm:
            return urls.get(tipo)
    
    # 2. Se não encontrou no dicionário, tentar na planilha
    url_from_sheet = get_amazonas_url(orgao, tipo)
    if url_from_sheet:
        return url_from_sheet
    
    # 3. Se for uma câmara municipal, tentar buscar o site da câmara
    if "câmara" in orgao_norm or "camara" in orgao_norm:
        return get_amazonas_url(orgao, 'site_camara')
    
    # Não encontrou em nenhuma fonte
    return None