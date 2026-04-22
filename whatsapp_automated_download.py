import asyncio
import os
import random
from datetime import datetime, timedelta
from camoufox.async_api import AsyncCamoufox

# Configurações (Caminho absoluto baseado no script para evitar system32)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, "whatsapp_session")
URL_REPORTS = "https://www.smsolucoesdigital.com.br/index.html#/relatorios/atendimentos"
FILENAME = "atendimento zap.xlsx"

async def run_automated_download():
    print("--- INICIANDO DOWNLOAD AUTOMATIZADO WHATSAPP (VIA SESSÃO) ---", flush=True)
    
    if not os.path.exists(SESSION_DIR):
        print(f"ERRO: Pasta de sessão não encontrada em {SESSION_DIR}.", flush=True)
        print("Por favor, execute 'python whatsapp_session_manager.py' primeiro para salvar seu login.", flush=True)
        return

    async with AsyncCamoufox(
        headless=False,
        persistent_context=True,
        user_data_dir=SESSION_DIR,
        viewport={'width': 1280, 'height': 720}
    ) as browser:
        # Camoufox com persistent_context já vem com uma página/contexto
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        print(f"Navegando para os relatórios: {URL_REPORTS}", flush=True)
        await page.goto(URL_REPORTS)
        await page.wait_for_load_state("networkidle")
        
        # Verifica se caiu na página de login (sessão expirou)
        if "login" in page.url:
            print("Sessão expirada ou não encontrada. Redirecionando para login manual...", flush=True)
            print("Execute o whatsapp_session_manager.py novamente.", flush=True)
            return

        print("Página de relatórios carregada. Configurando filtros...", flush=True)
        
        # Calcula datas (últimos 31 dias)
        ate = datetime.now()
        de = ate - timedelta(days=31)
        str_de = de.strftime("%d/%m/%Y")
        str_ate = ate.strftime("%d/%m/%Y")
        
        # Seletores (baseados no download_whatsapp.py e recon)
        sel_de = 'input[ng-model="filtro.dataCriacaoDe"]'
        sel_ate = 'input[ng-model="filtro.dataCriacaoAte"]'
        # Tenta múltiplos seletores para o botão de busca
        btn_buscar_selectors = ['button[title="Buscar"]', 'button:has-text("Buscar")', 'button[ng-click*="onSearch"]']
        
        try:
            # Aguarda campo de data
            print("Aguardando campos de data...", flush=True)
            await page.wait_for_selector(sel_de, timeout=30000)
            
            print(f"Filtrando de {str_de} até {str_ate}...", flush=True)
            
            # Preenche Data De
            await page.click(sel_de)
            await page.fill(sel_de, "")
            await page.type(sel_de, str_de, delay=100)
            await page.keyboard.press("Enter")
            
            await asyncio.sleep(1)
            
            # Preenche Data Ate
            await page.click(sel_ate)
            await page.fill(sel_ate, "")
            await page.type(sel_ate, str_ate, delay=100)
            await page.keyboard.press("Enter")
            
            await asyncio.sleep(2)
            
            # Clica em Buscar
            print("Localizando botão de BUSCAR...", flush=True)
            btn_buscar = None
            for sel in btn_buscar_selectors:
                try:
                    btn_buscar = await page.wait_for_selector(sel, timeout=5000)
                    if btn_buscar:
                        print(f"Botão Buscar encontrado: {sel}", flush=True)
                        break
                except: continue
            
            if btn_buscar:
                print("Clicando em BUSCAR...", flush=True)
                await btn_buscar.click()
            else:
                print("AVISO: Botão de BUSCAR não encontrado via seletores esperados.", flush=True)
            
            # Aguarda resultados
            print("Aguardando carregamento dos dados (10s)...", flush=True)
            await asyncio.sleep(10)
            
            # Procura o botão de exportação
            print("Localizando botão de exportação...", flush=True)
            selectors_export = [
                "button.bgm-teal", 
                "button.bgm-green",
                "button[ng-click*='exportRelatorio']",
                "button[ng-if*='DownloadReport']",
                "button:has(.zmdi-download)",
                "button[title*='Exportar']"
            ]
            
            btn_export = None
            for sel in selectors_export:
                try:
                    btn_export = await page.wait_for_selector(sel, timeout=3000, state="visible")
                    if btn_export:
                        print(f"Botão Exportação encontrado: {sel}", flush=True)
                        break
                except: continue
                
            if not btn_export:
                print("ERRO: Botão de exportação não encontrado após a busca.", flush=True)
                await page.screenshot(path="export_not_found.png")
                return

            # Gerencia o download
            print("Disparando download...", flush=True)
            async with page.expect_download(timeout=60000) as download_info:
                await btn_export.click()
                download = await download_info.value
                
                # Salva o arquivo
                save_path = os.path.join(BASE_DIR, FILENAME)
                await download.save_as(save_path)
                print(f"--- SUCESSO! Relatorio salvo em: {save_path} ---", flush=True)
                
        except Exception as e:
            print(f"Erro durante o processo: {e}", flush=True)
            await page.screenshot(path="automation_error.png")

        print("Finalizando robô...", flush=True)
        await asyncio.sleep(2)
        # Para persistent_context no Camoufox/Playwright, usamos close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_automated_download())
