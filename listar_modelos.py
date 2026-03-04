import google.generativeai as genai

# Coloque sua chave real aqui dentro das aspas
CHAVE_API = "AIzaSyDlfRG_SpOO7Q4qwo0rlpT5F2ZlYydJ-RU" 

genai.configure(api_key=CHAVE_API)

print("--- Modelos disponíveis para gerar texto na sua conta ---")

# Chama a função ListModels da API
for modelo in genai.list_models():
    # Filtra apenas os modelos que servem para gerar conteúdo (textos)
    if 'generateContent' in modelo.supported_generation_methods:
        print(f"Nome do Modelo: {modelo.name}")