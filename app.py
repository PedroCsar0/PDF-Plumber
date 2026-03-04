import os
import cv2
import numpy as np
from PIL import Image
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import streamlit as st
import tempfile

# --- FUNÇÕES DO MOTOR DE OCR ---
def limpar_imagem_para_ocr(imagem_pil):
    img_cv = np.array(imagem_pil)
    img_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    _, img_bin = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(img_bin)

def extrair_texto_pdf(caminho_pdf):
    texto_completo = ""
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto_extraido = pagina.extract_text()
                if texto_extraido:
                    texto_completo += texto_extraido + "\n"
    except Exception as e:
        st.warning(f"Aviso na leitura nativa: {e}")
    
    # Se o texto for muito curto, aciona o OCR
    if len(texto_completo.strip()) < 50:
        texto_completo = "" # Limpa o lixo nativo
        try:
            paginas_imagem = convert_from_path(caminho_pdf, dpi=300)
            config_tesseract = r'--oem 3 --psm 6'
            
            # Barra de progresso visual
            progress_bar = st.progress(0)
            total_pags = len(paginas_imagem)
            
            for i, imagem in enumerate(paginas_imagem):
                # Atualiza a barra de progresso
                progress_bar.progress((i + 1) / total_pags, text=f"Processando página {i+1} de {total_pags} com IA...")
                
                imagem_limpa = limpar_imagem_para_ocr(imagem)
                texto_ocr = pytesseract.image_to_string(imagem_limpa, lang='por', config=config_tesseract)
                texto_completo += texto_ocr + "\n"
                
            progress_bar.empty() # Esconde a barra ao terminar
            
        except Exception as e:
             st.error(f"Erro no OCR: {e}")
            
    return texto_completo

# --- INTERFACE WEB (FRONTEND) ---
# Adicionado layout="centered" para otimizar o mobile
st.set_page_config(
    page_title="PDF Plumber", 
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("📄 PDF Plumber - Extrator de texto OCR")
st.markdown("Faça o upload de um arquivo PDF (legível ou digitalizado). O sistema irá usar Inteligência Artificial para extrair o texto.")

# Área de Upload
arquivo_upado = st.file_uploader("Arraste o PDF aqui", type=["pdf"])

if arquivo_upado is not None:
    if st.button("Extrair texto", use_container_width=True):
        
        with st.spinner("Analisando o documento..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(arquivo_upado.getvalue())
                caminho_temporario = tmp_file.name
                
            texto_final = extrair_texto_pdf(caminho_temporario)
            os.remove(caminho_temporario)
            
        st.success("Extração concluída com sucesso!")
        
        # AJUSTE MOBILE 1: Colocar o botão de Download ANTES do texto
        nome_arquivo_txt = arquivo_upado.name.replace(".pdf", ".txt")
        st.download_button(
            label="Baixar arquivo .TXT",
            data=texto_final,
            file_name=nome_arquivo_txt,
            mime="text/plain",
            use_container_width=True # Faz o botão ocupar a largura toda no celular
        )
        
        # AJUSTE MOBILE 2: Esconder o texto longo num Expander
        with st.expander("Ver texto extraído na tela"):
            st.text_area("Copie o texto abaixo:", value=texto_final, height=250)