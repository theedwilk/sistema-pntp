# scraper.py
import re
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode
import time
import random
import json
import os
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Diretório para cache
CACHE_DIR = 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, 'search_cache.json')

# Lista de palavras-chave para busca de portais de transparência
BUSCA_PORTAL_TRANSPARENCIA = [
    'portal da transparencia',
    'portal da transparência',
    'acesso a informacao',
    'acesso à informação',
    'transparencia',
    'transparência'
]

# Termos para verificar atualização
ATUALIZACAO = [
    "dados atualizados em",
    "última atualização", "ultima atualizacao", "atualizacao", "atualizado em",
    "atualização", "atualizado"
]

# Termos para verificar RGF
termos = [
    "relatorios de gestao fiscal",
    "relatorio de gestao fiscal",
    "rgf"
]

def normalize(text):
    """Remove acentuação e converte para minúsculas."""
    if text is None:
        return ""
    return unidecode(text).strip().lower()

def load_cache():
    """Carrega o cache de buscas anteriores"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    """Salva o cache de buscas"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_cached_results(query, max_age_days=7):
    """Obtém resultados do cache se existirem e forem recentes"""
    cache = load_cache()
    
    if query in cache:
        timestamp = datetime.fromisoformat(cache[query]['timestamp'])
        if datetime.now() - timestamp < timedelta(days=max_age_days):
            print(f"Usando resultados em cache para: {query}")
            return cache[query]['results']
    
    return None

def cache_results(query, results):
    """Adiciona resultados ao cache"""
    cache = load_cache()
    
    cache[query] = {
        'timestamp': datetime.now().isoformat(),
        'results': results
    }
    
    save_cache(cache)
    print(f"Resultados salvos em cache para: {query}")

def search_duckduckgo(query, num_results=5):
    """Busca no DuckDuckGo usando requests (mais rápido, menos detecção)"""
    # Simular um user agent real
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://duckduckgo.com/',
        'DNT': '1',
    }
    
    # Codificar a consulta para URL
    encoded_query = requests.utils.quote(query)
    
    # URL da API do DuckDuckGo (formato HTML)
    url = f'https://html.duckduckgo.com/html/?q={encoded_query}'
    
    # Fazer a requisição
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    # Parsear o HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extrair os resultados
    results = []
    for result in soup.select('.result__a'):
        href = result.get('href', '')
        
        # O DuckDuckGo usa redirecionamento, extrair a URL real
        if '/l/?kh=' in href:
            # Extrair o parâmetro uddg que contém a URL real
            match = re.search(r'uddg=([^&]+)', href)
            if match:
                real_url = requests.utils.unquote(match.group(1))
                results.append(real_url)
                if len(results) >= num_results:
                    break
    
    return results

def search_with_selenium(query, num_results=5):
    """Busca usando Selenium com undetected_chromedriver para evitar detecção"""
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Adicionar comportamento mais humano
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Pasta de perfil persistente
    profile_path = os.path.join(os.getcwd(), 'chrome_profile')
    os.makedirs(profile_path, exist_ok=True)
    options.add_argument(f'--user-data-dir={profile_path}')
    
    driver = None
    try:
        # Inicializar o driver
        driver = uc.Chrome(options=options)
        
        # Tentar primeiro o Bing (menos propenso a bloqueios que o Google)
        driver.get('https://www.bing.com/')
        
        # Esperar carregar
        time.sleep(random.uniform(1.0, 2.0))
        
        # Encontrar a caixa de busca
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'sb_form_q'))
        )
        
        # Limpar a caixa
        search_box.clear()
        
        # Digitar lentamente como um humano
        for char in query:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        # Pequena pausa antes de enviar
        time.sleep(random.uniform(0.5, 1.0))
        search_box.send_keys(Keys.RETURN)
        
        # Esperar pelos resultados
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'b_results'))
        )
        
        # Simular comportamento humano
        for _ in range(random.randint(1, 2)):
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 500)})")
            time.sleep(random.uniform(0.5, 1.0))
        
        # Extrair os links
        results = []
        elements = driver.find_elements(By.CSS_SELECTOR, '#b_results h2 a')
        
        for element in elements[:num_results]:
            url = element.get_attribute('href')
            if url and 'bing.com' not in url and 'microsoft.com' not in url:
                results.append(url)
        
        return results
        
    finally:
        # Fechar o driver
        if driver:
            driver.quit()

def buscar_no_google(query, num_results=5):
    """
    Função de busca que substitui a original, usando técnicas anti-detecção.
    Primeiro verifica o cache, depois tenta DuckDuckGo, e por último Selenium.
    """
    # 1. Verificar cache primeiro
    cached_results = get_cached_results(query)
    if cached_results:
        return cached_results[:num_results]
    
    # 2. Se não estiver em cache, tentar busca direta no DuckDuckGo
    print(f"Realizando busca para: {query}")
    
    try:
        results = search_duckduckgo(query, num_results)
        if results:
            cache_results(query, results)
            return results[:num_results]
    except Exception as e:
        print(f"Erro na busca com DuckDuckGo: {e}")
    
    # 3. Se falhar, tentar com Selenium
    try:
        results = search_with_selenium(query, num_results)
        if results:
            cache_results(query, results)
            return results[:num_results]
    except Exception as e:
        print(f"Erro na busca com Selenium: {e}")
    
    # 4. Se tudo falhar, retornar lista vazia
    return []

def verificar_disponibilidade_simples(url):
    """Verifica se uma URL está disponível"""
    if not url: 
        return False
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        return response.status_code == 200
    except requests.RequestException:
        return False

