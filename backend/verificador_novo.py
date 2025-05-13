from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
import random

class VerificadorTransparencia:
    def __init__(self):
        # Configurar o driver
        self.configurar_driver()
        self.site_oficial = None
        self.portal_transparencia = None
        
    def configurar_driver(self):
        """Configura o driver do Chrome."""
        options = webdriver.ChromeOptions()
        # Não usar headless para evitar detecção
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36')
        
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        # Disfarçar o webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def obter_perguntas_padrao(self):
        """Retorna a lista de perguntas padronizadas."""
        return [
            {
                "id": "1.1",
                "pergunta": "Possui sítio oficial próprio na internet?",
                "classificacao": "Essencial"
            },
            {
                "id": "1.2",
                "pergunta": "Possui portal da transparência próprio ou compartilhado na internet?",
                "classificacao": "Essencial"
            },
            {
                "id": "2.1",
                "pergunta": "Divulga a sua estrutura organizacional?",
                "classificacao": "Obrigatória"
            },
            {
                "id": "2.2",
                "pergunta": "Divulga competências e/ou atribuições?",
                "classificacao": "Obrigatória"
            },
            {
                "id": "2.3",
                "pergunta": "Identifica o nome dos atuais responsáveis pela gestão do Poder/Órgão?",
                "classificacao": "Obrigatória"
            },
            {
                "id": "2.4",
                "pergunta": "Divulga os endereços e telefones atuais do Poder ou órgão e e-mails institucionais?",
                "classificacao": "Obrigatória"
            },
            {
                "id": "8.1",
                "pergunta": "Divulga a relação das licitações em ordem sequencial?",
                "classificacao": "Obrigatória"
            }
            # Adicione mais perguntas conforme necessário
        ]
    
    def extrair_palavras_chave(self, pergunta):
        """Extrai palavras-chave da pergunta."""
        palavras_chave = []
        
        # Palavras-chave padrão para todas as perguntas
        palavras_chave.extend(["site", "oficial", "institucional"])
        
        if "portal" in pergunta.lower() and "transparência" in pergunta.lower():
            palavras_chave.extend(["transparência", "portal", "acesso", "informação"])
        
        if "estrutura" in pergunta.lower() and "organizacional" in pergunta.lower():
            palavras_chave.extend(["organograma", "estrutura", "organizacional", "hierarquia"])
        
        if "competências" in pergunta.lower() or "atribuições" in pergunta.lower():
            palavras_chave.extend(["atribuições", "funções", "competências", "responsabilidades"])
        
        if "responsáveis" in pergunta.lower() or "gestão" in pergunta.lower():
            palavras_chave.extend(["prefeito", "secretários", "gestores", "diretores", "governador"])
        
        if "endereços" in pergunta.lower() or "telefones" in pergunta.lower():
            palavras_chave.extend(["contato", "fale conosco", "telefone", "endereço", "email"])
        
        if "licitações" in pergunta.lower():
            palavras_chave.extend(["licitação", "edital", "pregão", "concorrência", "compras"])
            
        # Remover duplicatas
        palavras_chave = list(set(palavras_chave))
        return palavras_chave
        
    def buscar_sites_do_orgao(self, orgao):
        """Busca o site oficial e portal de transparência com uma única busca no Google."""
        print(f"\n--- Buscando sites para o órgão: {orgao} ---")
        
        # Fazer uma única busca no Google pelo site oficial
        try:
            print("Buscando site oficial...")
            self.driver.get(f"https://www.google.com/search?q={orgao} site oficial gov.br")
            
            # Aguardar carregamento dos resultados
            time.sleep(3)
            
            # Extrair os links dos resultados
            resultados = self.driver.find_elements(By.CSS_SELECTOR, "div.g a")
            for resultado in resultados[:5]:
                try:
                    link = resultado.get_attribute("href")
                    if link and not link.startswith("https://webcache.googleusercontent.com"):
                        if ".gov.br" in link:
                            self.site_oficial = link
                            print(f"Site oficial encontrado: {self.site_oficial}")
                            break
                except:
                    continue
            
            # Fazer uma busca pelo portal da transparência
            print("Buscando portal de transparência...")
            self.driver.get(f"https://www.google.com/search?q={orgao} portal transparência")
            time.sleep(3)
            
            resultados = self.driver.find_elements(By.CSS_SELECTOR, "div.g a")
            for resultado in resultados[:5]:
                try:
                    link = resultado.get_attribute("href")
                    if link and not link.startswith("https://webcache.googleusercontent.com"):
                        if "transparencia" in link.lower() or "transparência" in link.lower():
                            self.portal_transparencia = link
                            print(f"Portal de transparência encontrado: {self.portal_transparencia}")
                            break
                except:
                    continue
                    
            return self.site_oficial, self.portal_transparencia
        
        except Exception as e:
            print(f"Erro ao buscar sites: {e}")
            return None, None
    
    def verificar_item(self, url, pergunta):
        """Verifica um item navegando DENTRO do site já aberto."""
        palavras_chave = self.extrair_palavras_chave(pergunta)
        print(f"\n--- Verificando: {pergunta} ---")
        print(f"URL base: {url}")
        print(f"Palavras-chave: {palavras_chave}")
        
        # Variáveis para rastrear a melhor página encontrada
        melhor_pontuacao = 0
        melhor_url = url
        urls_visitadas = set([url])
        
        try:
            # 1. Verificar a página inicial
            self.driver.get(url)
            time.sleep(3)
            
            # Avaliar a página inicial
            pontuacao_inicial = self.pontuar_pagina_atual(palavras_chave)
            melhor_pontuacao = pontuacao_inicial
            print(f"Pontuação da página inicial: {pontuacao_inicial:.2f}")
            
            # 2. Tentar usar a busca interna do site
            print("Tentando usar busca interna...")
            termos_busca = " ".join(palavras_chave[:2])  # Usar as 2 primeiras palavras-chave
            
            # Lista de possíveis seletores de busca
            seletores_busca = [
                "input[type='search']", 
                "input[name='search']", 
                "input[name='q']", 
                "input[placeholder*='busca']", 
                "input[placeholder*='pesquisa']",
                ".search-form input",
                "#search input"
            ]
            
            busca_feita = False
            for seletor in seletores_busca:
                try:
                    campos_busca = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    if campos_busca:
                        campo = campos_busca[0]
                        campo.clear()
                        for char in termos_busca:
                            campo.send_keys(char)
                            time.sleep(0.05)  # Digitar como humano
                        time.sleep(0.5)
                        campo.send_keys(Keys.RETURN)
                        time.sleep(3)  # Aguardar resultados
                        
                        # Avaliar página de resultados
                        pontuacao_busca = self.pontuar_pagina_atual(palavras_chave)
                        print(f"Pontuação após busca: {pontuacao_busca:.2f}")
                        
                        if pontuacao_busca > melhor_pontuacao:
                            melhor_pontuacao = pontuacao_busca
                            melhor_url = self.driver.current_url
                            
                        urls_visitadas.add(self.driver.current_url)
                        busca_feita = True
                        break
                except Exception as e:
                    print(f"Erro no campo de busca {seletor}: {e}")
                    continue
                    
            # 3. Encontrar e navegar por links relevantes
            if melhor_pontuacao < 0.5:  # Se ainda não encontramos informação suficiente
                print("Procurando links relevantes...")
                self.driver.get(url)  # Voltar para a URL base
                time.sleep(2)
                
                # Encontrar todos os links na página
                elementos_link = self.driver.find_elements(By.TAG_NAME, "a")
                links_relevantes = []
                
                for elemento in elementos_link:
                    try:
                        href = elemento.get_attribute("href")
                        texto = elemento.text.lower()
                        
                        # Ignorar links não válidos
                        if not href or href.startswith("javascript:") or href == "#":
                            continue
                            
                        # Verificar se é link interno (mesmo domínio)
                        dominio_base = "/".join(url.split("/")[:3])  # Ex: https://www.exemplo.gov.br
                        if not href.startswith(dominio_base) and not href.startswith("/"):
                            continue
                            
                        # Pontuar relevância do link
                        relevancia = 0
                        for palavra in palavras_chave:
                            if palavra.lower() in texto or palavra.lower() in href.lower():
                                relevancia += 1
                                
                        if relevancia > 0:
                            links_relevantes.append((href, relevancia, texto))
                    except:
                        continue
                
                # Ordenar links por relevância
                links_relevantes.sort(key=lambda x: x[1], reverse=True)
                
                # Navegar pelos links mais relevantes (máx. 3)
                for href, relevancia, texto in links_relevantes[:3]:
                    try:
                        if href not in urls_visitadas:
                            print(f"Navegando para: {href} (Relevância: {relevancia}, Texto: {texto})")
                            self.driver.get(href)
                            time.sleep(2)
                            
                            # Avaliar esta página
                            pontuacao = self.pontuar_pagina_atual(palavras_chave)
                            print(f"Pontuação: {pontuacao:.2f}")
                            
                            if pontuacao > melhor_pontuacao:
                                melhor_pontuacao = pontuacao
                                melhor_url = href
                                
                            urls_visitadas.add(href)
                    except Exception as e:
                        print(f"Erro ao navegar para {href}: {e}")
                        continue
            
            # Determinar se o item atende com base na melhor pontuação
            atende = melhor_pontuacao >= 0.3  # Limite de 30%
            
            return {
                "atende": atende,
                "pontuacao": melhor_pontuacao,
                "url": melhor_url,
                "observacao": f"Pontuação: {melhor_pontuacao:.0%}" if atende else "Informação não encontrada"
            }
                
        except Exception as e:
            print(f"Erro ao verificar item: {e}")
            return {"atende": False, "pontuacao": 0, "url": url, "observacao": f"Erro: {str(e)}"}
    
    def pontuar_pagina_atual(self, palavras_chave):
        """Avalia o conteúdo da página atual."""
        try:
            # Obter o texto da página
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            texto_pagina = soup.get_text().lower()
            
            # Contar palavras-chave encontradas
            total_palavras = len(palavras_chave)
            encontradas = 0
            
            for palavra in palavras_chave:
                if palavra.lower() in texto_pagina:
                    encontradas += 1
                    
            # Calcular pontuação base
            if total_palavras > 0:
                pontuacao = encontradas / total_palavras
            else:
                pontuacao = 0
                
            # Adicionar bônus por elementos estruturais relevantes
            # Exemplo: tabelas para licitações, imagens para organograma, etc.
            if soup.find_all("table"):
                pontuacao += 0.1
                
            if soup.find_all("img"):
                pontuacao += 0.05
                
            if soup.find_all(["h1", "h2", "h3"], text=lambda t: any(p.lower() in t.lower() for p in palavras_chave)):
                pontuacao += 0.2
                
            return min(pontuacao, 1.0)  # Limitar a 1.0 (100%)
            
        except Exception as e:
            print(f"Erro ao pontuar página: {e}")
            return 0
    
    def avaliar_orgao(self, orgao):
        """Avalia a transparência de um órgão com navegação interna."""
        resultados = []
        
        try:
            # 1. Fazer busca única no Google para encontrar os sites
            self.buscar_sites_do_orgao(orgao)
            
            if not self.site_oficial:
                print("Site oficial não encontrado. Avaliação encerrada.")
                return resultados
                
            # 2. Verificar cada pergunta
            perguntas = self.obter_perguntas_padrao()
            
            for pergunta in perguntas:
                print(f"\n==== Avaliando: {pergunta['id']} - {pergunta['pergunta']} ====")
                
                # Determinar qual URL usar para esta pergunta
                url_base = None
                
                if "portal" in pergunta['pergunta'].lower() or "transparência" in pergunta['pergunta'].lower():
                    url_base = self.portal_transparencia or self.site_oficial
                    print("Usando portal de transparência para esta pergunta")
                elif "licitações" in pergunta['pergunta'].lower():
                    url_base = self.portal_transparencia or self.site_oficial
                    print("Usando portal de transparência para esta pergunta")
                else:
                    url_base = self.site_oficial
                    print("Usando site oficial para esta pergunta")
                
                # Verificar o item
                resultado = self.verificar_item(url_base, pergunta['pergunta'])
                
                # Registrar resultado
                resultados.append({
                    "id": pergunta['id'],
                    "pergunta": pergunta['pergunta'],
                    "classificacao": pergunta['classificacao'],
                    "atende": resultado['atende'],
                    "pontuacao": resultado['pontuacao'],
                    "url": resultado['url'],
                    "observacao": resultado['observacao']
                })
                
                # Pausa entre verificações
                time.sleep(1)
                
            return resultados
            
        except Exception as e:
            print(f"Erro ao avaliar órgão: {e}")
            return resultados
        
    def fechar(self):
        """Fecha o driver."""
        if hasattr(self, 'driver'):
            self.driver.quit()

