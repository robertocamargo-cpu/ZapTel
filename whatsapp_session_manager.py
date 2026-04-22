import asyncio
import os
import sys
from camoufox.async_api import AsyncCamoufox

# Configurações (Caminho absoluto baseado no script para evitar system32)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, "whatsapp_session")
URL_LOGIN = "https://www.smsolucoesdigital.com.br/index.html#/login"

async def manage_session():
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)
        
    print(f"--- GERENCIADOR DE SESSÃO WHATSAPP (MODO ASSISTIDO) ---", flush=True)
    print(f"Os dados serão salvos em: {SESSION_DIR}", flush=True)
    
    # Iniciamos o Camoufox com resolução fixa para caber na tela
    # Iniciamos o Camoufox com viewport fixo
    async with AsyncCamoufox(
        headless=False,
        persistent_context=True,
        user_data_dir=SESSION_DIR,
        viewport={'width': 1280, 'height': 720}
    ) as browser:
        page = await browser.new_page()
        
        print(f"Abrindo portal: {URL_LOGIN}", flush=True)
        await page.goto(URL_LOGIN)
        
        print("\n" + "="*60)
        print("AÇÃO NECESSÁRIA:")
        print("1. No navegador que abriu, faça o login manualmente.")
        print("2. Resolva o reCAPTCHA (Não sou um robô).")
        print("3. Após entrar no Dashboard, VOLTE AQUI no terminal.")
        print("4. Pressione ENTER para fechar o navegador e salvar a sessão.")
        print("="*60 + "\n")
        
        # Espera o usuário pressionar Enter no terminal
        # Nota: sys.stdin.read() ou similar em async pode ser chato,
        # mas como estamos em um script de console simples, usaremos um loop ou input.
        await asyncio.to_thread(input, "Pressione [ENTER] quando estiver logado para salvar e sair...")
        
        print("Salvando e fechando...", flush=True)
        await browser.stop()
        print("Pronto! Agora você pode usar o script de download automático.", flush=True)

if __name__ == "__main__":
    asyncio.run(manage_session())
