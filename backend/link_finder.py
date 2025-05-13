# link_finder.py - Versão anti-detecção de robô
import time
import re
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Orgao, Link, TipoLink
import os
import undetected_chromedriver as uc  # Precisará instalar: pip install undetected-chromedriver

class LinkFinder:
    def __init__(self, db_path='sqlite:///transparencia.db', headless=True, use_undetected=True):
        """
        Inicializa o buscador de links.
        
        Args:
            db_path (str): Caminho para o banco de dados
            headless (bool): Se True, executa o Chrome em modo headless
            use_undetected (bool): Se True, usa undetected_chromedriver para evitar detecção
        """
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Configurar o Chrome
        self.headless = headless
        self.use_undetected = use_undetected
        self.setup_driver()
        
        # Padrões de URL para identificar portais de transparência
        self.patterns = [
            r'transparencia\..*\.gov\.br',
            r'transparente\..*\.gov\.br',
            r'transparencia\..*\.leg\.br',
            r'portal.*transparencia',
            r'transparencia\..*\.org\.br'
        ]
        
        # User agents para rotação
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
    
    def setup_driver(self):
        """Configura o driver do Selenium."""
        if self.use_undetected:
            # Usar undetected_chromedriver para evitar detecção
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-notifications')
            
            # Adicionar argumentos para parecer mais humano
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Pasta de perfil persistente para manter cookies
            profile_path = os.path.join(os.getcwd(), 'chrome_profile')
            if not os.path.exists(profile_path):
                os.makedirs(profile_path)
            options.add_argument(f'--user-data-dir={profile_path}')
            
            # Inicializar o driver
            self.driver = uc.Chrome(options=options)
        else:
            # Configuração padrão com Selenium
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-infobars')
            
            # Adicionar argumentos para parecer mais humano
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Escolher um user agent aleatório
            user_agent = random.choice(self.user_agents)
            options.add_argument(f'--user-agent={user_agent}')
            
            # Pasta de perfil persistente para manter cookies
            profile_path = os.path.join(os.getcwd(), 'chrome_profile')
            if not os.path.exists(profile_path):
                os.makedirs(profile_path)
            options.add_argument(f'--user-data-dir={profile_path}')
            
            # Inicializar o driver
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            
            # Modificar o navigator.webdriver para evitar detecção
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def simular_comportamento_humano(self):
        """Simula comportamento humano para evitar detecção."""
        # Rolar a página aleatoriamente
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(300, 700)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Rolar de volta para o topo
        self.driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(random.uniform(0.5, 1.0))
    
    def buscar_no_banco(self, nome_orgao, tipo_link='portal_transparencia'):
        """
        Busca um link no banco de dados.
        
        Args:
            nome_orgao (str): Nome do órgão
            tipo_link (str): Tipo de link a buscar
            
        Returns:
            str or None: URL encontrada ou None
        """
        session = self.Session()
        
        # Buscar tipo de link
        tipo = session.query(TipoLink).filter(TipoLink.nome == tipo_link).first()
        if not tipo:
            session.close()
            return None
        
        # Buscar órgão e link
        orgao = session.query(Orgao).filter(Orgao.nome.like(f'%{nome_orgao}%')).first()
        if not orgao:
            session.close()
            return None
        
        link = session.query(Link).filter(
            Link.orgao_id == orgao.id,
            Link.tipo_id == tipo.id,
            Link.ativo == True
        ).first()
        
        session.close()
        
        if link:
            return link.url
        return None
    
    def buscar_no_google(self, nome_orgao, tipo_busca='portal transparência'):
        """
        Busca um link usando o Selenium para acessar o Google.
        
        Args:
            nome_orgao (str): Nome do órgão
            tipo_busca (str): Tipo de busca (ex: "portal transparência", "site oficial")
            
        Returns:
            list: Lista de URLs encontradas
        """
        urls = []
        
        try:
            # Usar DuckDuckGo em vez do Google para evitar captcha
            # O DuckDuckGo é menos propenso a bloquear automação
            self.driver.get('https://duckduckgo.com/')
            
            # Esperar um tempo aleatório para parecer humano
            time.sleep(random.uniform(1.0, 3.0))
            
            # Realizar a busca
            query = f"{nome_orgao} {tipo_busca}"
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'search_form_input_homepage'))
            )
            
            # Digitar lentamente como um humano
            for char in query:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(0.5, 1.0))
            search_box.send_keys(Keys.RETURN)
            
            # Esperar pelos resultados
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.result__body'))
            )
            
            # Simular comportamento humano
            self.simular_comportamento_humano()
            
            # Extrair os links dos resultados
            results = self.driver.find_elements(By.CSS_SELECTOR, '.result__a')
            
            for result in results[:5]:  # Pegar os primeiros 5 resultados
                try:
                    url = result.get_attribute('href')
                    if url and 'duckduckgo.com' not in url:
                        # Verificar se é um portal de transparência
                        if tipo_busca == 'portal transparência':
                            for pattern in self.patterns:
                                if re.search(pattern, url, re.IGNORECASE):
                                    urls.append(url)
                                    break
                        else:
                            # Para outros tipos, apenas verificar se é do domínio gov.br ou leg.br
                            if '.gov.br' in url or '.leg.br' in url:
                                urls.append(url)
                except:
                    continue
            
            # Se não encontrou resultados no DuckDuckGo, tentar Bing como fallback
            if not urls:
                print("Tentando busca no Bing...")
                self.driver.get('https://www.bing.com/')
                
                time.sleep(random.uniform(1.0, 3.0))
                
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'sb_form_q'))
                )
                
                # Digitar lentamente
                search_box.clear()
                for char in query:
                    search_box.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                time.sleep(random.uniform(0.5, 1.0))
                search_box.send_keys(Keys.RETURN)
                
                # Esperar pelos resultados
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'b_results'))
                )
                
                # Simular comportamento humano
                self.simular_comportamento_humano()
                
                # Extrair os links
                results = self.driver.find_elements(By.CSS_SELECTOR, '#b_results h2 a')
                
                for result in results[:5]:
                    try:
                        url = result.get_attribute('href')
                        if url and 'bing.com' not in url:
                            if tipo_busca == 'portal transparência':
                                for pattern in self.patterns:
                                    if re.search(pattern, url, re.IGNORECASE):
                                        urls.append(url)
                                        break
                            else:
                                if '.gov.br' in url or '.leg.br' in url:
                                    urls.append(url)
                    except:
                        continue
            
            # Remover duplicatas
            urls = list(dict.fromkeys(urls))
            
        except Exception as e:
            print(f"Erro ao buscar: {e}")
        
        return urls
    
    def verificar_link(self, url):
        """
        Verifica se um link está funcionando.
        
        Args:
            url (str): URL a verificar
            
        Returns:
            bool: True se o link estiver funcionando
        """
        try:
            response = requests.head(url, timeout=10)
            return response.status_code < 400
        except:
            try:
                response = requests.get(url, timeout=10)
                return response.status_code < 400
            except:
                return False
    
    def buscar_link(self, nome_orgao, tipo_link='portal_transparencia', tipo_busca='portal transparência'):
        """
        Busca um link usando estratégia mista (banco + busca web).
        
        Args:
            nome_orgao (str): Nome do órgão
            tipo_link (str): Tipo de link no banco de dados
            tipo_busca (str): Tipo de busca no buscador
            
        Returns:
            dict: Informações sobre o link encontrado
        """
        resultado = {
            "orgao": nome_orgao,
            "tipo": tipo_link,
            "url": None,
            "fonte": None,
            "status": "Não encontrado",
            "alternativas": []
        }
        
        # 1. Buscar no banco de dados
        url_db = self.buscar_no_banco(nome_orgao, tipo_link)
        if url_db:
            # Verificar se o link está funcionando
            if self.verificar_link(url_db):
                resultado["url"] = url_db
                resultado["fonte"] = "banco_dados"
                resultado["status"] = "Encontrado"
                return resultado
            else:
                # Link do banco não funciona, marcar como alternativa
                resultado["alternativas"].append({
                    "url": url_db,
                    "fonte": "banco_dados",
                    "status": "Link inativo"
                })
        
        # 2. Buscar na web com Selenium
        urls_web = self.buscar_no_google(nome_orgao, tipo_busca)
        
        if urls_web:
            # Verificar os links encontrados
            for url in urls_web:
                if self.verificar_link(url):
                    # Se é o primeiro link válido, definir como principal
                    if resultado["url"] is None:
                        resultado["url"] = url
                        resultado["fonte"] = "busca_web"
                        resultado["status"] = "Encontrado"
                    else:
                        # Adicionar como alternativa
                        resultado["alternativas"].append({
                            "url": url,
                            "fonte": "busca_web",
                            "status": "Link ativo"
                        })
                else:
                    # Link inativo, adicionar como alternativa
                    resultado["alternativas"].append({
                        "url": url,
                        "fonte": "busca_web",
                        "status": "Link inativo"
                    })
        
        # 3. Se encontrou um link válido, salvar no banco
        if resultado["url"] and resultado["fonte"] == "busca_web":
            self.salvar_link_no_banco(nome_orgao, tipo_link, resultado["url"])
        
        return resultado
    
    def salvar_link_no_banco(self, nome_orgao, tipo_link, url):
        """
        Salva um novo link no banco de dados.
        
        Args:
            nome_orgao (str): Nome do órgão
            tipo_link (str): Tipo de link
            url (str): URL a salvar
        """
        session = self.Session()
        
        # Buscar tipo de link
        tipo = session.query(TipoLink).filter(TipoLink.nome == tipo_link).first()
        if not tipo:
            # Criar novo tipo se não existir
            tipo = TipoLink(nome=tipo_link)
            session.add(tipo)
            session.flush()
        
        # Buscar órgão
        orgao = session.query(Orgao).filter(Orgao.nome.like(f'%{nome_orgao}%')).first()
        if not orgao:
            # Criar novo órgão se não existir
            # Assumir que é um município do Amazonas por padrão
            orgao = Orgao(nome=nome_orgao, uf='AM', tipo_id=1)  # tipo_id=1 assume que é município
            session.add(orgao)
            session.flush()
        
        # Verificar se já existe este link
        link_existente = session.query(Link).filter(
            Link.orgao_id == orgao.id,
            Link.tipo_id == tipo.id
        ).first()
        
        if link_existente:
            # Atualizar link existente
            link_existente.url = url
            link_existente.ativo = True
            link_existente.ultima_verificacao = time.strftime("%Y-%m-%d")
        else:
            # Criar novo link
            novo_link = Link(
                orgao_id=orgao.id,
                tipo_id=tipo.id,
                url=url,
                ativo=True,
                ultima_verificacao=time.strftime("%Y-%m-%d")
            )
            session.add(novo_link)
        
        session.commit()
        session.close()
    
    def fechar(self):
        """Fecha o driver do Selenium."""
        if hasattr(self, 'driver'):
            self.driver.quit()