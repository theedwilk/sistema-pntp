import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, TipoOrgao, Orgao, TipoLink, Link

def importar_dados_planilha(caminho_planilha):
    # Configurar banco de dados
    engine = create_engine('sqlite:///transparencia.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Criar tipos de órgão
    tipos_orgao = {
        'municipio': TipoOrgao(nome='Município'),
        'poder_executivo': TipoOrgao(nome='Poder Executivo'),
        'poder_legislativo': TipoOrgao(nome='Poder Legislativo'),
        'poder_judiciario': TipoOrgao(nome='Poder Judiciário'),
        'tribunal_contas': TipoOrgao(nome='Tribunal de Contas'),
        'ministerio_publico': TipoOrgao(nome='Ministério Público'),
        'defensoria': TipoOrgao(nome='Defensoria Pública'),
        'autarquia': TipoOrgao(nome='Autarquia'),
        'estatal': TipoOrgao(nome='Estatal'),
        'secretaria': TipoOrgao(nome='Secretaria'),
        'fundacao': TipoOrgao(nome='Fundação')
    }
    
    for tipo in tipos_orgao.values():
        session.add(tipo)
    
    # Criar tipos de link
    tipos_link = {
        'site_oficial': TipoLink(nome='Site Oficial'),
        'site_camara': TipoLink(nome='Site Câmara'),
        'portal_transparencia': TipoLink(nome='Portal da Transparência')
    }
    
    for tipo in tipos_link.values():
        session.add(tipo)
    
    session.commit()
    
    # Ler a planilha
    df = pd.read_excel(caminho_planilha)
    
    # Processar municípios
    municipios_processados = set()
    
    for index, row in df.iterrows():
        if pd.notna(row.get('Nome_Município', None)) and row['Nome_Município'] not in municipios_processados:
            municipio = Orgao(
                nome=row['Nome_Município'],
                tipo_id=tipos_orgao['municipio'].id,
                uf='AM'
            )
            session.add(municipio)
            session.flush()  # Para obter o ID do município
            
            # Adicionar links do município
            if pd.notna(row.get('Site_Oficial', None)) and row['Site_Oficial'] != '(A ser determinado)':
                link_site = Link(
                    orgao_id=municipio.id,
                    tipo_id=tipos_link['site_oficial'].id,
                    url=row['Site_Oficial']
                )
                session.add(link_site)
            
            if pd.notna(row.get('Site_Camara', None)):
                link_camara = Link(
                    orgao_id=municipio.id,
                    tipo_id=tipos_link['site_camara'].id,
                    url=row['Site_Camara']
                )
                session.add(link_camara)
            
            municipios_processados.add(row['Nome_Município'])
    
    # Processar outros órgãos (Poderes, Secretarias, etc.)
    for index, row in df.iterrows():
        if pd.notna(row.get('Poder Executivo', None)) and row['Poder Executivo'] != '':
            tipo_key = 'poder_executivo'
            if 'Legislativo' in row['Poder Executivo']:
                tipo_key = 'poder_legislativo'
            elif 'Judiciário' in row['Poder Executivo']:
                tipo_key = 'poder_judiciario'
            elif 'Tribunal de Contas' in row['Poder Executivo']:
                tipo_key = 'tribunal_contas'
            elif 'Ministério Público' in row['Poder Executivo']:
                tipo_key = 'ministerio_publico'
            elif 'Defensoria' in row['Poder Executivo']:
                tipo_key = 'defensoria'
            elif 'Autarquias' in row['Poder Executivo']:
                tipo_key = 'autarquia'
            elif 'Estatais' in row['Poder Executivo']:
                tipo_key = 'estatal'
            elif 'Secretarias' in row['Poder Executivo']:
                tipo_key = 'secretaria'
            elif 'Fundações' in row['Poder Executivo']:
                tipo_key = 'fundacao'
            
            if pd.notna(row.get('URL do Site Oficial', None)):
                orgao = Orgao(
                    nome=row['Poder Executivo'],
                    tipo_id=tipos_orgao[tipo_key].id,
                    uf='AM'
                )
                session.add(orgao)
                session.flush()
                
                link_site = Link(
                    orgao_id=orgao.id,
                    tipo_id=tipos_link['site_oficial'].id,
                    url=row['URL do Site Oficial']
                )
                session.add(link_site)
                
                if pd.notna(row.get('Link do Portal da Transparência', None)):
                    link_transparencia = Link(
                        orgao_id=orgao.id,
                        tipo_id=tipos_link['portal_transparencia'].id,
                        url=row['Link do Portal da Transparência'].replace('(', '').replace(')', '')
                    )
                    session.add(link_transparencia)
    
    session.commit()
    print("Importação concluída com sucesso!")

if __name__ == "__main__":
    importar_dados_planilha("data/orgaos_amazonas.xlsx")