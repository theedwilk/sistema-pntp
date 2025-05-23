# amazonas_portals.py
import pandas as pd
import os
from unidecode import unidecode

class AmazonasPortals:
    def __init__(self):
        self.data = None
        self.load_data()
        
    def normalize(self, text):
        """Remove acentuação e converte para minúsculas."""
        if text is None or pd.isna(text):
            return ""
        return unidecode(str(text)).strip().lower()
        
    def load_data(self):
        """Carrega os dados da planilha de portais do Amazonas."""
        try:
            # Tenta carregar o arquivo da planilha
            # Ajuste o caminho conforme necessário
            file_path = os.path.join(os.path.dirname(__file__), 'data', 'orgaos_amazonas.xlsx')
            
            if not os.path.exists(file_path):
                print(f"Arquivo não encontrado: {file_path}")
                self.data = pd.DataFrame()
                return
                
            # Carrega a planilha
            self.data = pd.read_excel(file_path)
            
            # Renomeia as colunas para facilitar o acesso
            if 'portais_da_transparencia_dos_orgaos_do_estado_do_amazonas' in self.data.columns:
                self.data.rename(columns={
                    'portais_da_transparencia_dos_orgaos_do_estado_do_amazonas': 'nome_municipio',
                    'empty_2': 'site_oficial',
                    'empty_3': 'site_camara',
                    'empty_4': 'poder_executivo',
                    'empty_5': 'url_site_oficial',
                    'empty_6': 'portal_transparencia'
                }, inplace=True)
            
            # Remove linhas com nome_municipio vazio
            self.data = self.data.dropna(subset=['nome_municipio'])
            
            # Normaliza os nomes para facilitar a busca
            if 'nome_municipio' in self.data.columns:
                self.data['nome_municipio_norm'] = self.data['nome_municipio'].apply(self.normalize)
            
            print(f"Dados carregados com sucesso: {len(self.data)} registros")
            
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            self.data = pd.DataFrame()
    
    def get_url(self, orgao, tipo='site_oficial'):
        """
        Obtém a URL para um órgão específico.
        
        Args:
            orgao (str): Nome do órgão ou município
            tipo (str): Tipo de URL ('site_oficial', 'site_camara', 'portal_transparencia')
            
        Returns:
            str or None: URL se encontrada, None caso contrário
        """
        if self.data is None or self.data.empty:
            return None
            
        # Normaliza o nome do órgão para comparação
        orgao_norm = self.normalize(orgao)
        
        # Remove prefixos comuns para melhorar a correspondência
        search_term = orgao_norm
        for prefix in ['prefeitura de ', 'prefeitura municipal de ', 'camara municipal de ', 'camara de ']:
            if search_term.startswith(prefix):
                search_term = search_term[len(prefix):]
                break
        
        # Primeiro, tenta encontrar correspondência exata
        for idx, row in self.data.iterrows():
            if 'nome_municipio_norm' in row and row['nome_municipio_norm'] == search_term:
                # Mapeia o tipo para a coluna correspondente
                col_map = {
                    'site_oficial': 'site_oficial',
                    'site_camara': 'site_camara',
                    'portal_transparencia': 'portal_transparencia'
                }
                
                col = col_map.get(tipo)
                if col and col in row:
                    url = row[col]
                    # Verifica se é uma URL válida
                    if isinstance(url, str) and url.strip() and not url.startswith('('):
                        # Se for um placeholder como "(A ser determinado)", retorna None
                        if '(a ser determinado)' in url.lower():
                            return None
                        # Adiciona https:// se não tiver
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        return url
                
                # Se não encontrou na coluna específica, tenta outras colunas relevantes
                if tipo == 'site_oficial' and 'url_site_oficial' in row:
                    url = row['url_site_oficial']
                    if isinstance(url, str) and url.strip() and not url.startswith('('):
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        return url
                
                if tipo == 'portal_transparencia' and 'portal_transparencia' in row:
                    url = row['portal_transparencia']
                    if isinstance(url, str) and url.strip():
                        # Extrai a URL de dentro de parênteses se necessário
                        if url.startswith('(') and url.endswith(')'):
                            url = url[1:-1]
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        return url
        
        # Se não encontrou correspondência exata, tenta correspondência parcial
        for idx, row in self.data.iterrows():
            if 'nome_municipio_norm' in row and (search_term in row['nome_municipio_norm'] or row['nome_municipio_norm'] in search_term):
                # Mesma lógica de extração de URL que acima
                col_map = {
                    'site_oficial': 'site_oficial',
                    'site_camara': 'site_camara',
                    'portal_transparencia': 'portal_transparencia'
                }
                
                col = col_map.get(tipo)
                if col and col in row:
                    url = row[col]
                    if isinstance(url, str) and url.strip() and not url.startswith('('):
                        if '(a ser determinado)' in url.lower():
                            return None
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        return url
                
                if tipo == 'site_oficial' and 'url_site_oficial' in row:
                    url = row['url_site_oficial']
                    if isinstance(url, str) and url.strip() and not url.startswith('('):
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        return url
                
                if tipo == 'portal_transparencia' and 'portal_transparencia' in row:
                    url = row['portal_transparencia']
                    if isinstance(url, str) and url.strip():
                        if url.startswith('(') and url.endswith(')'):
                            url = url[1:-1]
                        if not url.startswith(('http://', 'https://')):
                            url = 'https://' + url
                        return url
        
        # Se não encontrou nada, retorna None
        return None
    
    def get_all_municipalities(self):
        """Retorna a lista de todos os municípios na planilha."""
        if self.data is None or self.data.empty or 'nome_municipio' not in self.data.columns:
            return []
        
        # Filtra apenas linhas que parecem ser municípios (não cabeçalhos ou linhas vazias)
        municipios = []
        for nome in self.data['nome_municipio']:
            if isinstance(nome, str) and nome.strip() and nome != 'Nome_Município':
                municipios.append(nome)
        
        return municipios

