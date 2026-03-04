import os
import cv2
import numpy as np
from PIL import Image
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import streamlit as st
import tempfile
import re
from google import genai

# --- FUNÇÕES DO MOTOR DE OCR ---

def alinhar_imagem(img_cv):
    gray = cv2.bitwise_not(img_cv)
    coords = np.column_stack(np.where(gray > 0))
    angulo = cv2.minAreaRect(coords)[-1]

    if angulo < -45:
        angulo = -(90 + angulo)
    else:
        angulo = -angulo

    if abs(angulo) < 0.5:
        return img_cv

    (h, w) = img_cv.shape[:2]
    centro = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(centro, angulo, 1.0)
    imagem_rotacionada = cv2.warpAffine(img_cv, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return imagem_rotacionada    

def limpar_imagem_para_ocr(imagem_pil):
    img_cv = np.array(imagem_pil)
    img_gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    img_reta = alinhar_imagem(img_gray)
    img_sem_ruido = cv2.medianBlur(img_reta, 3)
    _, img_bin = cv2.threshold(img_sem_ruido, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(img_bin)

def limpar_texto_sujo(texto):
    texto = re.sub(r'[-.=]+', ' ', texto)
    texto = re.sub(r'C[IYU]RG', 'CI/RG', texto)
    texto = re.sub(r'[\|«»\[\]]', '', texto)
    texto = re.sub(r'([^\.])\n', r'\1 ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

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
            
    return limpar_texto_sujo(texto_completo)

def estruturar_dados_com_gemini(texto_ocr):
    try:
        # Inicia o cliente novo puxando a chave do cofre secreto do Streamlit
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        prompt = f"""
        Você é um especialista em direito imobiliário e analista de cartório.
        Abaixo está um texto extraído de uma matrícula de imóvel através de um sistema de OCR. O texto contém muitos erros de leitura, lixo visual, caracteres estranhos e erros de formatação.
        
        Sua missão é ler esse texto sujo, ignorar o lixo e extrair os dados reais em um formato limpo, resumido e fácil de ler para uma equipe de engenharia e agronomia.
        
        Por favor, estruture a resposta com os seguintes tópicos (se a informação não existir, escreva 'Não identificado'):
        - **Número da Matrícula:**
        - **Comarca / Cidade:**
        - **Área Total (em hectares):**
        - **Proprietários Atuais:**
        - **Histórico Resumido (Vendas/Doações):**
        - **Ônus / Observações (Hipoteca, Usufruto, Reserva Legal, etc):**

        Texto do OCR:
        ---
        {texto_ocr}
        """
        
        # Chama o modelo novo (gemini-2.5-flash) usando a sintaxe atualizada
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Erro ao processar com a IA: {e}"

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
            
        st.success("OCR concluído! Passando para a Inteligência Artificial...")
        
        # Aqui acontece a mágica: enviamos o texto sujo para o Gemini
        with st.spinner("A IA está estruturando os dados da matrícula..."):
            texto_estruturado = estruturar_dados_com_gemini(texto_final)
            
        # Mostra o resultado final mastigado na tela
        st.markdown("### Resumo Inteligente da Matrícula")
        st.markdown(texto_estruturado)
        
        # Botões de Download
        nome_arquivo_txt = arquivo_upado.name.replace(".pdf", ".txt")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Baixar Resumo da IA",
                data=texto_estruturado,
                file_name=f"RESUMO_{nome_arquivo_txt}",
                mime="text/plain",
                use_container_width=True 
            )
            
        with col2:
            st.download_button(
                label="🗄️ Baixar OCR Bruto",
                data=texto_final,
                file_name=f"BRUTO_{nome_arquivo_txt}",
                mime="text/plain",
                use_container_width=True 
            )
        
        with st.expander("Ver texto bruto extraído pelo OCR"):
            st.text_area("Texto com sujeira:", value=texto_final, height=250)