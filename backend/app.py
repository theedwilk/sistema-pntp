# app.py
from flask import Flask, request, jsonify, Response, render_template, redirect, url_for, send_from_directory
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

# Configuração da aplicação
app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)  # Importante para permitir requisições do frontend React

# Caminho para o arquivo CSV
CSV_PATH = 'lista_criterios.csv'
df_transparencia = None

# Fila para armazenar resultados
resultados_queue = queue.Queue()
scraping_em_andamento = False

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
    if not url: return False
    try:
        response = scraper.requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        return response.status_code == 200
    except scraper.requests.RequestException:
        return False

@app.route('/api/avaliar_criterio', methods=['POST'])
def avaliar_criterio_endpoint():
    dados_requisicao = request.get_json()
    unidade_gestora = dados_requisicao.get('unidade_gestora')
    criterio_descricao = dados_requisicao.get('criterio_descricao')
    criterio_id = dados_requisicao.get('criterio_id') 

    if not unidade_gestora or not criterio_descricao:
        return jsonify({"erro": "Nome da Unidade Gestora e Descrição do Critério são obrigatórios."}), 400

    link_consultado = obter_link_da_planilha(unidade_gestora, criterio_id)

    resultados_verificacao = {}
    # Defina quais itens de verificação são aplicáveis para cada critério.
    itens_aplicaveis = []
    if criterio_id == "1.1": # "Possui sitio oficial proprio na internet?"
        itens_aplicaveis = ["disponibilidade"]
    elif criterio_id == "2.1": # Exemplo: "Divulga receita: ... (Previsão Inicial)"
        itens_aplicaveis = ["disponibilidade", "atualidade", "serie_historica", "gravacao_relatorios"] 
    # Adicione mais mapeamentos conforme a estrutura de seus critérios.

    if not itens_aplicaveis:
        print(f"Alerta: Nenhum item de verificação mapeado para o critério ID {criterio_id}.")

    if link_consultado:
        evidencia_texto = f"Evidência: {link_consultado}"

        # Aqui você chamará suas funções de verificação específicas.
        if "disponibilidade" in itens_aplicaveis:
            if criterio_id == "1.1":
                resultados_verificacao["disponibilidade"] = "Atendido" if verificar_disponibilidade_simples(link_consultado) else "Não Atendido"
            else:
                resultados_verificacao["disponibilidade"] = "Atendido (verificação de conteúdo pendente)" # Placeholder

        # Exemplo para outros itens (placeholders, substitua pela sua lógica)
        if "atualidade" in itens_aplicaveis:
            resultados_verificacao["atualidade"] = "Não Atendido (verificação pendente)"
        if "serie_historica" in itens_aplicaveis:
            resultados_verificacao["serie_historica"] = "Atendido (verificação pendente)"
        if "gravacao_relatorios" in itens_aplicaveis:
            resultados_verificacao["gravacao_relatorios"] = "Atendido (verificação pendente)"
        if "filtro_pesquisa" in itens_aplicaveis:
            resultados_verificacao["filtro_pesquisa"] = "Não Atendido (verificação pendente)"

    else: # Nenhum link encontrado na planilha
        evidencia_texto = "Evidência: não há página contendo a divulgação exigida pelo critério"
        for item in itens_aplicaveis:
            resultados_verificacao[item] = "Não Atendido"
        # Especificamente para o critério 1.1, se não há link, a disponibilidade é "Não Atendido"
        if "disponibilidade" in itens_aplicaveis and criterio_id == "1.1":
            resultados_verificacao["disponibilidade"] = "Não Atendido"

    return jsonify({
        "resultados_verificacao": resultados_verificacao,
        "evidencia": evidencia_texto
    })

@app.route('/api/criteria')
def get_criteria():
    return jsonify(criteria_data)