def verifica_site_ug(query=None, dominio_esperado=None, num_results=5, ug=None):
    """
    Busca os primeiros `num_results` resultados para `query`
    e verifica se algum URL corresponde ao padrão de domínio da UG.
    Retorna Atendido e o primeiro URL oficial encontrado, ou Não atendido e lista de URLs.
    """
    if ug is None and query is None:
        raise ValueError("É necessário fornecer 'ug' ou 'query'")
        
    if query is None:
        query = f"{ug} AM site oficial"
    if dominio_esperado is None:
        dominio_esperado = f"{ug}.am.gov.br"
    
    print(f"Verificando site oficial para: {query}")
    print(f"Domínio esperado: {dominio_esperado}")
    
    # Primeiro, tentar URLs diretas baseadas no padrão conhecido
    dominios_diretos = [
        f"https://www.{ug}.am.gov.br",
        f"https://{ug}.am.gov.br",
        f"https://www.prefeitura{ug}.am.gov.br",
        f"https://prefeitura{ug}.am.gov.br"
    ]
    
    for url in dominios_diretos:
        try:
            print(f"Tentando acesso direto a: {url}")
            response = requests.head(url, timeout=5, 
                                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            if response.status_code < 400:
                print(f"Site encontrado diretamente: {url}")
                return True, url
        except:
            continue
    
    # Se não encontrou diretamente, usar a busca
    resultados = []
    try:
        urls = buscar_no_google(query, num_results=num_results)
        for url in urls:
            resultados.append(url)
            if re.search(dominio_esperado, url, re.IGNORECASE):
                print(f"Site oficial encontrado via busca: {url}")
                return True, url
    except Exception as e:
        print(f"Erro na busca: {e}")
    
    print("Site oficial não encontrado")
    return False, resultados

def find_transparency_links(url):
    """
    Carrega a página e retorna todos os <a> cujo texto ou href
    contenha alguma das palavras-chave definidas em BUSCA_PORTAL_TRANSPARENCIA.
    """
    # Verificar se a URL é válida
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print(f"Buscando links de transparência em: {url}")
    
    # Usar um User-Agent real para evitar bloqueios
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        resp = requests.get(url, timeout=15, headers=headers)
        resp.raise_for_status()
    except Exception as e:
        print(f"Erro ao acessar {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    matches = []

    # Processar todos os links da página
    for a in soup.find_all('a', href=True):
        text_norm = normalize(a.get_text())
        href_norm = normalize(a['href'])
        
        # Verificar se alguma palavra-chave está presente
        for kw in BUSCA_PORTAL_TRANSPARENCIA:
            if kw in text_norm or kw in href_norm:
                # Resolver URLs relativas
                full_url = a['href']
                if not full_url.startswith(('http://', 'https://')):
                    # Resolver URL relativa
                    if full_url.startswith('/'):
                        # URL relativa à raiz
                        domain = re.match(r'(https?://[^/]+)', url)
                        if domain:
                            full_url = domain.group(1) + full_url
                    else:
                        # URL relativa ao caminho atual
                        full_url = url.rstrip('/') + '/' + full_url
                
                matches.append({
                    'texto': a.get_text(strip=True),
                    'url': full_url
                })
                break

    print(f"Encontrados {len(matches)} links de transparência")
    return matches

def obter_perguntas_padrao():
    """Retorna a lista completa de perguntas da matriz comum de transparência."""
    return [
        {
            "id": "1.1",
            "pergunta": "Possui sítio oficial próprio na internet?",
            "dimensao": "Informações Prioritárias",
            "fundamentacao": "Art. 48, §1º, II, da LC nº 101/00 e arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011 – LAI.",
            "classificacao": "Essencial"
        },
        {
            "id": "1.2",
            "pergunta": "Possui portal da transparência próprio ou compartilhado na internet?",
            "dimensao": "Informações Prioritárias",
            "fundamentacao": "Art. 48, §1º, II, da LC nº 101/00 e arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011 – LAI.",
            "classificacao": "Essencial"
        },
        {
            "id": "1.3",
            "pergunta": "O acesso ao portal transparência está visível na capa do site?",
            "dimensao": "Informações Prioritárias",
            "fundamentacao": "Art. 8º, caput, da Lei nº 12.527/2011 – LAI.",
            "classificacao": "Obrigatória"
        },
        {
            "id": "1.4",
            "pergunta": "O site e o portal de transparência contêm ferramenta de pesquisa de conteúdo que permita o acesso à informação?",
            "dimensao": "Informações Prioritárias",
            "fundamentacao": "Art. 8º, § 3º, I, da Lei nº 12.527/2011 – LAI.",
            "classificacao": "Obrigatória"
        },
        {
            "id": "2.1",
            "pergunta": "Disponibiliza a estrutura organizacional, competências, legislação aplicável, principais cargos e seus ocupantes, endereço e telefones das unidades, horários de atendimento ao público?",
            "dimensao": "Informações Institucionais",
            "fundamentacao": "Art. 8º, §1º, I da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "2.2",
            "pergunta": "Disponibiliza dados para contato como endereço físico, telefone e horário de funcionamento?",
            "dimensao": "Informações Institucionais",
            "fundamentacao": "Art. 8º, § 1º, I, da Lei nº 12.527/2011 - LAI e art. 6º, VI, b, da Lei 13.460/2017.",
            "classificacao": "Obrigatória"
        },
        {
            "id": "2.3",
            "pergunta": "Divulga sua estrutura organizacional e competências?",
            "dimensao": "Informações Institucionais",
            "fundamentacao": "Art. 8º, §1º, I da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "2.4",
            "pergunta": "Informa quais são os principais cargos e seus ocupantes (agenda de autoridades)?",
            "dimensao": "Informações Institucionais",
            "fundamentacao": "Art. 8º, §1º, I da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "2.5",
            "pergunta": "Disponibiliza o inteiro teor de leis, decretos, portarias, resoluções ou outros atos normativos?",
            "dimensao": "Informações Institucionais",
            "fundamentacao": "Art. 8º, §1º, I da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "2.6",
            "pergunta": "Divulga a agenda das autoridades?",
            "dimensao": "Informações Institucionais",
            "fundamentacao": "Art. 8º, §1º, I da Lei nº 12.527/2011",
            "classificacao": "Recomendada"
        },
        {
            "id": "2.7",
            "pergunta": "Divulga lista da legislação aplicável?",
            "dimensao": "Informações Institucionais",
            "fundamentacao": "Art. 8º, §1º, I da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "2.8",
            "pergunta": "Divulga planejamento estratégico?",
            "dimensao": "Informações Institucionais",
            "fundamentacao": "Art. 7º, VII, a, da Lei nº 12.527/2011",
            "classificacao": "Recomendada"
        },
        {
            "id": "2.9",
            "pergunta": "Divulga a remuneração e subsídio recebidos por ocupante de cargo, posto, graduação, função e emprego público, incluindo auxílios, ajudas de custo, jetons e quaisquer outras vantagens pecuniárias, bem como proventos de aposentadoria e pensões daqueles que estiverem na ativa, de maneira individualizada?",
            "dimensao": "Informações Institucionais",
            "fundamentacao": "Art. 7º, §3º, VI da Lei nº 12.527/2011, Art. 7º, VI do Decreto nº 7.724/2012",
            "classificacao": "Essencial"
        },
        {
            "id": "3.1",
            "pergunta": "Divulga informações sobre a receita pública?",
            "dimensao": "Receitas",
            "fundamentacao": "Art. 48-A, II, da LC nº 101/2000",
            "classificacao": "Essencial"
        },
        {
            "id": "3.2",
            "pergunta": "As informações sobre receitas estão disponibilizadas em tempo real (dia útil seguinte)?",
            "dimensao": "Receitas",
            "fundamentacao": "Art. 48-A, II, da LC nº 101/2000 e Art. 2º, §2º, II, do Decreto nº 7.185/2010",
            "classificacao": "Essencial"
        },
        {
            "id": "4.1",
            "pergunta": "Divulga informações sobre a despesa pública?",
            "dimensao": "Despesas",
            "fundamentacao": "Art. 48-A, I, da LC nº 101/2000",
            "classificacao": "Essencial"
        },
        {
            "id": "4.2",
            "pergunta": "As informações sobre despesas estão disponibilizadas em tempo real (dia útil seguinte)?",
            "dimensao": "Despesas",
            "fundamentacao": "Art. 48-A, I, da LC nº 101/2000 e Art. 2º, §2º, II, do Decreto nº 7.185/2010",
            "classificacao": "Essencial"
        },
        {
            "id": "5.1",
            "pergunta": "Divulga informações sobre repasses ou transferências de recursos financeiros?",
            "dimensao": "Convênios e Transferências",
            "fundamentacao": "Art. 8º, §1º, II da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "5.2",
            "pergunta": "Divulga informações sobre os convênios celebrados?",
            "dimensao": "Convênios e Transferências",
            "fundamentacao": "Art. 8º, §1º, II da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "5.3",
            "pergunta": "Divulga informações sobre os termos de parceria celebrados?",
            "dimensao": "Convênios e Transferências",
            "fundamentacao": "Art. 8º, §1º, II da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "6.1",
            "pergunta": "Divulga informações sobre concursos públicos?",
            "dimensao": "Recursos Humanos",
            "fundamentacao": "Art. 7º, V e VI da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "6.2",
            "pergunta": "Divulga a relação dos servidores públicos?",
            "dimensao": "Recursos Humanos",
            "fundamentacao": "Art. 7º, V e VI da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
                        "id": "6.3",
            "pergunta": "Divulga informações sobre os servidores terceirizados?",
            "dimensao": "Recursos Humanos",
            "fundamentacao": "Art. 7º, V e VI da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "6.4",
            "pergunta": "Divulga informações sobre os estagiários?",
            "dimensao": "Recursos Humanos",
            "fundamentacao": "Art. 7º, V e VI da Lei nº 12.527/2011",
            "classificacao": "Recomendada"
        },
        {
            "id": "6.5",
            "pergunta": "Divulga informações sobre cargos e salários dos servidores?",
            "dimensao": "Recursos Humanos",
            "fundamentacao": "Art. 7º, V e VI da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "6.6",
            "pergunta": "Divulga informações sobre servidores cedidos e recebidos?",
            "dimensao": "Recursos Humanos",
            "fundamentacao": "Art. 7º, V e VI da Lei nº 12.527/2011",
            "classificacao": "Recomendada"
        },
        {
            "id": "7.1",
            "pergunta": "Divulga informações sobre diárias?",
            "dimensao": "Diárias",
            "fundamentacao": "Art. 8º, §1º, II da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "7.2",
            "pergunta": "Divulga informações sobre passagens?",
            "dimensao": "Diárias",
            "fundamentacao": "Art. 8º, §1º, II da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "8.1",
            "pergunta": "Divulga informações sobre as licitações realizadas e em andamento, com editais, anexos e resultados?",
            "dimensao": "Licitações",
            "fundamentacao": "Art. 8º, §1º, IV da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "8.2",
            "pergunta": "Divulga a relação de licitações abertas, em andamento e já realizadas?",
            "dimensao": "Licitações",
            "fundamentacao": "Art. 8º, §1º, IV da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "8.3",
            "pergunta": "Divulga o conteúdo integral dos editais de licitação?",
            "dimensao": "Licitações",
            "fundamentacao": "Art. 8º, §1º, IV da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "8.4",
            "pergunta": "Divulga o resultado das licitações?",
            "dimensao": "Licitações",
            "fundamentacao": "Art. 8º, §1º, IV da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "8.5",
            "pergunta": "Divulga informações sobre dispensas e inexigibilidades?",
            "dimensao": "Licitações",
            "fundamentacao": "Art. 8º, §1º, IV da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "8.7",
            "pergunta": "Divulga informações sobre impugnações, recursos e representações?",
            "dimensao": "Licitações",
            "fundamentacao": "Art. 7º, VII, a, da Lei nº 12.527/2011",
            "classificacao": "Recomendada"
        },
        {
            "id": "9.1",
            "pergunta": "Divulga informações sobre os contratos celebrados?",
            "dimensao": "Contratos",
            "fundamentacao": "Art. 8º, §1º, IV da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "9.2",
            "pergunta": "Divulga o conteúdo integral dos contratos?",
            "dimensao": "Contratos",
            "fundamentacao": "Art. 8º, §1º, IV da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "9.3",
            "pergunta": "Divulga informações sobre os aditivos e apostilamentos dos contratos?",
            "dimensao": "Contratos",
            "fundamentacao": "Art. 8º, §1º, IV da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "10.2",
            "pergunta": "Divulga informações sobre as obras em andamento?",
            "dimensao": "Obras",
            "fundamentacao": "Art. 8º, §1º, V da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "11.3",
            "pergunta": "Divulga a prestação de contas (relatório de gestão) do ano anterior?",
            "dimensao": "Planejamento e Prestação de contas",
            "fundamentacao": "Art. 48, caput da LC nº 101/2000",
            "classificacao": "Obrigatória"
        },
        {
            "id": "11.5",
            "pergunta": "Divulga Relatório Resumido da Execução Orçamentária (RREO) dos últimos 6 meses?",
            "dimensao": "Planejamento e Prestação de contas",
            "fundamentacao": "Art. 48, caput da LC nº 101/2000",
            "classificacao": "Essencial"
        },
        {
            "id": "11.7",
            "pergunta": "Divulga Relatório de Gestão Fiscal (RGF) dos últimos 6 meses?",
            "dimensao": "Planejamento e Prestação de contas",
            "fundamentacao": "Art. 48, caput da LC nº 101/2000",
            "classificacao": "Essencial"
        },
        {
            "id": "12.1",
            "pergunta": "Disponibiliza informações sobre o Serviço de Informação ao Cidadão (SIC) presencial?",
            "dimensao": "Serviço de Informação ao Cidadão - SIC",
            "fundamentacao": "Art. 9º, I da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "12.2",
            "pergunta": "Disponibiliza informações sobre o Serviço Eletrônico de Informação ao Cidadão (e-SIC)?",
            "dimensao": "Serviço de Informação ao Cidadão - SIC",
            "fundamentacao": "Art. 10º, §2º da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "12.3",
            "pergunta": "Disponibiliza o formulário para pedido de acesso à informação no site?",
            "dimensao": "Serviço de Informação ao Cidadão - SIC",
            "fundamentacao": "Art. 10º, §2º da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "12.4",
            "pergunta": "Possibilita o acompanhamento do pedido de acesso à informação?",
            "dimensao": "Serviço de Informação ao Cidadão - SIC",
            "fundamentacao": "Art. 9º, I, b e Art. 10º, §2º da Lei nº 12.527/2011",
            "classificacao": "Essencial"
        },
        {
            "id": "12.5",
            "pergunta": "Divulga os relatórios estatísticos de atendimento à Lei de Acesso à Informação?",
            "dimensao": "Serviço de Informação ao Cidadão - SIC",
            "fundamentacao": "Art. 30, III da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "12.6",
            "pergunta": "Divulga informações sobre a autoridade responsável pelo monitoramento da implementação da Lei de Acesso à Informação?",
            "dimensao": "Serviço de Informação ao Cidadão - SIC",
            "fundamentacao": "Art. 40, Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "12.7",
            "pergunta": "Divulga respostas às perguntas mais frequentes da sociedade?",
            "dimensao": "Serviço de Informação ao Cidadão - SIC",
            "fundamentacao": "Art. 8º, §1º, VI da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "12.8",
            "pergunta": "Divulga o rol das informações que tenham sido desclassificadas nos últimos 12 (doze) meses?",
            "dimensao": "Serviço de Informação ao Cidadão - SIC",
            "fundamentacao": "Art. 30, I da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "12.9",
            "pergunta": "Divulga o rol de documentos classificados em cada grau de sigilo, com identificação para referência futura?",
            "dimensao": "Serviço de Informação ao Cidadão - SIC",
            "fundamentacao": "Art. 30, II da Lei nº 12.527/2011",
            "classificacao": "Obrigatória"
        },
        {
            "id": "13.1",
            "pergunta": "Disponibiliza o conteúdo acessível para pessoas com deficiência?",
            "dimensao": "Acessibilidade",
            "fundamentacao": "Art. 8º, §3º, VIII da Lei nº 12.527/2011 e Art. 63, Lei nº 13.146/2015",
            "classificacao": "Essencial"
        },
        {
            "id": "13.2",
            "pergunta": "Disponibiliza recursos de acessibilidade (como: alto contraste, atalhos de teclado, barra de acessibilidade, mapa do site, etc)?",
            "dimensao": "Acessibilidade",
            "fundamentacao": "Art. 8º, §3º, VIII da Lei nº 12.527/2011 e Art. 63, Lei nº 13.146/2015",
            "classificacao": "Essencial"
        },
        {
            "id": "13.3",
            "pergunta": "Disponibiliza símbolo de acessibilidade em destaque?",
            "dimensao": "Acessibilidade",
            "fundamentacao": "Art. 8º, §3º, VIII da Lei nº 12.527/2011 e Art. 63, Lei nº 13.146/2015",
            "classificacao": "Essencial"
        },
        {
            "id": "13.4",
            "pergunta": "Disponibiliza intérprete da Língua Brasileira de Sinais (Libras)?",
            "dimensao": "Acessibilidade",
            "fundamentacao": "Art. 8º, §3º, VIII da Lei nº 12.527/2011 e Art. 63, Lei nº 13.146/2015",
            "classificacao": "Essencial"
        },
        {
            "id": "13.5",
            "pergunta": "Disponibiliza VLibras?",
            "dimensao": "Acessibilidade",
            "fundamentacao": "Art. 8º, §3º, VIII da Lei nº 12.527/2011 e Art. 63, Lei nº 13.146/2015",
            "classificacao": "Essencial"
        },
        {
            "id": "14.1",
            "pergunta": "Disponibiliza ouvidoria ou fale conosco?",
            "dimensao": "Ouvidorias",
            "fundamentacao": "Art. 37, §3º, I, CF e Lei nº 13.460/2017",
            "classificacao": "Obrigatória"
        },
        {
            "id": "14.2",
            "pergunta": "Disponibiliza informações sobre o tratamento dado às manifestações registradas na ouvidoria?",
            "dimensao": "Ouvidorias",
            "fundamentacao": "Art. 37, §3º, I, CF e Lei nº 13.460/2017",
            "classificacao": "Obrigatória"
        },
        {
            "id": "14.3",
            "pergunta": "Disponibiliza relatórios estatísticos de atendimento?",
            "dimensao": "Ouvidorias",
            "fundamentacao": "Art. 37, §3º, I, CF e Lei nº 13.460/2017",
            "classificacao": "Obrigatória"
        },
        {
            "id": "15.1",
            "pergunta": "Divulga informações sobre a política de privacidade e os termos de uso?",
            "dimensao": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
            "fundamentacao": "Art. 6º, Lei nº 13.709/2018 (LGPD)",
            "classificacao": "Obrigatória"
        },
        {
            "id": "15.2",
            "pergunta": "Divulga informações sobre o encarregado pelo tratamento de dados pessoais?",
            "dimensao": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
            "fundamentacao": "Art. 41, §1º, Lei nº 13.709/2018 (LGPD)",
            "classificacao": "Obrigatória"
        },
        {
            "id": "15.3",
            "pergunta": "Divulga informações sobre o uso de cookies?",
            "dimensao": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
            "fundamentacao": "Art. 6º, Lei nº 13.709/2018 (LGPD)",
            "classificacao": "Obrigatória"
        },
        {
            "id": "15.4",
            "pergunta": "Divulga informações sobre o tratamento de dados pessoais?",
            "dimensao": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
            "fundamentacao": "Art. 6º, Lei nº 13.709/2018 (LGPD)",
            "classificacao": "Obrigatória"
        },
        {
            "id": "15.5",
            "pergunta": "Divulga informações sobre o acesso e a possibilidade de correção de dados pessoais?",
            "dimensao": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
            "fundamentacao": "Art. 18, Lei nº 13.709/2018 (LGPD)",
            "classificacao": "Obrigatória"
        },
        {
            "id": "15.6",
            "pergunta": "Divulga informações sobre a possibilidade de disponibilização de serviços digitais?",
            "dimensao": "Lei Geral de Proteção de Dados (LGPD) e Governo Digital",
            "fundamentacao": "Lei nº 14.129/2021 (Governo Digital)",
            "classificacao": "Recomendada"
        }
    ]

def obter_perguntas_especificas(tipo_matriz):
    """
    Retorna perguntas específicas para um tipo de matriz.
    
    Args:
        tipo_matriz (str): Tipo de matriz (comum-exceto-estatais-independentes, 
                          comum-exceto-estatais, executivo, etc.)
    
    Returns:
        list: Lista de perguntas específicas para o tipo de matriz
    """
    if tipo_matriz == "comum-exceto-estatais-independentes":
        return [
            {
                "id": "3.1",
                "pergunta": "Divulga as receitas do Poder ou órgão, evidenciando sua previsão e realização?",
                "dimensao": "Receita",
                "fundamentacao": "Arts. 48, §1º, II e 48-A, inciso II, da LC nº 101/00 e art. 8º, II, do Decreto nº 10.540/20.",
                "classificacao": "Essencial"
            },
            {
                "id": "4.1",
                "pergunta": "Divulga o total das despesas empenhadas, liquidadas e pagas?",
                "dimensao": "Despesa",
                "fundamentacao": "Arts. 7º, VI e 8º, §1º, inciso III, da Lei nº 12.527/2011 - LAI; arts. 48, §1º, inciso II e 48-A, inciso I, da LC nº 101/20; art. 8º, inciso I, do Decreto nº 10.540/20.",
                "classificacao": "Essencial"
            },
            {
                "id": "4.2",
                "pergunta": "Divulga as despesas por classificação orçamentária?",
                "dimensao": "Despesa",
                "fundamentacao": "Arts. 7º, VI e 8º, §1º, inciso III, da Lei nº 12.527/2011 - LAI; arts. 48, §1º, inciso II e 48-A, inciso I, da LC nº 101/20; art. 8º, inciso I, do Decreto nº 10.540/20.",
                "classificacao": "Essencial"
            },
            {
                "id": "4.3",
                "pergunta": "Possibilita a consulta de empenhos com os detalhes do beneficiário do pagamento ou credor, o bem fornecido ou serviço prestado e a identificação do procedimento licitatório originário da despesa?",
                "dimensao": "Despesa",
                "fundamentacao": "Arts. 7º, VI e 8º, §1º, inciso III, da Lei nº 12.527/2011 - LAI; arts. 48, §1º, inciso II e 48-A, inciso I, da LC nº 101/20, art. 8º, I, h, do Decreto nº 10.540/2020.",
                "classificacao": "Obrigatória"
            }
        ]
    elif tipo_matriz == "comum-exceto-estatais":
        return [
            {
                "id": "8.6",
                "pergunta": "Divulga o plano de contratações anual (art. 12, VII, da Lei n. 14.133)?",
                "dimensao": "Licitações",
                "fundamentacao": "Art. 12, §1º, da Lei 14.133/2021.",
                "classificacao": "Recomendada"
            },
            {
                "id": "9.4",
                "pergunta": "Divulga a ordem cronológica de seus pagamentos, bem como as justificativas que fundamentaram a eventual alteração dessa ordem?",
                "dimensao": "Contratos",
                "fundamentacao": "Art. 141, § 3º, da Lei 14.133/2021.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "10.1",
                "pergunta": "Divulga informações sobre as obras contendo o objeto, a situação atual, as datas de início e de conclusão da obra, empresa contratada e o percentual concluído?",
                "dimensao": "Obras",
                "fundamentacao": "Art. 8º, § 1º, V da Lei nº 12.527/2011;",
                "classificacao": "Recomendada"
            },
            {
                "id": "10.3",
                "pergunta": "Divulga os quantitativos executados e os preços efetivamente pagos?",
                "dimensao": "Obras",
                "fundamentacao": "Art. 8º, §1º, V da Lei nº 12.527/2011; art. 94, § 3º, da Lei 14.133/2021.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "10.4",
                "pergunta": "Divulga relação das obras paralisadas contendo o motivo, o responsável pela inexecução temporária do objeto do contrato e a data prevista para o reinício da sua execução?",
                "dimensao": "Obras",
                "fundamentacao": "Art. 8º, § 1º, V, da Lei nº 12.527/2011 – LAI e art. 115, § 6º, da Lei nº 14.133/2021.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "11.1",
                "pergunta": "Publica a Prestação de Contas do Ano Anterior (Balanço Geral)?",
                "dimensao": "Planejamento e Prestação de contas",
                "fundamentacao": "Art. 48, caput, da LC nº 101/00.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "11.2",
                "pergunta": "Divulga o Relatório de Gestão ou Atividades?",
                "dimensao": "Planejamento e Prestação de contas",
                "fundamentacao": "Art. 8º, §1º, inciso V, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "11.5",
                "pergunta": "Divulga o Relatório de Gestão Fiscal (RGF)?",
                "dimensao": "Planejamento e Prestação de contas",
                "fundamentacao": "Art. 48, caput, da LC nº 101/00. e para Consórcio: inclui-se a Portaria STN nº. 274/16, art. 14, IV",
                "classificacao": "Essencial"
            }
        ]
    elif tipo_matriz == "executivo":
        return [
            {
                "id": "3.2",
                "pergunta": "Divulga a classificação orçamentária por natureza da receita (categoria econômica, origem, espécie)?",
                "dimensao": "Receita",
                "fundamentacao": "Art. 8º, II, e, do Decreto nº 10.540/2020.",
                "classificacao": "Essencial"
            },
            {
                "id": "3.3",
                "pergunta": "Divulga a lista dos inscritos em dívida ativa, contendo, no mínimo, dados referentes ao nome do inscrito e o valor total da dívida?",
                "dimensao": "Receita",
                "fundamentacao": "Art. 198, § 3º, II da Lei 5.172/1966.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "11.4",
                "pergunta": "Divulga o resultado do julgamento das Contas do Chefe do Poder Executivo pelo Poder Legislativo?",
                "dimensao": "Planejamento e Prestação de contas",
                "fundamentacao": "Art. 56, §3º, da LC nº 101/00.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "11.8",
                "pergunta": "Divulga a Lei do Plano Plurianual (PPA) e seus anexos?",
                "dimensao": "Planejamento e Prestação de contas",
                "fundamentacao": "Art. 48, caput, da LC nº 101/00.",
                "classificacao": "Essencial"
            },
            {
                "id": "11.9",
                "pergunta": "Divulga a Lei de Diretrizes Orçamentárias (LDO) e seus anexos?",
                "dimensao": "Planejamento e Prestação de contas",
                "fundamentacao": "Art. 48, caput, da LC nº 101/00.",
                "classificacao": "Essencial"
            },
            {
                "id": "11.10",
                "pergunta": "Divulga a Lei Orçamentária (LOA) e seus anexos?",
                "dimensao": "Planejamento e Prestação de contas",
                "fundamentacao": "Art. 48, caput, da LC nº 101/00.",
                "classificacao": "Essencial"
            },
            {
                "id": "16.1",
                "pergunta": "Divulga as desonerações tributárias concedidas e a fundamentação legal individualizada?",
                "dimensao": "Renúncias de Receitas",
                "fundamentacao": "Art. 7º, inciso VI, da Lei nº 12.527/2011 - LAI e art. 198, §3º, III, do Código Tributário Nacional.",
                "classificacao": "Recomendada"
            },
            {
                "id": "16.2",
                "pergunta": "Divulga os valores da renúncia fiscal prevista e realizada, por tipo ou espécie de benefício ou incentivo fiscal?",
                "dimensao": "Renúncias de Receitas",
                "fundamentacao": "Art. 37, caput, da CF, Arts. 14, 48, §1º, II e 48-A, inciso II, da LC nº 101/00 e art. 8º, II, do Decreto nº 10.540/20.",
                "classificacao": "Recomendada"
            },
            {
                "id": "16.3",
                "pergunta": "Identifica os beneficiários das desonerações tributárias (benefícios ou incentivos fiscais)?",
                "dimensao": "Renúncias de Receitas",
                "fundamentacao": "Art. 37, caput, da CF, Arts. 14, 48, §1º, II e 48-A, inciso II, da LC nº 101/00 e art. 8º, II, do Decreto nº 10.540/20.",
                "classificacao": "Recomendada"
            },
            {
                "id": "16.4",
                "pergunta": "Divulga informações sobre projetos de incentivo à cultura (incluindo esportivos), identificando os projetos aprovados, o respectivo beneficiário e o valor aprovado?",
                "dimensao": "Renúncias de Receitas",
                "fundamentacao": "Art. 37, caput, da CF, Arts. 14, 48, §1º, II e 48-A, inciso II, da LC nº 101/00 e art. 8º, II, do Decreto nº 10.540/20.",
                "classificacao": "Recomendada"
            },
            {
                "id": "17.1",
                "pergunta": "Identifica as emendas parlamentares recebidas, contendo informações sobre a origem, a forma de repasse, o tipo de emenda, o número da emenda, a autoria, o valor previsto e realizado, o objeto e função de governo?",
                "dimensao": "Emendas Parlamentares",
                "fundamentacao": "Emenda à Constituição nº 105/2019, Portaria Interministerial ME/SEGOV nº 6.411/2021, art. 19; Nota Recomendatória Atricon nº 01/2022; Acórdão nº 518/2023 - TCU-Plenário.",
                "classificacao": "Recomendada"
            },
            {
                "id": "17.2",
                "pergunta": "Demonstra a execução orçamentária e financeira oriunda das emendas pix?",
                "dimensao": "Emendas Parlamentares",
                "fundamentacao": "Art. 166-A, I (Emenda à Constituição nº 105/2019), Portaria Interministerial ME/SEGOV nº 6.411/2021, art. 19; Nota Recomendatória Atricon nº 01/2022; Acórdão nº 518/2023 - TCU-Plenário, Portaria Conjunta MF/MPO/MGI/SRI-PR nº 1, de 1º de abril de 2024",
                "classificacao": "Recomendada"
            },
            {
                "id": "18.1",
                "pergunta": "Divulga o plano de saúde, a programação anual e o relatório de gestão?",
                "dimensao": "Saúde",
                "fundamentacao": "Art. 8º, § 1º, V e art. 9º, II, da Lei nº 12.527/2011 - LAI e art. 37, caput, da CF (princípio da publicidade).",
                "classificacao": "Obrigatória"
            },
                        {
                "id": "18.2",
                "pergunta": "Divulga informações relacionadas aos serviços de saúde, indicando os horários, os profissionais prestadores de serviços, as especialidades e local?",
                "dimensao": "Saúde",
                "fundamentacao": "Art. 7º, VI, da Lei nº 8.080/1990.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "18.3",
                "pergunta": "Divulga a lista de espera de regulação para acesso às consultas, exames e serviços médicos?",
                "dimensao": "Saúde",
                "fundamentacao": "Portaria nº 1.559, de 1º de agosto de 2008.",
                "classificacao": "Recomendada"
            },
            {
                "id": "18.4",
                "pergunta": "Divulga lista dos medicamentos a serem fornecidos pelo SUS e informações de como obter medicamentos, incluindo os de alto custo?",
                "dimensao": "Saúde",
                "fundamentacao": "Art. 26, parágrafo único, inciso I, do Decreto n. 7.508, de 28 de junho de 2011 (redação dada pelo Decreto n. 11.161, de 2022).",
                "classificacao": "Recomendada"
            },
            {
                "id": "18.5",
                "pergunta": "Divulga os estoques de medicamentos das farmácias públicas?",
                "dimensao": "Saúde",
                "fundamentacao": "Art. 6º-A da Lei nº 8.080/1990 (alterada pela Lei nº 14.654/2023)",
                "classificacao": "Obrigatória"
            },
            {
                "id": "19.1",
                "pergunta": "Divulga o plano de educação e o respectivo relatório de resultados?",
                "dimensao": "Educação",
                "fundamentacao": "Art. 37, caput da CF; Art. 8º, § 1º, V, da Lei nº 12.527/2011 – LAI e Art. 8º da Lei nº 13.005/2014.",
                "classificacao": "Recomendada"
            },
            {
                "id": "19.2",
                "pergunta": "Divulga a lista de espera em creches públicas e os critérios de priorização de acesso a elas?",
                "dimensao": "Educação",
                "fundamentacao": "Art. 37, caput da CF e Art. 8º, § 1º, V, da Lei nº 12.527/2011 – LAI; Art. 5º, §1º, IV da Lei nº 9.394/96 (LDB, alterada pela Lei nº 14.685/23)",
                "classificacao": "Obrigatória"
            }
        ]
    elif tipo_matriz == "executivo-consorcios":
        return [
            {
                "id": "11.6",
                "pergunta": "Divulga o Relatório Resumido da Execução Orçamentária (RREO)?",
                "dimensao": "Planejamento e Prestação de contas",
                "fundamentacao": "Art. 48, caput, da LC nº 101/00. Consórcio: Portaria STN nº. 274/16, art. 14, IV",
                "classificacao": "Essencial"
            }
        ]
    elif tipo_matriz == "legislativo":
        return [
            {
                "id": "20.1",
                "pergunta": "Divulga a composição da Casa, com a biografia dos parlamentares?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "Art. 37, caput da CF e Art. 8º, § 1º, I, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "20.2",
                "pergunta": "Divulga as leis e atos infralegais (resoluções, decretos, etc.) produzidos?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "Art. 37, da CF (princípio da publicidade) e arts. 6, inciso I, e 8º da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "20.3",
                "pergunta": "Divulga projetos de leis e de atos infralegais, bem como as respectivas tramitações (contemplando ementa, documentos anexos, situação atual, autor, relator)?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "Art. 37, da CF (princípio da publicidade) e arts. 6, inciso I, e 8º da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "20.4",
                "pergunta": "Divulga a pauta das sessões do Plenário?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "arts. 7º, incisos IV, V e VI, e 8º caput da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "20.5",
                "pergunta": "Divulga a pauta das Comissões?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "Art. 37, caput, da CF e Art. 3, II, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "20.6",
                "pergunta": "Divulga as atas das sessões, incluindo a lista de presença dos parlamentares em cada sessão?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "Art. 37, caput, da CF e Art. 3, II, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "20.7",
                "pergunta": "Divulga lista sobre as votações nominais?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "Art. 37, caput, da CF e Art. 3, II, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            },
            {
                "id": "20.8",
                "pergunta": "Divulga o ato que aprecia as Contas do Chefe do Poder Executivo (Decreto) e o teor do julgamento (Ata ou Resumo da Sessão que aprovou ou rejeitou as contas)?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "Art. 7º, inciso VII, alínea b, da Lei nº 12.527/2011 - LAI e art. 56, §3º, da LRF.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "20.9",
                "pergunta": "Há transmissão de sessões, audiências públicas, consultas públicas ou outras formas de participação popular via meios de comunicação como rádio, TV, internet, entre outros?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "Arts. 7, 13 e ss. da Lei 13.460/17, c/c art. 9º, inciso II, da Lei nº 12.527/2011 - LAI e art. 37, caput, da CF (princípio da publicidade).",
                "classificacao": "Recomendada"
            },
            {
                "id": "20.10",
                "pergunta": "Divulga a regulamentação e os valores relativos às cotas para exercício da atividade parlamentar/verba indenizatória?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "Arts. 7º, incisos IV e V, e 8º caput da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            },
            {
                "id": "20.11",
                "pergunta": "Divulga dados sobre as atividades legislativas dos parlamentares?",
                "dimensao": "Atividades Finalísticas - PL",
                "fundamentacao": "Art. 37, caput da CF e Art. 8º, § 1º, V, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            }
        ]
    elif tipo_matriz == "judiciario":
        return [
            {
                "id": "21.1",
                "pergunta": "Divulga a composição da Casa, com a indicação de onde cada magistrado atua?",
                "dimensao": "Atividades Finalísticas - PJ",
                "fundamentacao": "Art. 37, caput da CF e Art. 8º, § 1º, I, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            },
            {
                "id": "21.2",
                "pergunta": "Divulga pauta das sessões?",
                "dimensao": "Atividades Finalísticas - PJ",
                "fundamentacao": "Art. 7º, V, da Lei nº 12.527/2011 - LAI; art. 12, § 1º, da Lei nº 13.105/15.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "21.3",
                "pergunta": "Divulga ata das sessões de julgamento/deliberativas?",
                "dimensao": "Atividades Finalísticas - PJ",
                "fundamentacao": "Arts. 37, caput (princípio da publicidade), e 93, IX e X, da CF; arts. 7º, II e V, e 8º, caput, da Lei nº 12.527/2011 - LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "21.4",
                "pergunta": "Divulga suas decisões?",
                "dimensao": "Atividades Finalísticas - PJ",
                "fundamentacao": "Arts. 7º, incisos II e VI, e 8º, caput da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "21.5",
                "pergunta": "Divulga informativo de jurisprudência contendo decisões atualizadas?",
                "dimensao": "Atividades Finalísticas - PJ",
                "fundamentacao": "Arts. 37, caput (princípio da publicidade), e 93, IX e X, da CF; arts. 7º, II e V, e 8º, caput, da Lei nº 12.527/2011 - LAI e art. 24, parágrafo único da do Decreto-Lei nº 4.657/42.",
                "classificacao": "Recomendada"
            },
            {
                "id": "21.6",
                "pergunta": "Há transmissão das sessões de julgamento e eventuais audiências públicas via meios de comunicação como rádio, TV, internet, entre outros?",
                "dimensao": "Atividades Finalísticas - PJ",
                "fundamentacao": "Art. 37, caput, da CF e Arts. 3º, incisos II, III e X, e 14 da Lei 14.129/2021 e Art. 3º, III, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            }
        ]
    elif tipo_matriz == "tribunal-contas":
        return [
            {
                "id": "22.1",
                "pergunta": "Divulga a composição da Casa, com a indicação das funções exercidas por membro e onde cada um deles atua?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 37, caput da CF e Art. 8º, § 1º, I, da Lei nº 12.527/2011 - LAI.",
                "classificacao": "Recomendada"
            },
            {
                "id": "22.2",
                "pergunta": "Divulga pauta das sessões?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Arts. 7º, incisos IV e V; e 8º, caput da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "22.3",
                "pergunta": "Divulga ata das sessões de julgamento/deliberativas?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Arts. 7º, incisos IV e V, e 8º, caput, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "22.4",
                "pergunta": "Divulga suas Decisões?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Arts. 7º, incisos II e VI, e 8º, caput da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "22.5",
                "pergunta": "Divulga as peças dos processos em trâmite nos Tribunais de Contas a partir da análise do contraditório?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Arts. 37, caput (princípio da publicidade), e 93, IX e X, da CF c/c arts. 7º, II, V, VII, b e 8º, caput, da Lei nº 12.527/2011 - LAI; Normas Brasileiras de Auditoria no Setor Público - NBASP nº 1 (VI, seções 16 e 17) 12 (princípio 4, 31), 20 (18, 28, princípio 7, 35, 36, 37, 38, 39, princípio 8, 40, 41, 42, 43), 100 (43 e 51), 300 (29 e 41), 400 (49) e 300 (133, 134 e 135).",
                "classificacao": "Recomendada"
            },
            {
                "id": "22.6",
                "pergunta": "Divulga a íntegra dos processos após o trânsito em julgado?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Arts. 37, caput (princípio da publicidade), e 93, IX e X, da CF c/c arts. 7º, II, V, VII, b e 8º, caput, da Lei nº 12.527/2011 - LAI, Normas Brasileiras de Auditoria no Setor Público - NBASP nº 1 (VI, seções 16 e 17) 12 (princípio 4, 31), 20 (18, 28, princípio 7, 35, 36, 37, 38, 39, princípio 8, 40, 41, 42, 43), 100 (43 e 51), 300 (29 e 41), 400 (49) e 300 (133, 134 e 135).",
                "classificacao": "Obrigatória"
            },
            {
                "id": "22.7",
                "pergunta": "Divulga informativo de jurisprudência contendo decisões atualizadas?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Arts. 37, caput (princípio da publicidade), e 93, IX e X, da CF; arts. 7º, II e V, e 8º, caput, da Lei nº 12.527/2011 - LAI e art. 24, parágrafo único da do Decreto-Lei nº 4.657/42, Normas Brasileiras de Auditoria no Setor Público - NBASP nº 1 (VI, seções 16 e 17) 12 (princípio 4, 31), 20 (18, 28, princípio 7, 35, 36, 37, 38, 39, princípio 8, 40, 41, 42, 43), 100 (43 e 51), 300 (29 e 41), 400 (49) e 300 (133, 134 e 135).",
                "classificacao": "Recomendada"
            },
            {
                "id": "22.8",
                "pergunta": "Divulga informações técnicas de cunho orientativo?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 37, caput, da CF e Art. 3, II, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            },
            {
                "id": "22.9",
                "pergunta": "Informa sobre valor das condenações (débitos e multas)?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 37, caput, da CF e Art. 3, II, da Lei nº 12.527/2011 - LAI, Normas Brasileiras de Auditoria no Setor Público - NBASP nº 1 (VI, seções 16 e 17) 12 (princípio 4, 31), 20 (18, 28, princípio 7, 35, 36, 37, 38, 39, princípio 8, 40, 41, 42, 43), 100 (43 e 51), 300 (29 e 41), 400 (49) e 300 (133, 134 e 135).",
                "classificacao": "Recomendada"
            },
            {
                "id": "22.10",
                "pergunta": "Divulga relação de responsáveis que tiveram suas contas julgadas irregulares ou receberam parecer pela reprovação de suas contas?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Arts. 7º, incisos IV e V, e 8º caput da LAI, Normas Brasileiras de Auditoria no Setor Público - NBASP nº 1 (VI, seções 16 e 17) 12 (princípio 4, 31), 20 (18, 28, princípio 7, 35, 36, 37, 38, 39, princípio 8, 40, 41, 42, 43), 100 (43 e 51), 300 (29 e 41), 400 (49) e 300 (133, 134 e 135).",
                "classificacao": "Recomendada"
            },
            {
                "id": "22.11",
                "pergunta": "O Tribunal de Contas disponibiliza dados atualizados encaminhados pelos respectivos entes fiscalizados (Estados ou Municípios) referentes à despesa e à receita?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Arts. 7º, II, V e VI e 8º, caput da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            },
            {
                "id": "22.12",
                "pergunta": "Há transmissão das sessões de julgamento e eventuais audiências públicas via meios de comunicação como rádio, TV, internet, entre outros?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 37, caput, da CF e Arts. 3º, incisos II, III e X, e 14 da Lei 14.129/2021 e Art. 3º, III, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            }
        ]
    elif tipo_matriz == "ministerio-publico":
        return [
            {
                "id": "23.1",
                "pergunta": "Divulga a composição da Casa, com a indicação de onde cada membro atual?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 37, caput da CF e Art. 8º, § 1º, I, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            },
            {
                "id": "23.2",
                "pergunta": "Divulga os registros de procedimentos preparatórios e de seus respectivos andamentos?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 3º, II e V, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "23.3",
                "pergunta": "Divulga os registros de procedimentos de investigação e de seus respectivos andamentos?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 3º, II e V, da Lei nº 12.527/2011 - LAI.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "23.4",
                "pergunta": "Divulga os registros sobre os inquéritos civis e de seus respectivos andamentos?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 3º, II e V, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Obrigatória"
            }
        ]
    elif tipo_matriz == "defensoria":
        return [
            {
                "id": "24.1",
                "pergunta": "Divulga a composição da Casa?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 37, caput da CF e Art. 8º, § 1º, I, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            },
            {
                "id": "24.2",
                "pergunta": "Disponibiliza material informativo?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 3º, II e V, da Lei nº 12.527/2011 – LAI.",
                "classificacao": "Recomendada"
            },
            {
                "id": "24.3",
                "pergunta": "Disponibiliza informações sobre o atendimento?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Art. 4º-A, I, da Lei Complementar nº 80/1994.",
                "classificacao": "Recomendada"
            }
        ]
    elif tipo_matriz == "consorcios":
        return [
            {
                "id": "11.11",
                "pergunta": "Divulga o Orçamento do Consórcio Público onde conste a estimativa da receita e a fixação da despesa para o exercício atual?",
                "dimensao": "Planejamento e Prestação de contas",
                "fundamentacao": "Art. 48, caput, da LC nº 101/00; Portaria STN nº. 274/16, art 2, II, Art 6 e art. 14, IV.",
                "classificacao": "Obrigatória"
            },
            {
                "id": "25.1",
                "pergunta": "Divulga o protocolo de intenções que antecede a formalização do Contrato?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Lei Federal nº 11.107/2005, art. 4º, §2º e 5º.",
                "classificacao": "Recomendada"
            },
            {
                "id": "25.2",
                "pergunta": "Divulga estatuto do consórcio?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Lei Federal nº 11.107/2005, art. 7º; Decreto Federal nº. 6.017/07, art. 8º, §3º.",
                "classificacao": "Recomendada"
            },
            {
                "id": "25.3",
                "pergunta": "Divulga os contratos de rateio?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Lei Federal nº 11.107/2005, art. 8º, §1º; Portaria STN nº. 274/16, art. 14, II; Lei Complementar nº 101, de 4 de maio de 2000.",
                "classificacao": "Recomendada"
            },
            {
                "id": "25.4",
                "pergunta": "Divulga o Contrato de Programa?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Lei Federal nº 11.107/2005, art. 13, §1º, II; Decreto Federal nº. 6.017/07, art. 33, V",
                "classificacao": "Recomendada"
            },
            {
                "id": "25.5",
                "pergunta": "Divulga a ata de eleição dos atuais dirigentes?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Lei Federal nº 11.107/2005, art. 6º, §1º; Decreto Federal nº. 6.017/07",
                "classificacao": "Recomendada"
            },
            {
                "id": "25.6",
                "pergunta": "Divulga as atas da assembleia geral?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Lei Federal nº 11.107/2005; Decreto Federal nº. 6.017/07",
                "classificacao": "Recomendada"
            },
            {
                "id": "25.7",
                "pergunta": "Divulga os entes consorciados (municípios integrantes)?",
                "dimensao": "Atividades Finalísticas",
                "fundamentacao": "Lei Federal nº 11.107/2005; Decreto Federal nº. 6.017/07",
                "classificacao": "Recomendada"
            }
        ]
    elif tipo_matriz == "estatais":
        return [
            {
                "id": "4.4",
                "pergunta": "Publica relação das despesas com aquisições de bens efetuadas pela instituição contendo: identificação do bem, preço unitário, quantidade, nome do fornecedor e valor total de cada aquisição?",
                "dimensao": "Despesa",
                "fundamentacao": "Estatais Dependentes: Art. 3º c/c art. 6º, I, c/c art. 7º, II e VI, c/c art. 8º, caput e § 1º, III-IV e § 2º da Lei 12.527/2011 (LAI); Art. 48 da Lei 13.303/2016. Estatais Independentes: Arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011(LAI).",
                "classificacao": "Recomendada"
            },
            # Adicione as outras perguntas para estatais...
        ]
    elif tipo_matriz == "estatais-independentes":
        return [
            {
                "id": "11.14",
                "pergunta": "Pública o Orçamento de Investimentos da instituição que compõe a Lei Orçamentária Anual?",
                "dimensao": "Planejamento e Prestação de contas",
                "fundamentacao": "Art. 3º combinado com art. 6º, I, combinado com art. 7º, II, VI e VII, combinado com art. 8º, caput e § 1º, III e V, e § 2º da Lei 12.527/2011 (LAI); Art. 7º, § 3º, II-IV, do Decreto 7.724/2012;",
                "classificacao": "Obrigatória"
            }
        ]
    
    return []  # Retorna lista vazia se o tipo de matriz não for reconhecido

def verificar_item(url, pergunta):
    """
    Verifica se um item específico é atendido na URL fornecida.
    """
    try:
        # Verificar disponibilidade básica
        if not verificar_disponibilidade_simples(url):
            return False
            
        # Verificações específicas baseadas na pergunta
        if "sítio oficial" in pergunta.lower():
            return True  # Se chegou aqui, o site está disponível
            
        if "portal da transparência" in pergunta.lower():
            links = find_transparency_links(url)
            return len(links) > 0
            
        # Para outras perguntas, verificar se há palavras-chave no conteúdo
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = normalize(soup.get_text())
        
        # Extrair palavras-chave da pergunta
        keywords = [w for w in normalize(pergunta).split() if len(w) > 3]
        
        # Verificar se pelo menos 50% das palavras-chave estão presentes
        matches = sum(1 for kw in keywords if kw in text)
        return matches >= len(keywords) * 0.5
        
    except Exception as e:
        print(f"Erro ao verificar item: {e}")
        return False

def pagina_tem_termo(url, termos_lista):
    """Verifica se a página contém algum dos termos especificados"""
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        resp.raise_for_status()
    except requests.RequestException:
        return False
    
    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.body.get_text() if soup.body else ""
    texto = normalize(content)
    
    return any(termo in texto for termo in termos_lista)

def ultimo_quadrimestre_exigivel(avaliacao):
    """
    Retorna (ano, quadrimestre) do último RGF exigível na data de avaliação.
    """
    ano = avaliacao.year

    # 1) Definições de término de cada quadrimestre no ano corrente
    termos = [
        (ano, 1, datetime(ano, 4, 30).date()),
        (ano, 2, datetime(ano, 8, 31).date()),
        (ano, 3, datetime(ano, 12, 31).date()),
    ]

    periodos = []
    # 2) Para cada, calcula due_date = fim + 30 dias
    for y, q, fim in termos:
        due = fim + timedelta(days=30)
        periodos.append((y, q, due))

    # 3) Inclui também o Q3 do ano anterior
    prev = ano - 1
    fim_prev = datetime(prev, 12, 31).date()
    periodos.append((prev, 3, fim_prev + timedelta(days=30)))

    # 4) Filtra os já exigíveis (due_date <= data de avaliação)
    exigiveis = [(y, q) for (y, q, due) in periodos if due <= avaliacao]

    # 5) Seleciona o mais recente por comparação lexicográfica
    if exigiveis:
        return max(exigiveis)
    return (ano-1, 3)  # Fallback para o último do ano anterior

def pagina_tem_atualidade(url, quadr):
    """
    Verifica se, na página indicada, há menção ao RGF do último quadrimestre.
    """
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        resp.raise_for_status()
    except requests.RequestException:
        return False

    soup = BeautifulSoup(resp.text, "html.parser")
    content = soup.body.get_text() if soup.body else ""
    texto = normalize(content)

    termo_quad_acento = f"{quadr}º quadrimestre"
    termo_quad = f"{quadr}o quadrimestre"

    return (
        "rgf" in texto and
        (termo_quad_acento in texto or termo_quad in texto)
    )

# Funções de verificação para critérios específicos
def check_disponibilidade(soup):
    # Implementação genérica para verificar disponibilidade
    full_text = normalize(soup.get_text(separator=" "))
    # Verificar palavras-chave relevantes para receitas
    keywords = ["receita", "arrecadacao", "previsao", "realizado"]
    return any(kw in full_text for kw in keywords)

def check_atualidade(soup):
    # Busca por indicações de atualização recente
    for t in soup.stripped_strings:
        tn = normalize(t)
        if any(syn in tn for syn in ATUALIZACAO):
            m = re.search(r'(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}:\d{2}))?', t)
            if not m:
                return False
            data_str = m.group(1)
            fmt = '%d/%m/%Y'
            if m.group(2):
                data_str += ' ' + m.group(2)
                fmt = '%d/%m/%Y %H:%M:%S'
            try:
                dt = datetime.strptime(data_str, fmt)
                return datetime.now() - dt <= timedelta(days=30)
            except:
                return False
    return False

def check_serie_historica(soup, ano=None):
    if ano is None:
        ano = datetime.now().year
    # Busca por seletor de anos ou lista de anos no texto
    select = soup.find('select', {'name': re.compile(r'ano|exercicio', re.I)})
    if select:
        anos = {int(opt['value']) for opt in select.find_all('option') if opt.get('value','').isdigit()}
        return {ano-1, ano-2, ano-3}.issubset(anos)
    
    # Se não encontrou select, procura anos no texto
    text = soup.get_text()
    anos = {int(y) for y in re.findall(r'\b(20\d{2})\b', text) if y.isdigit()}
    return {ano-1, ano-2, ano-3}.issubset(anos)

def check_gravacao_relatorios(soup):
    # Busca por links de download em formatos comuns
    formatos = ('.xls', '.xlsx', '.csv', '.txt', '.odt', '.ods', '.rtf', '.json', '.pdf')
    for a in soup.find_all('a', href=True):
        href = a['href'].lower()
        if any(ext in href for ext in formatos):
            return True
    
    # Busca por botões ou links com texto sugestivo
    for elem in soup.find_all(['a', 'button']):
        text = normalize(elem.get_text())
        if any(kw in text for kw in ['download', 'exportar', 'baixar', 'salvar', 'gerar']):
            return True
    
    return False

def check_filtro_pesquisa(soup):
    # Busca por elementos de formulário para filtro ou pesquisa
    has_search = bool(
        soup.find('input', {'type': 'search'}) or
        soup.find('input', {'placeholder': re.compile(r'pesquisa|search|filtro|busca', re.I)}) or
        soup.find('input', {'aria-label': re.compile(r'pesquisa|search|filtro|busca', re.I)})
    )
    
    has_select = bool(soup.find('select'))
    has_filter_button = bool(soup.find(['button', 'a'], string=re.compile(r'filtrar|pesquisar|buscar', re.I)))
    
    return has_search or has_select or has_filter_button

# Aliases para compatibilidade com código existente
check_availability = check_disponibilidade
check_recency = check_atualidade
check_historical = check_serie_historica
check_download = check_gravacao_relatorios
check_filter = check_filtro_pesquisa
check_disponibility = check_disponibilidade
check_historico = check_serie_historica

def avaliar_transparencia(orgao):
    """Realiza a avaliação de transparência para um órgão."""
    resultados = []
    
    # Buscar site oficial
    print(f"Buscando site oficial para: {orgao}")
    tem_site, url_site = verifica_site_ug(query=f"{orgao} site oficial")
    
    if not tem_site:
        # Se não tem site, já retorna com resultado negativo
        return [{
            "id": "1.1",
            "pergunta": "Possui sítio oficial próprio na internet?",
            "atende": False,
            "disponibilidade": False,
            "atualidade": False,
            "serieHistorica": False,
            "gravacaoRelatorios": False,
            "filtroPesquisa": False,
            "linkEvidencia": None,
            "observacao": "Site oficial não encontrado"
        }]
    
    # Para cada pergunta do questionário
    perguntas = obter_perguntas_padrao()
    for pergunta in perguntas:
        resultado = verificar_item(url_site, pergunta["pergunta"])
        resultados.append({
            "id": pergunta["id"],
            "pergunta": pergunta["pergunta"],
            "atende": resultado,
            "disponibilidade": resultado,
            "atualidade": False if not resultado else check_atualidade(url_site),
            "serieHistorica": False if not resultado else check_serie_historica(url_site),
            "gravacaoRelatorios": False if not resultado else check_gravacao_relatorios(url_site),
            "filtroPesquisa": False if not resultado else check_filtro_pesquisa(url_site),
            "linkEvidencia": url_site if resultado else None,
            "observacao": None if resultado else "Informação não encontrada"
        })
        
    return resultados