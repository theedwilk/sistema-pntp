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
    """Retorna a lista de perguntas padronizadas com ID, classificação e fundamentação."""
    return [
        {
            "id": "1.1",
            "pergunta": "Possui sítio oficial próprio na internet?",
            "classificacao": "Essencial",
            "fundamentacao": "Art. 48, §1º, II, da LC nº 101/00 e arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "1.2",
            "pergunta": "Possui portal da transparência próprio ou compartilhado na internet?",
            "classificacao": "Essencial",
            "fundamentacao": "Art. 48, §1º, II, da LC nº 101/00 e arts. 3º, III, 6º, I, e 8º, §2º, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "1.3",
            "pergunta": "O acesso ao portal transparência está visível na capa do site?",
            "classificacao": "Obrigatória",
            "fundamentacao": "Art. 8º, caput, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "1.4",
            "pergunta": "O site e o portal de transparência contêm ferramenta de pesquisa de conteúdo que permita o acesso à informação?",
            "classificacao": "Obrigatória",
            "fundamentacao": "Art. 8º, § 3º, I, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "2.1",
            "pergunta": "Divulga a sua estrutura organizacional?",
            "classificacao": "Obrigatória",
            "fundamentacao": "Art. 8º, § 3º, I, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "2.2",
            "pergunta": "Divulga competências e/ou atribuições?",
            "classificacao": "Obrigatória",
            "fundamentacao": "Art. 8º, § 1º, I, da Lei nº 12.527/2011 - LAI e art. 6º, VI, b, da Lei 13.460/2017."
        },
        {
            "id": "2.3",
            "pergunta": "Identifica o nome dos atuais responsáveis pela gestão do Poder/Órgão?",
            "classificacao": "Obrigatória",
            "fundamentacao": "Art. 8º, § 3º, I, da Lei nº 12.527/2011 – LAI."
        },
        {
            "id": "2.4",
            "pergunta": "Divulga os endereços e telefones atuais do Poder ou órgão e e-mails institucionais?",
            "classificacao": "Obrigatória",
            "fundamentacao": "Art. 8º, § 1º, I, da Lei nº 12.527/2011 - LAI e art. 6º, VI, b, da Lei 13.460/2017."
        },
        {
            "id": "2.5",
            "pergunta": "Divulga o horário de atendimento?",
            "classificacao": "Obrigatória",
            "fundamentacao": "Art. 8º, § 1º, I, da Lei nº 12.527/2011 - LAI e art. 6º, VI, b, da Lei 13.460/2017."
        },
        {
            "id": "3.1",
            "pergunta": "Divulga as receitas do Poder ou órgão, evidenciando sua previsão e realização?",
            "classificacao": "Obrigatória",
            "fundamentacao": "Art. 48-A, II, da LC nº 101/00."
        },
        {
            "id": "4.1",
            "pergunta": "Divulga o total das despesas empenhadas, liquidadas e pagas?",
            "classificacao": "Obrigatória",
            "fundamentacao": "Art. 48-A, I, da LC nº 101/00."
        },
        {
            "id": "11.5",
            "pergunta": "Divulga o Relatório de Gestão Fiscal (RGF)?",
            "classificacao": "Obrigatória",
            "fundamentacao": "Arts. 54 e 55 da LC nº 101/00."
        }
        # Adicione mais perguntas conforme necessário
    ]

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