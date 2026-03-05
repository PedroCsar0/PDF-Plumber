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
import base64
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
        # Inicia o cliente puxando a chave do cofre secreto do Streamlit
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        prompt = f"""
        Você é um analista sênior de regularização fundiária, especialista em direito imobiliário, contratos agrários e documentação (INCRA, CAR, CCIR, Matrículas).
        Abaixo está um texto extraído de um documento através de OCR. Ele pode conter lixo visual, erros de leitura e caracteres estranhos.
        
        Sua missão é identificar do que se trata o documento, limpar os erros pelo contexto e extrair os dados de forma impecável para a equipe de engenharia e agronomia.
        
        Estruture sua resposta preenchendo APENAS os blocos abaixo que fizerem sentido para o documento analisado (se uma informação não existir no texto, não invente, apenas escreva 'Não identificado' ou omita o campo):

        ### 1. Classificação do Documento
        - **Tipo Principal:** (Ex: Matrícula de Imóvel, Recibo do CAR, CCIR, Contrato de Arrendamento, Contrato de Compra e Venda, etc.)

        ### 2. Dados do Imóvel (Matrículas / INCRA / CCIR)
        - **Número da Matrícula e Comarca:**
        - **Denominação do Imóvel / Fazenda:**
        - **Área Total (hectares):**
        - **Código INCRA / Número CCIR:**
        - **Módulos Rurais / Módulos Fiscais / Fração Mínima:**

        ### 3. Dados Ambientais (CAR)
        - **Número do Recibo CAR:**
        - **Situação (Ativo, Pendente, etc.):**
        - **Área de Preservação Permanente (APP) / Reserva Legal:**

        ### 4. Proprietários e Qualificação das Partes
        - **Identificação Completa:** (É OBRIGATÓRIO extrair todos os nomes citados e seus respectivos documentos: CPFs, CNPJs, RGs, estado civil, cônjuge, profissão e domicílio).
        - **Condição Jurídica:** (Especifique claramente do lado de cada nome se a pessoa é: proprietário pleno, nua-proprietário, usufrutuário, comprador, vendedor, arrendador ou arrendatário).

        ### 5. Nuances Contratuais (Apenas para Contratos)
        - **Objeto do Contrato:**
        - **Valores e Condições de Pagamento:**
        - **Prazos e Vigência:**
        - **Penalidades, Multas e Cláusulas Especiais:**

        ### 6. Histórico e Ônus (Apenas para Matrículas)
        - **Histórico Resumido (Vendas/Doações/Desmembramentos):**
        - **Ônus e Restrições:** (Hipotecas, penhoras, alienações fiduciárias, usufrutos ativos ou extintos).

        Texto do OCR:
        ---
        {texto_ocr}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
        
    except Exception as e:
        erro_str = str(e).lower()
        # Verifica se o erro é de limite de cota (429) ou exaustão de recursos
        if "429" in erro_str or "quota" in erro_str or "exhausted" in erro_str:
            mensagem_limite = (
                "⚠️ **Limite de Análises Atingido!**\n\n"
                "O sistema de Inteligência Artificial atingiu o teto de segurança da cota gratuita.\n\n"
                "👉 **Se for o limite por minuto (10 documentos):** Aguarde cerca de 60 segundos e clique em 'Extrair texto' novamente.\n"
                "👉 **Se for o limite diário (250 documentos):** A cota da empresa esgotou por hoje. O acesso será renovado automaticamente amanhã!"
            )
            return mensagem_limite
        else:
            # Para outros erros técnicos aleatórios
            return f"❌ **Erro técnico inesperado ao conectar com a IA:** {e}"

# --- INTERFACE WEB (FRONTEND) ---
# Adicionado layout="centered" para otimizar o mobile
icone_personalizado = Image.open("logo_ark.png")

st.set_page_config(
    page_title="Ark DataMiner", 
    page_icon="icone_personalizado",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS CUSTOMIZADOS ---
st.markdown("""
    <style>

    /* 1. Traduz o texto "Drag and drop file here" */
    [data-testid*="Dropzone"] > div > div::before {
        content: "Arraste e solte o documento aqui" !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        display: block !important;
        color: inherit !important;
        margin-bottom: 5px !important;
    }
            
    /* 1. Encolhe o texto original em inglês até sumir */
    [data-testid*="Dropzone"] button {
        font-size: 0px !important;
    }

    /* 2. Escreve o texto em português por cima */
    [data-testid*="Dropzone"] button::after {
        content: "Procurar arquivo" !important;
        font-size: 14px !important; /* Retorna o tamanho da fonte ao normal */
        font-weight: 400 !important;
        color: #1E293B !important; /* Mantém a cor escura do seu tema */
        display: block !important;
    }
            
    /* Esconde o span original em inglês */
    [data-testid*="Dropzone"] > div > div > span,
    [data-testid*="Dropzone"] > div > div > small {
        display: none !important;
    }

    /* 2. Traduz o limite "Limit 200MB per file" */
    [data-testid*="Dropzone"] > div > div::after {
        content: "Limite de 200MB por arquivo • PDF" !important;
        font-size: 14px !important;
        color: gray !important;
        display: block !important;
    }
            
    /* Esconde o small original em inglês */
    [data-testid="stFileUploadDropzone"] div div small {
        display: none;
    }                

    /* Esconde o menu padrão e o rodapé do Streamlit para dar cara de App próprio */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Deixa os botões mais arredondados e com efeito Hover (animação fluida) */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s ease;
        border: 1px solid #4CAF50; /* Uma cor de borda moderna */
    }
    .stButton>button:hover {
        transform: scale(1.02); /* Cresce 2% ao passar o mouse */
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }
    
    /* Centraliza e estiliza a caixa de Upload */
    .stFileUploader {
        border-radius: 10px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)
# --------------------------------

# --- SISTEMA DE LOGIN SIMPLES ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    # Cria 3 colunas e usa a do meio para o login (efeito de centralização)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔒 Ark Group</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Área restrita. Insira a credencial.</p>", unsafe_allow_html=True)
        
        senha_digitada = st.text_input("", placeholder="Digite a senha de acesso...", type="password")
        
        if st.button("Entrar no Sistema", use_container_width=True):
            if senha_digitada == st.secrets["SENHA_ARK"]:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
                
    st.stop() # Bloqueia o resto da página
# --------------------------------
col_img, col_txt = st.columns([1, 8]) 

def carregar_imagem_local(caminho):
    with open(caminho, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded_string}"

img_base64 = carregar_imagem_local("logo_ark.png")

# Desenha a logo e o título perfeitamente alinhados, sem perder qualidade e sem clique
st.markdown(
    f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="{img_base64}" width="65" style="margin-right: 15px; pointer-events: none;">
        <h1 style="margin: 0; padding: 0;">Ark DataMiner</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("Faça o upload de um arquivo PDF (legível ou digitalizado). O sistema irá usar Inteligência Artificial para extrair os dados da matrícula.")

# Área de Upload
arquivo_upado = st.file_uploader("Documento PDF", type=["pdf"], label_visibility="collapsed")

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