# Executar diretamente
if __name__ == "__main__":
    # Configurar o verificador
    verificador = VerificadorTransparencia()
    
    try:
        # Definir o órgão a ser avaliado
        orgao = "TCE Amazonas"  # Substitua pelo órgão desejado
        
        print(f"\n{'='*60}")
        print(f"INICIANDO AVALIAÇÃO DE TRANSPARÊNCIA: {orgao}")
        print(f"{'='*60}")
        
        # Executar avaliação
        resultados = verificador.avaliar_orgao(orgao)
        
        # Exibir resultados
        print(f"\n{'='*60}")
        print(f"RESULTADOS DA AVALIAÇÃO: {orgao}")
        print(f"{'='*60}")
        
        for resultado in resultados:
            print(f"\n{resultado['id']} - {resultado['pergunta']}")
            print(f"Classificação: {resultado['classificacao']}")
            print(f"Atende: {'SIM' if resultado['atende'] else 'NÃO'}")
            print(f"Pontuação: {resultado['pontuacao']:.0%}")
            print(f"URL: {resultado['url']}")
            print(f"Observação: {resultado['observacao']}")
        
        # Estatísticas
        atendidos = sum(1 for r in resultados if r['atende'])
        total = len(resultados)
        
        print(f"\n{'='*60}")
        print(f"RESUMO: {atendidos}/{total} critérios atendidos ({atendidos/total:.0%})")
        
    finally:
        # Fechar o navegador ao final
        verificador.fechar()