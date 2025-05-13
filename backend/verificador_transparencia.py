# verificador_transparencia.py - Versão modificada
from link_finder import LinkFinder
from verificador_site_oficial import VerificadorSiteOficial
from gerador_relatorios import GeradorRelatorios

class VerificadorTransparencia:
    def __init__(self, headless=True, use_undetected=False):
        self.link_finder = LinkFinder(headless=headless, use_undetected=use_undetected)
        # Não instanciamos o VerificadorSiteOficial aqui
        self.gerador_relatorios = GeradorRelatorios()
    
    # Resto do código permanece igual...    
    def avaliar_orgao(self, nome_orgao):
        """
        Avalia a transparência de um órgão.
        
        Args:
            nome_orgao (str): Nome do órgão a avaliar
            
        Returns:
            dict: Resultados da avaliação
        """
        print(f"\n=== Avaliando transparência para: {nome_orgao} ===\n")
        
        # 1. Buscar links do órgão
        resultado_site = self.link_finder.buscar_link(
            nome_orgao, 
            tipo_link='site_oficial', 
            tipo_busca='site oficial'
        )
        
        resultado_transparencia = self.link_finder.buscar_link(
            nome_orgao, 
            tipo_link='portal_transparencia', 
            tipo_busca='portal transparência'
        )
        
        # 2. Verificar site oficial
        if resultado_site["url"]:
            # Criar uma instância do VerificadorSiteOficial com os parâmetros necessários
            verificacao_site = VerificadorSiteOficial(resultado_site["url"], nome_orgao)
        else:
            verificacao_site = {
                "status": "Não Atende",
                "observacoes": "Site oficial não encontrado",
                "evidencias": []
            }
        
        # 3. Verificar portal da transparência
        # Implementar verificações específicas conforme critérios da cartilha
        
        # 4. Gerar relatório
        resultados = [
            {
                "id": "1.1",
                "pergunta": "Possui sítio oficial próprio na internet?",
                "classificacao": "Essencial",
                "fundamentacao": "Art. 48, §1º, II, da LC nº 101/00 e arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011 – LAI.",
                "atende": verificacao_site.get("status", "Não Atende") == "Atende" if isinstance(verificacao_site, dict) else False,
                "disponibilidade": verificacao_site.get("status", "Não Atende") == "Atende" if isinstance(verificacao_site, dict) else False,
                "atualidade": "Não se Aplica",
                "serieHistorica": "Não se Aplica",
                "gravacaoRelatorios": "Não se Aplica",
                "filtroPesquisa": "Não se Aplica",
                "linkEvidencia": resultado_site["url"] if resultado_site["url"] else "",
                "observacao": verificacao_site.get("observacoes", "") if isinstance(verificacao_site, dict) else ""
            },
            {
                "id": "1.2",
                "pergunta": "Possui portal da transparência próprio ou compartilhado na internet?",
                "classificacao": "Essencial",
                "fundamentacao": "Art. 48, §1º, II, da LC nº 101/00 e arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011 – LAI.",
                "atende": resultado_transparencia["url"] is not None,
                "disponibilidade": resultado_transparencia["url"] is not None,
                "atualidade": "Não Verificado",  # Implementar verificação específica
                "serieHistorica": "Não Verificado",  # Implementar verificação específica
                "gravacaoRelatorios": "Não Verificado",  # Implementar verificação específica
                "filtroPesquisa": "Não Verificado",  # Implementar verificação específica
                "linkEvidencia": resultado_transparencia["url"] if resultado_transparencia["url"] else "",
                "observacao": f"Portal de transparência {'encontrado' if resultado_transparencia['url'] else 'não encontrado'}"
            }
        ]
        
        # Gerar relatórios
        caminhos_relatorios = self.gerador_relatorios.gerar_todos_formatos(resultados, nome_orgao)
        
        return {
            "orgao": nome_orgao,
            "site_oficial": resultado_site,
            "portal_transparencia": resultado_transparencia,
            "verificacao_site": verificacao_site if isinstance(verificacao_site, dict) else {},
            "resultados": resultados,
            "relatorios": caminhos_relatorios
        }
    
    def fechar(self):
        """Fecha recursos abertos."""
        self.link_finder.fechar()