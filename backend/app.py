# app.py - Versão completa
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import scraper
import queue
import threading
import json
import time
import os
import pandas as pd
from datetime import datetime, timedelta, date
from utils import save_criteria_json
import requests
from bs4 import BeautifulSoup
from known_urls import get_known_url
from amazonas_portals import get_amazonas_url, get_all_amazonas_municipalities

# Configuração da aplicação
app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)  # Importante para permitir requisições do frontend React

# Caminho para o arquivo CSV
CSV_PATH = 'lista_criterios.csv'
df_transparencia = None

# Fila para armazenar resultados
resultados_queue = queue.Queue()
scraping_em_andamento = False
cancelamento_solicitado = False

# Carregar dados do CSV
def carregar_dados_csv():
    global df_transparencia
    try:
        if os.path.exists(CSV_PATH):
            df_transparencia = pd.read_csv(CSV_PATH, delimiter=';')
            print("Arquivo CSV carregado com sucesso.")
        else:
            print(f"Aviso: Arquivo CSV não encontrado em {CSV_PATH}. Será criado um arquivo vazio.")
            # Criar um DataFrame vazio com as colunas necessárias
            df_transparencia = pd.DataFrame(columns=['sigla_UG', 'ID_criterio', 'link'])
            # Salvar o DataFrame vazio como CSV
            df_transparencia.to_csv(CSV_PATH, sep=';', index=False)
    except Exception as e:
        df_transparencia = None
        print(f"ERRO CRÍTICO: Falha ao carregar o CSV. {e}")

# Carregar dados na inicialização
carregar_dados_csv()

# Load criteria on startup
criteria_data = save_criteria_json()

def normalizar_texto(texto):
    if texto is None:
        return ""
    return texto.strip().lower()

def obter_link_da_planilha(sigla_UG, ID_criterio):
    if df_transparencia is None:
        return None

    # Normaliza a sigla da UG
    ug_norm = sigla_UG.strip().lower()
    
    try:
        # Filtra pela coluna de sigla
        df_ug = df_transparencia[
            df_transparencia['sigla_UG'].str.strip().str.lower() == ug_norm
        ]
        if df_ug.empty:
            return None

        # Filtra pela coluna de ID_criterio
        df_crit = df_ug[df_ug['ID_criterio'].astype(str) == str(ID_criterio)]
        if df_crit.empty:
            return None

        link = df_crit.iloc[0]['link']
        if pd.isna(link) or not str(link).strip():
            return None

        return str(link).strip()
    except Exception as e:
        print(f"Erro ao obter link da planilha: {e}")
        return None

