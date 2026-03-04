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
# Título personalizado para os seus sócios
st.set_page_config(page_title="PDF Plumber", page_icon="📄")
st.title("📄 Extrator de texto OCR")
st.markdown("Faça o upload de um PDF (legível ou digitalizado). O sistema irá extrair o texto.")

# Área de Upload
arquivo_upado = st.file_uploader("Arraste o PDF para aqui", type=["pdf"])

if arquivo_upado is not None:
    if st.button("Iniciar Extração", use_container_width=True):
        
        # Cria um "spinner" de carregamento animado
        with st.spinner("A analisar o documento..."):
            
            # Salva o ficheiro upado temporariamente no disco para o pdf2image conseguir ler
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(arquivo_upado.getvalue())
                caminho_temporario = tmp_file.name
                
            # Chama o seu motor de extração
            texto_final = extrair_texto_pdf(caminho_temporario)
            
            # Apaga o ficheiro temporário
            os.remove(caminho_temporario)
            
        st.success("Extração concluída com sucesso!")
        
        # Mostra o texto no ecrã para conferência rápida
        st.text_area("Texto Extraído (Pode copiar diretamente daqui):", value=texto_final, height=300)
        
        # Botão para descarregar o TXT
        nome_arquivo_txt = arquivo_upado.name.replace(".pdf", ".txt")
        st.download_button(
            label="Fazer download (TXT)",
            data=texto_final,
            file_name=nome_arquivo_txt,
            mime="text/plain",
            use_container_width=True
        )