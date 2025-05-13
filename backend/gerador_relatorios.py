import os
import json
import csv
import datetime
import pandas as pd
from fpdf import FPDF
import xml.etree.ElementTree as ET

class GeradorRelatorios:
    """
    Classe para gerar relatórios em diferentes formatos a partir dos resultados da avaliação.
    Suporta: TXT, CSV, JSON, PDF, XML, ODS (OpenDocument Spreadsheet)
    """
    
    def __init__(self, diretorio_saida="relatorios"):
        """
        Inicializa o gerador de relatórios.
        
        Args:
            diretorio_saida (str): Diretório onde os relatórios serão salvos
        """
        self.diretorio_saida = diretorio_saida
        
        # Criar diretório de saída se não existir
        if not os.path.exists(diretorio_saida):
            os.makedirs(diretorio_saida)
    
    def gerar_nome_arquivo(self, orgao, formato):
        """
        Gera um nome de arquivo padronizado para o relatório.
        
        Args:
            orgao (str): Nome do órgão avaliado
            formato (str): Formato do arquivo (ex: "csv", "json")
            
        Returns:
            str: Caminho completo do arquivo
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"avaliacao_{orgao.replace(' ', '_')}_{timestamp}.{formato}"
        return os.path.join(self.diretorio_saida, nome_arquivo)
    
    def salvar_txt(self, resultados, orgao):
        """
        Salva os resultados em formato TXT.
        
        Args:
            resultados (list): Lista de resultados da avaliação
            orgao (str): Nome do órgão avaliado
            
        Returns:
            str: Caminho do arquivo salvo
        """
        caminho_arquivo = self.gerar_nome_arquivo(orgao, "txt")
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(f"AVALIAÇÃO DE TRANSPARÊNCIA - {orgao}\n")
            f.write(f"Data da avaliação: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            
            for resultado in resultados:
                f.write(f"ID: {resultado['id']}\n")
                f.write(f"Pergunta: {resultado['pergunta']}\n")
                f.write(f"Classificação: {resultado['classificacao']}\n")
                f.write(f"Fundamentação: {resultado['fundamentacao']}\n")
                f.write(f"Atende: {'Sim' if resultado['atende'] else 'Não'}\n")
                
                if 'observacao' in resultado and resultado['observacao']:
                    f.write(f"Observação: {resultado['observacao']}\n")
                
                if 'linkEvidencia' in resultado and resultado['linkEvidencia']:
                    f.write(f"Link de Evidência: {resultado['linkEvidencia']}\n")
                
                f.write("\n" + "-"*50 + "\n\n")
        
        return caminho_arquivo
    
    def salvar_csv(self, resultados, orgao):
        """
        Salva os resultados em formato CSV.
        
        Args:
            resultados (list): Lista de resultados da avaliação
            orgao (str): Nome do órgão avaliado
            
        Returns:
            str: Caminho do arquivo salvo
        """
        caminho_arquivo = self.gerar_nome_arquivo(orgao, "csv")
        
        with open(caminho_arquivo, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Escrever cabeçalho
            writer.writerow([
                'ID', 'Pergunta', 'Classificação', 'Fundamentação', 'Atende', 
                'Disponibilidade', 'Atualidade', 'Série Histórica', 
                'Gravação de Relatórios', 'Filtro de Pesquisa', 
                'Link de Evidência', 'Observação'
            ])
            
            # Escrever dados
            for resultado in resultados:
                writer.writerow([
                    resultado.get('id', ''),
                    resultado.get('pergunta', ''),
                    resultado.get('classificacao', ''),
                    resultado.get('fundamentacao', ''),
                    'Sim' if resultado.get('atende', False) else 'Não',
                    'Sim' if resultado.get('disponibilidade', False) else 'Não',
                    resultado.get('atualidade', 'N/A'),
                    resultado.get('serieHistorica', 'N/A'),
                    resultado.get('gravacaoRelatorios', 'N/A'),
                    resultado.get('filtroPesquisa', 'N/A'),
                    resultado.get('linkEvidencia', ''),
                    resultado.get('observacao', '')
                ])
        
        return caminho_arquivo
    
    def salvar_json(self, resultados, orgao):
        """
        Salva os resultados em formato JSON.
        
        Args:
            resultados (list): Lista de resultados da avaliação
            orgao (str): Nome do órgão avaliado
            
        Returns:
            str: Caminho do arquivo salvo
        """
        caminho_arquivo = self.gerar_nome_arquivo(orgao, "json")
        
        dados = {
            "orgao": orgao,
            "data_avaliacao": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "resultados": resultados
        }
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        
        return caminho_arquivo
    
    def salvar_pdf(self, resultados, orgao):
        """
        Salva os resultados em formato PDF em orientação vertical (retrato) A4.
        
        Args:
            resultados (list): Lista de resultados da avaliação
            orgao (str): Nome do órgão avaliado
            
        Returns:
            str: Caminho do arquivo salvo
        """
        caminho_arquivo = self.gerar_nome_arquivo(orgao, "pdf")
        
        # Função para sanitizar texto para compatibilidade com latin-1
        def sanitizar_texto(texto):
            if not texto:
                return ""
            # Substituir caracteres problemáticos
            replacements = {
                '\u2013': '-',  # traço longo (en dash)
                '\u2014': '-',  # traço mais longo (em dash)
                '\u2018': "'",  # aspas simples esquerda
                '\u2019': "'",  # aspas simples direita
                '\u201c': '"',  # aspas duplas esquerda
                '\u201d': '"',  # aspas duplas direita
                '\u00a0': ' ',  # espaço não-quebrável
                '\u00ba': 'o',  # símbolo de ordenal masculino
                '\u00aa': 'a',  # símbolo de ordenal feminino
                '\u00b0': ' graus',  # símbolo de grau
                '\u00a7': 'paragrafo ',  # símbolo de parágrafo
            }
            
            for unicode_char, ascii_char in replacements.items():
                texto = texto.replace(unicode_char, ascii_char)
            
            # Remover outros caracteres não-latin1
            return ''.join(c if ord(c) < 256 else '?' for c in texto)
            
        # Criar PDF em formato A4 vertical (portrait)
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # Configurar margens
        pdf.set_margins(left=20, top=20, right=20)
        
        # Configurar fonte
        pdf.set_font("Arial", size=12)
        
        # Título
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(170, 10, txt=sanitizar_texto(f"Avaliação de Transparência - {orgao}"), ln=True, align='C')
        
        # Data da avaliação
        pdf.set_font("Arial", size=10)
        pdf.cell(170, 10, txt=sanitizar_texto(f"Data da avaliação: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"), ln=True)
        
        # Adicionar resultados
        pdf.set_font("Arial", size=12)
        for resultado in resultados:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.multi_cell(170, 8, txt=sanitizar_texto(f"ID: {resultado['id']} - {resultado['pergunta']}"))
            
            pdf.set_font("Arial", size=10)
            pdf.cell(170, 8, txt=sanitizar_texto(f"Classificação: {resultado['classificacao']}"), ln=True)
            pdf.multi_cell(170, 6, txt=sanitizar_texto(f"Fundamentação: {resultado['fundamentacao']}"))
            pdf.cell(170, 8, txt=sanitizar_texto(f"Atende: {'Sim' if resultado['atende'] else 'Não'}"), ln=True)
            
            if 'observacao' in resultado and resultado['observacao']:
                pdf.multi_cell(170, 6, txt=sanitizar_texto(f"Observação: {resultado['observacao']}"))
            
            if 'linkEvidencia' in resultado and resultado['linkEvidencia']:
                pdf.multi_cell(170, 6, txt=sanitizar_texto(f"Link de Evidência: {resultado['linkEvidencia']}"))
            
            # Linha separadora
            pdf.line(20, pdf.get_y() + 5, 190, pdf.get_y() + 5)
        
        pdf.output(caminho_arquivo)
        return caminho_arquivo
    
    def salvar_xml(self, resultados, orgao):
        """
        Salva os resultados em formato XML.
        
        Args:
            resultados (list): Lista de resultados da avaliação
            orgao (str): Nome do órgão avaliado
            
        Returns:
            str: Caminho do arquivo salvo
        """
        caminho_arquivo = self.gerar_nome_arquivo(orgao, "xml")
        
        # Criar elemento raiz
        root = ET.Element("AvaliacaoTransparencia")
        
        # Adicionar informações gerais
        info = ET.SubElement(root, "Informacoes")
        ET.SubElement(info, "Orgao").text = orgao
        ET.SubElement(info, "DataAvaliacao").text = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Adicionar resultados
        resultados_elem = ET.SubElement(root, "Resultados")
        
        for resultado in resultados:
            item = ET.SubElement(resultados_elem, "Item")
            
            ET.SubElement(item, "ID").text = resultado.get('id', '')
            ET.SubElement(item, "Pergunta").text = resultado.get('pergunta', '')
            ET.SubElement(item, "Classificacao").text = resultado.get('classificacao', '')
            ET.SubElement(item, "Fundamentacao").text = resultado.get('fundamentacao', '')
            ET.SubElement(item, "Atende").text = 'Sim' if resultado.get('atende', False) else 'Não'
            
            if 'observacao' in resultado and resultado['observacao']:
                ET.SubElement(item, "Observacao").text = resultado['observacao']
            
            if 'linkEvidencia' in resultado and resultado['linkEvidencia']:
                ET.SubElement(item, "LinkEvidencia").text = resultado['linkEvidencia']
        
        # Criar árvore XML e salvar
        tree = ET.ElementTree(root)
        tree.write(caminho_arquivo, encoding='utf-8', xml_declaration=True)
        
        return caminho_arquivo
    
    def salvar_ods(self, resultados, orgao):
        """
        Salva os resultados em formato ODS (OpenDocument Spreadsheet).
        
        Args:
            resultados (list): Lista de resultados da avaliação
            orgao (str): Nome do órgão avaliado
            
        Returns:
            str: Caminho do arquivo salvo
        """
        caminho_arquivo = self.gerar_nome_arquivo(orgao, "ods")
        
        # Criar DataFrame com os resultados
        dados = []
        for resultado in resultados:
            dados.append({
                'ID': resultado.get('id', ''),
                'Pergunta': resultado.get('pergunta', ''),
                'Classificação': resultado.get('classificacao', ''),
                'Fundamentação': resultado.get('fundamentacao', ''),
                'Atende': 'Sim' if resultado.get('atende', False) else 'Não',
                'Disponibilidade': 'Sim' if resultado.get('disponibilidade', False) else 'Não',
                'Atualidade': resultado.get('atualidade', 'N/A'),
                'Série Histórica': resultado.get('serieHistorica', 'N/A'),
                'Gravação de Relatórios': resultado.get('gravacaoRelatorios', 'N/A'),
                'Filtro de Pesquisa': resultado.get('filtroPesquisa', 'N/A'),
                'Link de Evidência': resultado.get('linkEvidencia', ''),
                'Observação': resultado.get('observacao', '')
            })
        
        df = pd.DataFrame(dados)
        
        # Adicionar informações gerais em uma segunda planilha
        info = pd.DataFrame({
            'Informação': ['Órgão', 'Data da Avaliação'],
            'Valor': [orgao, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        })
        
        # Salvar como ODS
        with pd.ExcelWriter(caminho_arquivo, engine='odf') as writer:
            df.to_excel(writer, sheet_name='Resultados', index=False)
            info.to_excel(writer, sheet_name='Informações', index=False)
        
        return caminho_arquivo
    
    def gerar_todos_formatos(self, resultados, orgao):
        """
        Gera relatórios em todos os formatos suportados.
        
        Args:
            resultados (list): Lista de resultados da avaliação
            orgao (str): Nome do órgão avaliado
            
        Returns:
            dict: Dicionário com os caminhos dos arquivos gerados
        """
        arquivos = {}
        
        arquivos['txt'] = self.salvar_txt(resultados, orgao)
        arquivos['csv'] = self.salvar_csv(resultados, orgao)
        arquivos['json'] = self.salvar_json(resultados, orgao)
        
        # Temporariamente desativando PDF para evitar erros de codificação
        try:
            arquivos['pdf'] = self.salvar_pdf(resultados, orgao)
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
            print("Continuando com outros formatos...")
        
        arquivos['xml'] = self.salvar_xml(resultados, orgao)
        
        try:
            arquivos['ods'] = self.salvar_ods(resultados, orgao)
        except Exception as e:
            print(f"Erro ao gerar ODS: {e}")
            print("Continuando com outros formatos...")
        
        return arquivos