def verificar_disponibilidade_simples(url):
    """Verifica se uma URL está disponível, com timeout reduzido e tratamento de erros melhorado"""
    if not url: 
        return False
    try:
        # Reduzir o timeout para 8 segundos para evitar esperas longas
        response = requests.get(url, timeout=8, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        return response.status_code == 200
    except requests.Timeout:
        print(f"Timeout ao acessar {url}")
        return False
    except requests.ConnectionError:
        print(f"Erro de conexão ao acessar {url}")
        return False
    except requests.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return False

@app.route('/api/avaliar_criterio', methods=['POST'])
def avaliar_criterio_endpoint():
    dados_requisicao = request.get_json()
    unidade_gestora = dados_requisicao.get('unidade_gestora')
    criterio_descricao = dados_requisicao.get('criterio_descricao')
    criterio_id = dados_requisicao.get('criterio_id') 

    if not unidade_gestora or not criterio_id:
        return jsonify({"erro": "Nome da Unidade Gestora e ID do Critério são obrigatórios."}), 400

    # Primeiro, verificar se temos o link na planilha
    link_consultado = obter_link_da_planilha(unidade_gestora, criterio_id)
    
    # Se não temos o link na planilha, tentar URL conhecida
    if not link_consultado:
        print(f"Link não encontrado na planilha para {unidade_gestora}, critério {criterio_id}")
        
        # Tentar obter da configuração
        if criterio_id == "1.1":  # Site oficial
            link_consultado = get_known_url(unidade_gestora, "site_oficial")
        elif criterio_id == "1.2":  # Portal de transparência
            link_consultado = get_known_url(unidade_gestora, "portal_transparencia")
        
        # Se ainda não encontrou, tentar busca
        if not link_consultado:
            if criterio_id == "1.1":
                query = f"{unidade_gestora} site oficial"
            elif criterio_id == "1.2":
                query = f"{unidade_gestora} portal transparência"
            else:
                query = f"{criterio_descricao} {unidade_gestora}"
                
            # Verificar cache primeiro
            cached_results = scraper.get_cached_results(query)
            if cached_results and cached_results[0]:
                link_consultado = cached_results[0]
            else:
                # Se não estiver em cache, fazer busca
                links = scraper.buscar_no_google(query, 3)
                if links:
                    link_consultado = links[0]

    resultados_verificacao = {}
    # Defina quais itens de verificação são aplicáveis para cada critério.
    itens_aplicaveis = []
    if criterio_id == "1.1": # "Possui sitio oficial proprio na internet?"
        itens_aplicaveis = ["disponibilidade"]
    elif criterio_id == "1.2": # "Possui portal da transparência próprio ou compartilhado na internet?"
        itens_aplicaveis = ["disponibilidade"]
    elif criterio_id == "1.3": # "O acesso ao portal transparência está visível na capa do site?"
        itens_aplicaveis = ["disponibilidade"]
    elif criterio_id == "1.4": # "O site e o portal de transparência contêm ferramenta de pesquisa de conteúdo que permita o acesso à informação?"
        itens_aplicaveis = ["disponibilidade"]
    elif criterio_id in ["3.1", "3.2", "4.1", "4.2"]:
        itens_aplicaveis = ["disponibilidade", "atualidade", "serie_historica", "gravacao_relatorios", "filtro_pesquisa"]
    elif criterio_id == "11.5":
        itens_aplicaveis = ["disponibilidade", "atualidade"]
    else:
        itens_aplicaveis = ["disponibilidade"]  # Default para outros critérios

    if not itens_aplicaveis:
        print(f"Alerta: Nenhum item de verificação mapeado para o critério ID {criterio_id}.")

    if link_consultado:
        evidencia_texto = f"Evidência: {link_consultado}"

        # Verificar disponibilidade
        if "disponibilidade" in itens_aplicaveis:
            # Tratamento especial para o TCE-AM
            if 'tce.am.gov.br' in link_consultado.lower():
                if criterio_id in ["1.1", "1.2"]:
                    resultados_verificacao["disponibilidade"] = "Atendido"
                else:
                    # Para outros critérios, usar URL alternativa
                    alt_url = "https://transparencia.tce.am.gov.br/"
                    resultados_verificacao["disponibilidade"] = "Atendido" if verificar_disponibilidade_simples(alt_url) else "Não Atendido"
            else:
                # Verificação normal para outros sites
                resultados_verificacao["disponibilidade"] = "Atendido" if verificar_disponibilidade_simples(link_consultado) else "Não Atendido"

        # Verificar outros critérios
        if "atualidade" in itens_aplicaveis:
            try:
                response = requests.get(link_consultado, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if criterio_id == "3.1":
                    resultados_verificacao["atualidade"] = "Atendido" if scraper.check_atualidade(soup) else "Não Atendido"
                elif criterio_id == "3.2":
                    resultados_verificacao["atualidade"] = "Atendido" if scraper.check_recency(soup) else "Não Atendido"
                elif criterio_id == "4.1":
                    resultados_verificacao["atualidade"] = "Atendido" if scraper.check_atualidade(soup) else "Não Atendido"
                elif criterio_id == "4.2":
                    resultados_verificacao["atualidade"] = "Atendido" if scraper.check_atualidade(soup) else "Não Atendido"
                elif criterio_id == "11.5":
                    hoje = datetime.now().date()
                    quadr, ano_quad = scraper.ultimo_quadrimestre_exigivel(hoje)
                    resultados_verificacao["atualidade"] = "Atendido" if scraper.pagina_tem_atualidade(link_consultado, quadr) else "Não Atendido"
                else:
                    resultados_verificacao["atualidade"] = "Não Atendido (verificação não implementada)"
            except Exception as e:
                print(f"Erro ao verificar atualidade: {e}")
                resultados_verificacao["atualidade"] = "Não Atendido (erro na verificação)"
        
        # Verificar série histórica
        if "serie_historica" in itens_aplicaveis:
            try:
                response = requests.get(link_consultado, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if criterio_id in ["3.1", "3.2", "4.1", "4.2"]:
                    resultados_verificacao["serie_historica"] = "Atendido" if scraper.check_serie_historica(soup) else "Não Atendido"
                else:
                    resultados_verificacao["serie_historica"] = "Não Atendido (verificação não implementada)"
            except Exception as e:
                print(f"Erro ao verificar série histórica: {e}")
                resultados_verificacao["serie_historica"] = "Não Atendido (erro na verificação)"
        
        # Verificar gravação de relatórios
        if "gravacao_relatorios" in itens_aplicaveis:
            try:
                response = requests.get(link_consultado, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if criterio_id in ["3.1", "3.2", "4.1", "4.2"]:
                    resultados_verificacao["gravacao_relatorios"] = "Atendido" if scraper.check_gravacao_relatorios(soup) else "Não Atendido"
                else:
                    resultados_verificacao["gravacao_relatorios"] = "Não Atendido (verificação não implementada)"
            except Exception as e:
                print(f"Erro ao verificar gravação de relatórios: {e}")
                resultados_verificacao["gravacao_relatorios"] = "Não Atendido (erro na verificação)"
        
        # Verificar filtro de pesquisa
        if "filtro_pesquisa" in itens_aplicaveis:
            try:
                response = requests.get(link_consultado, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if criterio_id in ["3.1", "3.2", "4.1", "4.2"]:
                    resultados_verificacao["filtro_pesquisa"] = "Atendido" if scraper.check_filtro_pesquisa(soup) else "Não Atendido"
                else:
                    resultados_verificacao["filtro_pesquisa"] = "Não Atendido (verificação não implementada)"
            except Exception as e:
                print(f"Erro ao verificar filtro de pesquisa: {e}")
                resultados_verificacao["filtro_pesquisa"] = "Não Atendido (erro na verificação)"

    else: # Nenhum link encontrado
        evidencia_texto = "Evidência: não há página contendo a divulgação exigida pelo critério"
        for item in itens_aplicaveis:
            resultados_verificacao[item] = "Não Atendido"

    return jsonify({
        "resultados_verificacao": resultados_verificacao,
        "evidencia": evidencia_texto
    })

@app.route('/api/criteria')
def get_criteria():
    return jsonify(criteria_data)

@app.route('/api/cancelar-avaliacao', methods=['POST'])
def cancelar_avaliacao():
    """Cancela uma avaliação em andamento"""
    global scraping_em_andamento, cancelamento_solicitado
    
    if not scraping_em_andamento:
        return jsonify({"error": "Não há avaliação em andamento para cancelar"}), 400
    
    # Marcar para cancelamento
    cancelamento_solicitado = True
    
    return jsonify({"message": "Solicitação de cancelamento recebida"})

@app.route('/api/avaliar-transparencia', methods=['POST'])
def avaliar_transparencia():
    """Inicia o processo de avaliação em uma thread separada"""
    global scraping_em_andamento, cancelamento_solicitado
    
    if scraping_em_andamento:
        return jsonify({"error": "Já existe uma avaliação em andamento"}), 400
    
    data = request.json
    orgao = data.get('orgao')
    tipo_orgao = data.get('tipo_orgao', 'todos')  # Novo parâmetro para tipo de órgão
    
    if not orgao:
        return jsonify({"error": "O nome do órgão é obrigatório"}), 400
    
    # Limpa a fila de resultados anteriores
    while not resultados_queue.empty():
        resultados_queue.get()
    
    # Resetar flag de cancelamento
    cancelamento_solicitado = False
    
    # Obtém o total de perguntas para cálculo de progresso
    perguntas = scraper.obter_perguntas_padrao()
    
    # Adiciona perguntas específicas com base no tipo de órgão
    if tipo_orgao == 'executivo':
        perguntas.extend(scraper.obter_perguntas_especificas('executivo'))
        perguntas.extend(scraper.obter_perguntas_especificas('executivo-consorcios'))
    elif tipo_orgao == 'legislativo':
        perguntas.extend(scraper.obter_perguntas_especificas('legislativo'))
    elif tipo_orgao == 'judiciario':
        perguntas.extend(scraper.obter_perguntas_especificas('judiciario'))
    elif tipo_orgao == 'tribunal-contas':
        perguntas.extend(scraper.obter_perguntas_especificas('tribunal-contas'))
    elif tipo_orgao == 'ministerio-publico':
        perguntas.extend(scraper.obter_perguntas_especificas('ministerio-publico'))
    elif tipo_orgao == 'defensoria':
        perguntas.extend(scraper.obter_perguntas_especificas('defensoria'))
    elif tipo_orgao == 'consorcio':
        perguntas.extend(scraper.obter_perguntas_especificas('consorcios'))
    elif tipo_orgao == 'estatal':
        perguntas.extend(scraper.obter_perguntas_especificas('estatais'))
    elif tipo_orgao == 'estatal-independente':
        perguntas.extend(scraper.obter_perguntas_especificas('estatais'))
        perguntas.extend(scraper.obter_perguntas_especificas('estatais-independentes'))
    
    total_perguntas = len(perguntas)
    
    # Inicia o scraping em uma thread separada
    scraping_em_andamento = True
    threading.Thread(target=executar_scraping, args=(orgao, perguntas)).start()
    
    return jsonify({
        "message": "Avaliação iniciada com sucesso",
        "totalPerguntas": total_perguntas
    })

def executar_scraping(orgao, perguntas):
    """Executa o scraping e coloca os resultados na fila"""
    global scraping_em_andamento, cancelamento_solicitado
    
    try:
        # Obtém o total de perguntas
        total_perguntas = len(perguntas)
        
        # Envia mensagem de status: iniciando busca
        resultados_queue.put({
            "type": "status",
            "message": "Buscando site oficial...",
            "progress": 5
        })
        
        # Busca o site oficial
        site_oficial = None
        
        # 1. Primeiro, tentar URL conhecida do dicionário ou da planilha
        site_oficial = get_known_url(orgao, "site_oficial")
        if site_oficial:
            print(f"Usando URL conhecida para {orgao}: {site_oficial}")
        
        # 2. Se não encontrou em URLs conhecidas, tentar URLs diretas
        if not site_oficial:
            orgao_simplificado = scraper.normalize(orgao.lower().replace("prefeitura de ", "").replace("câmara municipal de ", ""))
            dominios_diretos = [
                f"https://www.{orgao_simplificado}.am.gov.br",
                f"https://{orgao_simplificado}.am.gov.br",
                f"https://www.prefeitura{orgao_simplificado}.am.gov.br",
                f"https://prefeitura{orgao_simplificado}.am.gov.br"
            ]
            
            for url in dominios_diretos:
                try:
                    if verificar_disponibilidade_simples(url):
                        site_oficial = url
                        break
                except:
                    continue
        
        # 3. Se não encontrou diretamente, buscar no cache
        if not site_oficial:
            query = f"{orgao} site oficial"
            cached_results = scraper.get_cached_results(query)
            if cached_results and cached_results[0]:
                site_oficial = cached_results[0]
        
        # 4. Por último, fazer busca na web
        if not site_oficial:
            links_site = scraper.buscar_no_google(f"{orgao} site oficial", 3)
            if links_site:
                site_oficial = links_site[0]
        
        # Verificar cancelamento
        if cancelamento_solicitado:
            resultados_queue.put({
                "type": "status",
                "message": "Avaliação cancelada pelo usuário",
                "progress": 100
            })
            return
        
        if site_oficial:
            resultados_queue.put({
                "type": "status",
                "message": f"Site oficial encontrado: {site_oficial}",
                "progress": 10
            })
        else:
            resultados_queue.put({
                "type": "status",
                "message": "Site oficial não encontrado",
                "progress": 10
            })
        
        # Busca o portal de transparência
        resultados_queue.put({
            "type": "status",
            "message": "Buscando portal de transparência...",
            "progress": 15
        })
        
        portal_transparencia = None
        
        # 1. Primeiro, tentar URL conhecida do dicionário ou da planilha
        portal_transparencia = get_known_url(orgao, "portal_transparencia")
        if portal_transparencia:
            print(f"Usando URL conhecida para portal de transparência de {orgao}: {portal_transparencia}")
        
        # 2. Se não encontrou em URLs conhecidas, tentar encontrar no site oficial
        if not portal_transparencia and site_oficial:
            try:
                links_transparencia = scraper.find_transparency_links(site_oficial)
                if links_transparencia:
                    portal_transparencia = links_transparencia[0]['url']
            except Exception as e:
                print(f"Erro ao buscar links de transparência no site oficial: {e}")
        
        # 3. Se não encontrou no site oficial, tentar URLs diretas
        if not portal_transparencia:
            orgao_simplificado = scraper.normalize(orgao.lower().replace("prefeitura de ", "").replace("câmara municipal de ", ""))
            dominios_transparencia = [
                f"https://transparencia.{orgao_simplificado}.am.gov.br",
                f"https://{orgao_simplificado}.am.gov.br/transparencia",
                f"https://www.{orgao_simplificado}.am.gov.br/transparencia",
                f"https://transparencia.{orgao_simplificado}.leg.br"
            ]
            
            for url in dominios_transparencia:
                try:
                    if verificar_disponibilidade_simples(url):
                        portal_transparencia = url
                        break
                except:
                    continue
        
        # 4. Se ainda não encontrou, buscar no cache
        if not portal_transparencia:
            query = f"{orgao} portal transparência"
            cached_results = scraper.get_cached_results(query)
            if cached_results and cached_results[0]:
                portal_transparencia = cached_results[0]
        
        # 5. Por último, fazer busca na web
        if not portal_transparencia:
            links_portal = scraper.buscar_no_google(f"{orgao} portal transparência", 3)
            if links_portal:
                portal_transparencia = links_portal[0]
        
        # Verificar cancelamento
        if cancelamento_solicitado:
            resultados_queue.put({
                "type": "status",
                "message": "Avaliação cancelada pelo usuário",
                "progress": 100
            })
            return
        
        if portal_transparencia:
            resultados_queue.put({
                "type": "status",
                "message": f"Portal de transparência encontrado: {portal_transparencia}",
                "progress": 20
            })
        else:
            resultados_queue.put({
                "type": "status",
                "message": "Portal de transparência não encontrado",
                "progress": 20
            })
        
        # Processa cada pergunta individualmente
        for i, item in enumerate(perguntas):
            # Verificar cancelamento
            if cancelamento_solicitado:
                resultados_queue.put({
                    "type": "status",
                    "message": "Avaliação cancelada pelo usuário",
                    "progress": 100
                })
                break
                
            pergunta = item["pergunta"]
            
            # Envia mensagem de status: verificando pergunta atual
            resultados_queue.put({
                "type": "status",
                "message": f"Verificando item {i+1} de {total_perguntas}",
                "progress": 20 + ((i / total_perguntas) * 80),
                "perguntaAtual": pergunta
            })
            
            # Determinar qual URL usar para verificação
            url_verificacao = None
            if "sítio oficial" in pergunta.lower() and site_oficial:
                url_verificacao = site_oficial
            elif "portal da transparência" in pergunta.lower() and portal_transparencia:
                url_verificacao = portal_transparencia
            elif portal_transparencia:  # Para outras perguntas, verificar primeiro no portal de transparência
                url_verificacao = portal_transparencia
            elif site_oficial:  # Se não tiver portal, verificar no site oficial
                url_verificacao = site_oficial
            
            # Se não temos uma URL específica, buscar no cache ou na web
            if not url_verificacao:
                query = f"{pergunta} {orgao}"
                cached_results = scraper.get_cached_results(query)
                if cached_results and cached_results[0]:
                    url_verificacao = cached_results[0]
                else:
                    links = scraper.buscar_no_google(query, 3)
                    if links:
                        url_verificacao = links[0]
            
            # Verificar o item
            resultado = None
            if url_verificacao:
                # Tratamento especial para o TCE-AM
                if 'tce.am.gov.br' in url_verificacao.lower():
                    # Para o TCE-AM, usamos URLs conhecidas em vez de tentar acessar diretamente
                    if "sítio oficial" in pergunta.lower():
                        disponibilidade = True
                    elif "portal da transparência" in pergunta.lower():
                        disponibilidade = True
                    else:
                        # Para outras perguntas, usamos a URL do portal de transparência
                        url_verificacao = "https://transparencia.tce.am.gov.br/"
                        disponibilidade = verificar_disponibilidade_simples(url_verificacao)
                else:
                    disponibilidade = scraper.verificar_item(url_verificacao, pergunta)
                
                resultado = {
                    "id": item["id"],
                    "pergunta": pergunta,
                    "dimensao": item["dimensao"],
                    "fundamentacao": item["fundamentacao"],
                    "classificacao": item["classificacao"],
                    "disponibilidade": disponibilidade,
                    "atualidade": True if item["id"] in ["1.1", "1.2", "1.3", "1.4"] else None,
                    "serieHistorica": None,
                    "gravacaoRelatorios": None,
                    "filtroPesquisa": None,
                    "linkEvidencia": url_verificacao if disponibilidade else None,
                    "observacao": None if disponibilidade else f"Informação não encontrada para {orgao} em {url_verificacao}"
                }
            else:
                resultado = {
                    "id": item["id"],
                    "pergunta": pergunta,
                    "dimensao": item["dimensao"],
                    "fundamentacao": item["fundamentacao"],
                    "classificacao": item["classificacao"],
                    "disponibilidade": False,
                    "atualidade": None,
                    "serieHistorica": None,
                    "gravacaoRelatorios": None,
                    "filtroPesquisa": None,
                    "linkEvidencia": None,
                    "observacao": f"Não foi possível encontrar informações para {orgao}"
                }
            
            # Adiciona o resultado à fila para streaming
            resultados_queue.put(resultado)
            
            # Pequena pausa para não sobrecarregar o cliente
            time.sleep(0.1)
        
        # Envia mensagem de conclusão
        resultados_queue.put({
            "type": "status",
            "message": "Avaliação concluída!",
            "progress": 100
        })
        
    except Exception as e:
        # Registrar erro
        print(f"Erro durante o scraping: {e}")
        # Enviar mensagem de erro para o cliente
        resultados_queue.put({
            "type": "error",
            "message": f"Ocorreu um erro durante a avaliação: {str(e)}",
            "progress": 100
        })
    finally:
        # Resetar flags
        cancelamento_solicitado = False
        scraping_em_andamento = False
        
        # Envia evento de conclusão
        resultados_queue.put({
            "type": "complete"
        })

@app.route('/api/stream-resultados')
def stream_resultados():
    """Endpoint SSE para streaming de resultados"""
    def generate():
        while True:
            # Se não há mais scraping e a fila está vazia, termina o streaming
            if not scraping_em_andamento and resultados_queue.empty():
                yield f"event: complete\ndata: {{}}\n\n"
                break
            
            # Tenta obter um resultado da fila
            try:
                resultado = resultados_queue.get(block=False)
                
                # Se for uma mensagem de status
                if isinstance(resultado, dict) and resultado.get("type") == "status":
                    yield f"data: {json.dumps(resultado)}\n\n"
                # Se for uma mensagem de erro
                elif isinstance(resultado, dict) and resultado.get("type") == "error":
                    yield f"event: error\ndata: {json.dumps(resultado)}\n\n"
                # Se for uma mensagem de conclusão
                elif isinstance(resultado, dict) and resultado.get("type") == "complete":
                    yield f"event: complete\ndata: {{}}\n\n"
                    break
                # Se for um resultado normal
                else:
                    yield f"data: {json.dumps(resultado)}\n\n"
                    
            except queue.Empty:
                # Se a fila está vazia mas o scraping ainda está em andamento, espera
                time.sleep(0.5)
                continue
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/municipios')
def get_municipios():
    """Retorna a lista de municípios do Amazonas"""
    try:
        municipios = get_all_amazonas_municipalities()
        return jsonify({
            "municipios": municipios,
            "total": len(municipios)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return jsonify({"message": "API do Sistema de Avaliação de Portais de Transparência"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)