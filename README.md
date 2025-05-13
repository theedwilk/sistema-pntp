# Sistema PNTP - Avaliador de Transparência Pública

Um sistema automatizado para avaliação da transparência de órgãos públicos no estado do Amazonas.

## Descrição

Este sistema utiliza web scraping para analisar sites de órgãos públicos e verificar se atendem aos requisitos de transparência conforme a legislação brasileira. O sistema avalia critérios como:

- Existência de site oficial
- Portal da transparência
- Estrutura organizacional
- Competências
- Horários de atendimento
- E outros critérios de transparência pública

## Tecnologias Utilizadas

- **Backend**: Python, Flask, Selenium, BeautifulSoup, Tesseract OCR
- **Frontend**: React, JavaScript, HTML, CSS

## Instalação

### Requisitos

- Python 3.8+
- Node.js 14+
- Google Chrome (para o Selenium)
- Tesseract OCR

### Configuração do Backend

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/sistema-pntp.git
cd sistema-pntp/backend

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

Configuração do Frontend
bash
Copiar

cd ../frontend
npm install
Uso
bash
Copiar

# Inicie o backend
cd backend
python app.py

# Em outro terminal, inicie o frontend
cd frontend
npm start
Licença
Este projeto está licenciado sob a Licença MIT.


### Criar um arquivo requirements.txt

Para facilitar a instalação das dependências:

```bash
# No diretório do backend, com o ambiente virtual ativado
pip freeze > requirements.txt