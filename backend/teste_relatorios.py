from gerador_relatorios import GeradorRelatorios
import json

# Criar alguns resultados de exemplo para teste
resultados_exemplo = [
    {
        "id": "1.1",
        "pergunta": "Possui sítio oficial próprio na internet?",
        "classificacao": "Essencial",
        "fundamentacao": "Art. 48, §1º, II, da LC nº 101/00 e arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011 – LAI.",
        "atende": True,
        "disponibilidade": True,
        "atualidade": "Não se Aplica",
        "serieHistorica": "Não se Aplica",
        "gravacaoRelatorios": "Não se Aplica",
        "filtroPesquisa": "Não se Aplica",
        "linkEvidencia": "https://www.manaus.am.gov.br/",
        "observacao": "Site oficial verificado e funcionando."
    },
    {
        "id": "1.2",
        "pergunta": "Possui portal da transparência próprio ou compartilhado na internet?",
        "classificacao": "Essencial",
        "fundamentacao": "Art. 48, §1º, II, da LC nº 101/00 e arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011 – LAI.",
        "atende": True,
        "disponibilidade": True,
        "atualidade": True,
        "serieHistorica": False,
        "gravacaoRelatorios": True,
        "filtroPesquisa": True,
        "linkEvidencia": "https://transparencia.manaus.am.gov.br/",
        "observacao": "Portal de transparência encontrado e funcionando."
    }
]

# Testar a geração de relatórios
def testar_geracao_relatorios():
    orgao = "Prefeitura de Manaus"
    gerador = GeradorRelatorios()
    
    print(f"Gerando relatórios para {orgao}...")
    
    # Gerar relatórios em todos os formatos
    caminhos = gerador.gerar_todos_formatos(resultados_exemplo, orgao)
    
    print("\nRelatórios gerados:")
    for formato, caminho in caminhos.items():
        print(f"- {formato.upper()}: {caminho}")
    
    return caminhos

if __name__ == "__main__":
    caminhos = testar_geracao_relatorios()
    
    # Ler o relatório JSON para verificar
    with open(caminhos['json'], 'r', encoding='utf-8') as f:
        dados = json.load(f)
        print("\nConteúdo do relatório JSON:")
        print(json.dumps(dados, ensure_ascii=False, indent=2))