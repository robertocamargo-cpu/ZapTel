import asyncio
import os
from playwright.async_api import async_playwright

# Configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, "whatsapp_session")
SHEET_ID = "19kbZQ0gvqsS-mCGPiq2FYK_EjNIvpkl-2J3r5wsupIE"
URL_EXPORT = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
FILENAME = "mostruario.xlsx"

async def download_mostruario():
    print("--- INICIANDO DOWNLOAD MOSTRUÁRIO ---")
    
    async with async_playwright() as p:
        if os.path.exists(SESSION_DIR):
            print(f"Usando sessão existente em: {SESSION_DIR}")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=SESSION_DIR,
                headless=True,
                accept_downloads=True
            )
        else:
            print("Sessão não encontrada. Iniciando navegador limpo...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(accept_downloads=True)

        page = context.pages[0] if context.pages else await context.new_page()

        try:
            print(f"Disparando download...")
            
            # Usamos expect_download ANTES do gatilho
            async with page.expect_download(timeout=60000) as download_info:
                try:
                    # O goto vai falhar se disparar um download direto, mas o expect_download vai capturar
                    await page.goto(URL_EXPORT, wait_until="commit") 
                except Exception as e:
                    if "Download is starting" in str(e):
                        print("Download iniciado detectado.")
                    else:
                        raise e

            download = await download_info.value
            save_path = os.path.join(BASE_DIR, FILENAME)
            await download.save_as(save_path)
            print(f"--- SUCESSO! Mostruário salvo em: {save_path} ---")

        except Exception as e:
            print(f"Erro durante o processo: {e}")
            raise
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(download_mostruario())
