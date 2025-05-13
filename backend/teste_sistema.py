# teste_sistema.py - Com órgãos alternativos
from verificador_transparencia import VerificadorTransparencia
import json
import time

def testar_sistema():
    # Configurar o verificador
    verificador = VerificadorTransparencia(headless=False)
    
    try:
        # Lista de órgãos alternativos para testar
        # Escolha um ou mais destes órgãos para testar
        orgaos = [
            # Municípios menores do Amazonas
            "Prefeitura de Parintins",
            "Prefeitura de Itacoatiara",
            "Prefeitura de Tefé",
            
            # Órgãos estaduais específicos
            "Secretaria de Educação do Amazonas",
            "Tribunal de Justiça do Amazonas",
            "Assembleia Legislativa do Amazonas",
            
            # Órgãos federais no Amazonas
            "INSS Amazonas",
            "Receita Federal Amazonas",
            
            # Autarquias e fundações
            "FAPEAM",  # Fundação de Amparo à Pesquisa do Estado do Amazonas
            "IPAAM"    # Instituto de Proteção Ambiental do Amazonas
        ]
        
        # Escolha apenas um órgão para testar inicialmente
        orgaos_para_teste = [orgaos[1]]  # Testando apenas Prefeitura de Itacoatiara
        
        resultados = {}
        
        for orgao in orgaos_para_teste:
            print(f"\nAvaliando: {orgao}")
            resultado = verificador.avaliar_orgao(orgao)
            resultados[orgao] = resultado
            
            # Exibir resumo
            print(f"\nResumo da avaliação para {orgao}:")
            print(f"Site Oficial: {resultado['site_oficial']['status']}")
            print(f"URL: {resultado['site_oficial']['url']}")
            print(f"Portal da Transparência: {resultado['portal_transparencia']['status']}")
            print(f"URL: {resultado['portal_transparencia']['url']}")
            
            # Exibir resultados detalhados
            for item in resultado['resultados']:
                print(f"\n{item['id']} - {item['pergunta']}")
                print(f"Atende: {'Sim' if item['atende'] else 'Não'}")
                print(f"Observação: {item['observacao']}")
            
            # Esperar entre órgãos para evitar bloqueio
            if len(orgaos_para_teste) > 1:
                print("\nEsperando 30 segundos antes do próximo órgão...")
                time.sleep(30)
        
        # Salvar resultados em JSON
        with open("resultados_avaliacao.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
        
        print("\nAvaliação concluída! Resultados salvos em 'resultados_avaliacao.json'")
    
    finally:
        # Garantir que o driver do Selenium seja fechado
        verificador.fechar()

if __name__ == "__main__":
    testar_sistema()