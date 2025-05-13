from verificador_site_oficial import VerificadorSiteOficial

# Inicializar o verificador
verificador = VerificadorSiteOficial()

# Lista de órgãos para testar
orgaos_teste = [
    {"nome": "Prefeitura de Manaus", "url": "Manaus"},
    {"nome": "Secretaria de Fazenda do Amazonas", "url": "SEFAZ"},
    {"nome": "Câmara Municipal de Manaus", "url": "Camara Municipal de Manaus"}
]

# Testar cada órgão
for orgao in orgaos_teste:
    print(f"\nVerificando: {orgao['nome']}")
    resultado = verificador.verificar_site_oficial(orgao["url"], orgao["nome"])
    
    print(f"Status: {resultado['status']}")
    print(f"Observações: {resultado['observacoes']}")
    
    if resultado['evidencias']:
        print(f"Evidências: {resultado['evidencias']}")