# Instância global para uso em outros módulos
amazonas_portals = AmazonasPortals()

# Função de utilidade para obter URL
def get_amazonas_url(orgao, tipo='site_oficial'):
    """
    Obtém a URL para um órgão do Amazonas.
    
    Args:
        orgao (str): Nome do órgão ou município
        tipo (str): Tipo de URL ('site_oficial', 'site_camara', 'portal_transparencia')
        
    Returns:
        str or None: URL se encontrada, None caso contrário
    """
    return amazonas_portals.get_url(orgao, tipo)

# Função para obter todos os municípios
def get_all_amazonas_municipalities():
    """Retorna a lista de todos os municípios do Amazonas na planilha."""
    return amazonas_portals.get_all_municipalities()

# Exemplo de uso
if __name__ == "__main__":
    # Teste para alguns municípios
    test_municipalities = [
        "Manaus",
        "Parintins",
        "Itacoatiara",
        "Prefeitura de Manaus",
        "Câmara Municipal de Manaus"
    ]
    
    for municipio in test_municipalities:
        site = get_amazonas_url(municipio, 'site_oficial')
        portal = get_amazonas_url(municipio, 'portal_transparencia')
        camara = get_amazonas_url(municipio, 'site_camara')
        
        print(f"\n{municipio}:")
        print(f"  Site Oficial: {site}")
        print(f"  Portal Transparência: {portal}")
        print(f"  Site Câmara: {camara}")
    
    # Listar todos os municípios
    print("\nTodos os municípios:")
    for i, municipio in enumerate(get_all_amazonas_municipalities(), 1):
        if i <= 10:  # Limitar a exibição aos 10 primeiros
            print(f"  {i}. {municipio}")
        elif i == 11:
            print(f"  ... e mais {len(get_all_amazonas_municipalities()) - 10} municípios")