@app.route('/api/avaliar-transparencia', methods=['POST'])
def avaliar_transparencia():
    """Inicia o processo de avaliação em uma thread separada"""
    global scraping_em_andamento
    
    if scraping_em_andamento:
        return jsonify({"error": "Já existe uma avaliação em andamento"}), 400
    
    data = request.json
    orgao = data.get('orgao')
    
    if not orgao:
        return jsonify({"error": "O nome do órgão é obrigatório"}), 400
    
    # Limpa a fila de resultados anteriores
    while not resultados_queue.empty():
        resultados_queue.get()
    
    # Obtém o total de perguntas para cálculo de progresso
    perguntas = scraper.obter_perguntas_padrao()
    total_perguntas = len(perguntas)
    
    # Inicia o scraping em uma thread separada
    scraping_em_andamento = True
    threading.Thread(target=executar_scraping, args=(orgao,)).start()
    
    return jsonify({
        "message": "Avaliação iniciada com sucesso",
        "totalPerguntas": total_perguntas
    })

def executar_scraping(orgao):
    """Executa o scraping e coloca os resultados na fila"""
    global scraping_em_andamento
    
    try:
        # Obtém a lista de perguntas
        perguntas = scraper.obter_perguntas_padrao()
        total_perguntas = len(perguntas)
        
        # Envia mensagem de status: iniciando busca
        resultados_queue.put({
            "type": "status",
            "message": "Buscando site oficial...",
            "progress": 5
        })
        
        # Busca o site oficial
        site_oficial = None
        
        # 1. Primeiro, tentar URLs diretas baseadas no padrão conhecido
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
        
        # 2. Se não encontrou diretamente, buscar no cache
        if not site_oficial:
            query = f"{orgao} site oficial"
            cached_results = scraper.get_cached_results(query)
            if cached_results and cached_results[0]:
                site_oficial = cached_results[0]
        
        # 3. Por último, fazer busca na web
        if not site_oficial:
            links_site = scraper.buscar_no_google(f"{orgao} site oficial", 3)
            if links_site:
                site_oficial = links_site[0]
        
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
        
        # 1. Primeiro, tentar encontrar no site oficial
        if site_oficial:
            links_transparencia = scraper.find_transparency_links(site_oficial)
            if links_transparencia:
                portal_transparencia = links_transparencia[0]['url']
        
        # 2. Se não encontrou no site oficial, tentar URLs diretas
        if not portal_transparencia:
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
        
        # 3. Se ainda não encontrou, buscar no cache
        if not portal_transparencia:
            query = f"{orgao} portal transparência"
            cached_results = scraper.get_cached_results(query)
            if cached_results and cached_results[0]:
                portal_transparencia = cached_results[0]
        
        # 4. Por último, fazer busca na web
        if not portal_transparencia:
            links_portal = scraper.buscar_no_google(f"{orgao} portal transparência", 3)
            if links_portal:
                portal_transparencia = links_portal[0]
        
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
            elif site_oficial:  # Para outras perguntas, verificar primeiro no site oficial
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
                atende = scraper.verificar_item(url_verificacao, pergunta)
                resultado = {
                    "id": item["id"],
                    "pergunta": pergunta,
                    "classificacao": item["classificacao"],
                    "fundamentacao": item["fundamentacao"],
                    "atende": atende,
                    "disponibilidade": True,
                    "atualidade": True,
                    "serieHistorica": False,
                    "gravacaoRelatorios": False,
                    "filtroPesquisa": False,
                    "linkEvidencia": url_verificacao if atende else None,
                    "observacao": None if atende else f"Informação não encontrada para {orgao} em {url_verificacao}"
                }
            else:
                resultado = {
                    "id": item["id"],
                    "pergunta": pergunta,
                    "classificacao": item["classificacao"],
                    "fundamentacao": item["fundamentacao"],
                    "atende": False,
                    "disponibilidade": False,
                    "atualidade": False,
                    "serieHistorica": False,
                    "gravacaoRelatorios": False,
                    "filtroPesquisa": False,
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
        print(f"Erro durante o scraping: {e}")
        resultados_queue.put({
            "type": "error",
            "message": f"Ocorreu um erro durante a avaliação: {str(e)}",
            "progress": 100
        })
    finally:
        # Envia evento de conclusão
        resultados_queue.put({
            "type": "complete"
        })
        scraping_em_andamento = False

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

@app.route('/')
def index():
    return jsonify({"message": "API do Sistema de Avaliação de Portais de Transparência"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)