# 📄 PDF Plumber - Extrator OCR

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web_App-FF4B4B.svg)
![Tesseract](https://img.shields.io/badge/Tesseract-OCR-green.svg)

Uma ferramenta web interna desenvolvida para a **Ark Group** com o objetivo de automatizar a extração de texto de documentos fundiários (matrículas de imóveis, contratos, etc.) em formato PDF.

O sistema utiliza Inteligência Artificial para identificar se o PDF possui uma camada de texto nativa ou se é um documento digitalizado (imagem), aplicando pré-processamento de imagem e reconhecimento ótico de caracteres (OCR) quando necessário.

---

## Funcionalidades

- **Leitura Inteligente:** Tenta extrair o texto de forma nativa primeiro (mais rápido).
- **Fallback para OCR:** Se detetar que o PDF é uma imagem (menos de 50 caracteres de texto nativo), aciona automaticamente o motor OCR.
- **Pré-processamento com OpenCV:** Binarização e limpeza da imagem (tons de cinza e *Thresholding* de Otsu) para maximizar a precisão da leitura de documentos antigos ou amarelados.
- **Interface Web Simples:** Upload e download de ficheiros com apenas um clique através de uma interface construída em Streamlit.

---

## Acesso Rápido (Cloud)

A aplicação está hospedada na nuvem e pode ser acedida de qualquer dispositivo (computador ou telemóvel), sem necessidade de instalação:

🔗 **[Aceder ao Extrator PDF Plumber](https://pdf-plumber.streamlit.app/)**

---

## 🛠️ Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/) - Framework para a interface web.
- [pdfplumber](https://github.com/jsvine/pdfplumber) - Extração de texto em PDFs nativos.
- [pytesseract](https://pypi.org/project/pytesseract/) - Motor de OCR (Tesseract).
- [OpenCV](https://opencv.org/) - Tratamento de imagens pré-OCR.
- [pdf2image](https://pypi.org/project/pdf2image/) - Conversão de páginas PDF em imagens.

---

## 💻 Como rodar o projeto localmente (Para Desenvolvedores)

Se precisar de correr a aplicação na sua própria máquina para testes ou modificações, siga os passos abaixo:

### 1. Pré-requisitos de Sistema (Windows)
Antes de instalar as bibliotecas Python, o seu sistema precisa de ter os binários destas duas ferramentas instalados:
- **Tesseract OCR:** [Download aqui](https://github.com/UB-Mannheim/tesseract/wiki). Instale e certifique-se de instalar o pacote de idioma Português (`por`).
- **Poppler:** Necessário para o `pdf2image`. [Download aqui](https://github.com/oschwartz10612/poppler-windows/releases/). Adicione a pasta `bin` às variáveis de ambiente do Windows.

### 2. Instalação das Bibliotecas
Clone o repositório e instale as dependências:

```bash
git clone [https://github.com/PedroCsar0/PDF-Plumber.git](https://github.com/PedroCsar0/PDF-Plumber.git)
cd PDF-Plumber
pip install -r requirements.txt
```
3. Executar a Aplicação
Rode o comando abaixo no terminal para iniciar o servidor local:

```bash
streamlit run app.py
```

A aplicação ficará disponível no seu navegador em http://localhost:8501.

🔒 Privacidade
Este é um repositório da Ark Group. Os arquivos PDF submetidos na aplicação são processados temporariamente na memória do servidor e eliminados imediatamente após a extração, garantindo a total confidencialidade de dados.

---

Desenvolvido por Pedro César Vanzela



