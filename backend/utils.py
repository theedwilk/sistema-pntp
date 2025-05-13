# utils.py
import json
import os

def save_criteria_json():
    """
    Cria um arquivo JSON com os critérios de avaliação.
    Retorna os dados dos critérios.
    """
    criteria_data = [
        {
            "id": "1.1",
            "name": "Possui sítio oficial próprio na internet?",
            "items": ["disponibilidade"],
            "evidence": "",
            "classification": "Essencial",
            "legal_basis": "Art. 48, §1º, II, da LC nº 101/00 e arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "1.2",
            "name": "Possui portal da transparência próprio ou compartilhado na internet?",
            "items": ["disponibilidade"],
            "evidence": "",
            "classification": "Essencial",
            "legal_basis": "Art. 48, §1º, II, da LC nº 101/00 e arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "1.3",
            "name": "O acesso ao portal transparência está visível na capa do site?",
            "items": ["disponibilidade"],
            "evidence": "",
            "classification": "Obrigatória",
            "legal_basis": "Art. 8º, caput, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "1.4",
            "name": "O site e o portal de transparência contêm ferramenta de pesquisa de conteúdo que permita o acesso à informação?",
            "items": ["disponibilidade"],
            "evidence": "",
            "classification": "Obrigatória",
            "legal_basis": "Art. 8º, § 3º, I, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "2.1",
            "name": "Divulga a sua estrutura organizacional?",
            "items": ["disponibilidade"],
            "evidence": "",
            "classification": "Obrigatória",
            "legal_basis": "Art. 8º, § 3º, I, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "2.2",
            "name": "Divulga competências e/ou atribuições?",
            "items": ["disponibilidade"],
            "evidence": "",
            "classification": "Obrigatória",
            "legal_basis": "Art. 8º, § 1º, I, da Lei nº 12.527/2011 - LAI e art. 6º, VI, b, da Lei 13.460/2017."
        },
        {
            "id": "2.3",
            "name": "Identifica o nome dos atuais responsáveis pela gestão do Poder/Órgão?",
            "items": ["disponibilidade"],
            "evidence": "",
            "classification": "Obrigatória",
            "legal_basis": "Art. 8º, § 3º, I, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "3.1",
            "name": "Divulga as receitas do Poder ou órgão, evidenciando sua previsão e realização?",
            "items": ["disponibilidade", "atualidade", "serie_historica", "gravacao_relatorios", "filtro_pesquisa"],
            "evidence": "",
            "classification": "Obrigatória",
            "legal_basis": "Art. 48-A, II, da LC nº 101/00."
        },
        {
            "id": "4.1",
            "name": "Divulga o total das despesas empenhadas, liquidadas e pagas?",
            "items": ["disponibilidade", "atualidade", "serie_historica", "gravacao_relatorios", "filtro_pesquisa"],
            "evidence": "",
            "classification": "Obrigatória",
            "legal_basis": "Art. 48-A, I, da LC nº 101/00."
        },
        {
            "id": "11.5",
            "name": "Divulga o Relatório de Gestão Fiscal (RGF)?",
            "items": ["disponibilidade", "atualidade"],
            "evidence": "",
            "classification": "Obrigatória",
            "legal_basis": "Arts. 54 e 55 da LC nº 101/00."
        }
    ]
    
    # Salvar em arquivo
    os.makedirs('data', exist_ok=True)
    with open('data/criteria.json', 'w', encoding='utf-8') as f:
        json.dump(criteria_data, f, ensure_ascii=False, indent=2)
    
    return criteria_data