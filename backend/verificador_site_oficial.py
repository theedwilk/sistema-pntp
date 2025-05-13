# verificador_site_oficial.py
import requests
from bs4 import BeautifulSoup
import re
import time

class VerificadorSiteOficial:
    """Classe para verificar sites oficiais de órgãos públicos."""
    
    def __init__(self):
        """Inicializa o verificador de sites oficiais."""
        # Padrões para identificar sites oficiais
        self.padroes_dominio = [
            r'\.gov\.br$',
            r'\.leg\.br$',
            r'\.jus\.br$',
            r'\.mp\.br$',
            r'\.edu\.br$',
            r'\.org\.br$'  # Alguns órgãos usam .org.br
        ]
        
        # Palavras-chave que indicam sites oficiais
        self.palavras_chave = [
            'prefeitura', 'município', 'municipal', 'câmara', 
            'assembleia', 'governo', 'secretaria', 'tribunal',
            'ministério', 'autarquia', 'fundação', 'instituto'
        ]
    
    def verificar_site_oficial(self, url, nome_orgao):
        """
        Verifica se um site é o site oficial de um órgão público.
        
        Args:
            url (str): URL do site a verificar
            nome_orgao (str): Nome do órgão
            
        Returns:
            dict: Resultado da verificação
        """
        resultado = {
            "status": "Não Atende",
            "observacoes": "",
            "evidencias": []
        }
        
        # Verificar se a URL está vazia
        if not url:
            resultado["observacoes"] = "URL não fornecida."
            return resultado
        
        # Adicionar protocolo se não existir
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        # Verificar se o site está acessível
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                resultado["observacoes"] = f"Site não acessível. Código de status: {response.status_code}"
                return resultado
        except Exception as e:
            resultado["observacoes"] = f"Erro ao acessar o site: {str(e)}"
            return resultado
        
        # Verificar domínio
        dominio_oficial = False
        for padrao in self.padroes_dominio:
            if re.search(padrao, url, re.IGNORECASE):
                dominio_oficial = True
                resultado["evidencias"].append(f"Domínio oficial: {url}")
                break
        
        if not dominio_oficial:
            resultado["observacoes"] = "O site não possui um domínio oficial (.gov.br, .leg.br, etc.)"
            return resultado
        
        # Analisar conteúdo da página
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Verificar título e conteúdo
        titulo = soup.title.string if soup.title else ""
        conteudo = soup.get_text()
        
        # Verificar se o nome do órgão aparece no título ou conteúdo
        nome_orgao_lower = nome_orgao.lower()
        nome_encontrado = False
        
        if nome_orgao_lower in titulo.lower():
            nome_encontrado = True
            resultado["evidencias"].append(f"Nome do órgão encontrado no título: {titulo}")
        
        # Verificar palavras-chave relacionadas a sites oficiais
        palavras_encontradas = []
        for palavra in self.palavras_chave:
            if palavra in conteudo.lower():
                palavras_encontradas.append(palavra)
        
        if palavras_encontradas:
            resultado["evidencias"].append(f"Palavras-chave encontradas: {', '.join(palavras_encontradas)}")
        
        # Verificar elementos comuns em sites oficiais
        elementos_oficiais = {
            "Brasão/Logo": soup.find('img', {'alt': re.compile('(brasão|logo|símbolo)', re.IGNORECASE)}) is not None,
            "Menu de Acesso": soup.find('nav') is not None or soup.find('menu') is not None,
            "Rodapé com Informações": soup.find('footer') is not None,
            "Acesso à Informação": "acesso à informação" in conteudo.lower() or "e-sic" in conteudo.lower(),
            "Transparência": "transparência" in conteudo.lower() or "portal da transparência" in conteudo.lower()
        }
        
        elementos_encontrados = [k for k, v in elementos_oficiais.items() if v]
        if elementos_encontrados:
            resultado["evidencias"].append(f"Elementos de site oficial encontrados: {', '.join(elementos_encontrados)}")
        
        # Determinar status final
        if dominio_oficial and (nome_encontrado or len(palavras_encontradas) >= 2) and len(elementos_encontrados) >= 3:
            resultado["status"] = "Atende"
            resultado["observacoes"] = f"Site verificado e confirmado como oficial de {nome_orgao}."
        else:
            resultado["observacoes"] = "O site não apresenta características suficientes de um site oficial."
        
        return resultado