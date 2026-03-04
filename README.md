# 📄 PDF Plumber - Analista Fundiário e Extrator OCR

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web_App-FF4B4B.svg)
![Tesseract](https://img.shields.io/badge/Tesseract-OCR-green.svg)
![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-8A2BE2.svg)

Uma ferramenta web interna desenvolvida para a **Ark Group** com o objetivo de automatizar a extração, limpeza e estruturação de dados de documentos fundiários (Matrículas de Imóveis, Recibos de CAR, CCIR, Contratos de Arrendamento, etc.) em formato PDF.

O sistema atua em duas frentes: primeiro, utiliza Visão Computacional (OpenCV) e OCR (Tesseract) para extrair o texto bruto de documentos escaneados. Em seguida, aciona a Inteligência Artificial Generativa (Google Gemini) para interpretar o contexto jurídico, corrigir erros de leitura e devolver os dados perfeitamente mastigados e estruturados para a equipe.

---

## Funcionalidades

- **Leitura Híbrida (Nativa/OCR):** Tenta extrair o texto de forma nativa primeiro. Se detectar que o PDF é uma imagem, aciona automaticamente o motor OCR.
- **Visão Computacional Avançada:** Utiliza OpenCV para alinhar páginas tortas (*Deskew*), remover ruídos/sujeira do scanner (*Denoise*) e aplicar binarização (*Thresholding* de Otsu), otimizando a leitura de documentos antigos ou amarelados.
- **Filtro RegEx:** Varredura em Python para limpar ruídos visuais de cartório (linhas pontilhadas, caracteres especiais) antes de acionar a IA.
- **Análise Inteligente (Gemini 2.5 Flash):** A IA lê o texto sujo, identifica o tipo de documento e estrutura tópicos cruciais como: dados do imóvel, áreas (hectares), histórico de ônus, nuances contratuais e qualificação completa das partes (RG, CPF e condição jurídica).
- **Proteção de Cota (Login):** Interface protegida por senha para evitar o esgotamento dos limites da API por robôs ou usuários não autorizados.

---

## Acesso Rápido (Cloud)

A aplicação está hospedada na nuvem e pode ser acessada de qualquer dispositivo (computador ou celular), sem necessidade de instalação:

🔗 **[Acessar o Analista PDF Plumber](https://pdf-plumber.streamlit.app/)**
*(Acesso restrito a usuários com a credencial da Ark Group).*

---

## 🛠️ Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/) - Framework para a interface web responsiva.
- [Google GenAI SDK](https://pypi.org/project/google-genai/) - Integração com o modelo Gemini 2.5 Flash.
- [pdfplumber](https://github.com/jsvine/pdfplumber) - Extração de texto em PDFs nativos.
- [pytesseract](https://pypi.org/project/pytesseract/) - Motor de OCR (Tesseract).
- [OpenCV](https://opencv.org/) - Tratamento de imagens pré-OCR.
- [pdf2image](https://pypi.org/project/pdf2image/) - Conversão de páginas PDF em imagens.

---

## Como rodar o projeto localmente (Desenvolvedores)

Se precisar rodar a aplicação na sua própria máquina para testes ou modificações, siga os passos abaixo:

### 1. Pré-requisitos de Sistema (Windows)
Antes de instalar as bibliotecas Python, o seu sistema precisa ter os binários destas duas ferramentas instalados:
- **Tesseract OCR:** [Download aqui](https://github.com/UB-Mannheim/tesseract/wiki). Instale e certifique-se de instalar o pacote de idioma Português (`por`).
- **Poppler:** Necessário para o `pdf2image`. [Download aqui](https://github.com/oschwartz10612/poppler-windows/releases/). Adicione a pasta `bin` às variáveis de ambiente do Windows.

### 2. Configuração do Cofre de Chaves (Secrets)
O sistema exige chaves de autenticação para rodar. Crie uma pasta chamada `.streamlit` na raiz do projeto e, dentro dela, um arquivo chamado `secrets.toml` com o seguinte formato:
```toml
GEMINI_API_KEY = "sua_chave_do_google_ai_studio_aqui"
SENHA_ARK = "senha_de_acesso_desejada"
```

### 3. Instalação das Bibliotecas
Clone o repositório e instale as dependências:
```bash
git clone [https://github.com/PedroCsar0/PDF-Plumber.git](https://github.com/PedroCsar0/PDF-Plumber.git)
cd PDF-Plumber
pip install -r requirements.txt
```
### 4. Executar a Aplicação
Rode o comando abaixo no terminal para iniciar o servidor local:
```bash
streamlit run app.py
```
---
#### 🔒 Privacidade
Este é um repositório da Ark Group. Os arquivos PDF submetidos na aplicação são processados temporariamente na memória do servidor e eliminados imediatamente após a extração, garantindo a total confidencialidade dos dados.

Desenvolvido por Pedro César Vanzela