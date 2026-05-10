import asyncio
import os
import random
from datetime import datetime, timedelta
import calendar
import pandas as pd
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
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await page.goto(URL_REPORTS, wait_until="load", timeout=60000)
                await page.wait_for_load_state("networkidle")
                break
            except Exception as e:
                if attempt == max_retries - 1: raise
                print(f"Falha na navegação: {e}. Tentando novamente...", flush=True)
                await asyncio.sleep(5)
        
        # Verifica se caiu na página de login (sessão expirou)
        if "login" in page.url:
            print("Sessão expirada ou não encontrada. Redirecionando para login manual...", flush=True)
            print("Execute o whatsapp_session_manager.py novamente.", flush=True)
            return

        print("Página de relatórios carregada. Configurando filtros...", flush=True)
        
        # Helper function to get the date ranges (2 months approx 60 days)
        def get_2_months_ranges():
            now = datetime.now()
            ranges = []
            # Mês 1 (Atual)
            start_m1 = datetime(now.year, now.month, 1)
            end_m1 = now
            # Adiciona 1 dia para não perder as transações de hoje à tarde/noite
            end_m1_plus_1 = end_m1 + timedelta(days=1)
            ranges.append((start_m1.strftime("%d/%m/%Y"), end_m1_plus_1.strftime("%d/%m/%Y")))
            # Mês 2 (Anterior)
            end_m2 = start_m1 - timedelta(days=1)
            start_m2 = datetime(end_m2.year, end_m2.month, 1)
            ranges.append((start_m2.strftime("%d/%m/%Y"), end_m2.strftime("%d/%m/%Y")))
            return ranges

        date_ranges = get_2_months_ranges()
        downloaded_files = []

        # Seletores
        sel_de = 'input[ng-model="filtro.dataCriacaoDe"]'
        sel_ate = 'input[ng-model="filtro.dataCriacaoAte"]'
        btn_buscar_selectors = ['button[title="Buscar"]', 'button:has-text("Buscar")', 'button[ng-click*="onSearch"]']
        selectors_export = [
            "button.bgm-teal", 
            "button.bgm-green",
            "button[ng-click*='exportRelatorio']",
            "button[ng-if*='DownloadReport']",
            "button:has(.zmdi-download)",
            "button[title*='Exportar']"
        ]

        try:
            # Aguarda os campos estarem visíveis inicialmente
            await page.wait_for_selector(sel_de, timeout=30000)

            for i, (str_de, str_ate) in enumerate(date_ranges):
                print(f"--- Processando Mês {i+1}/{len(date_ranges)}: de {str_de} até {str_ate} ---", flush=True)
                
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
                            break
                    except: continue
                
                if btn_buscar:
                    print("Clicando em BUSCAR...", flush=True)
                    await btn_buscar.click()
                else:
                    print("AVISO: Botão de BUSCAR não encontrado via seletores esperados.", flush=True)
                
                # Aguarda carregamento
                print("Aguardando carregamento dos dados (10s)...", flush=True)
                await asyncio.sleep(10)
                
                # Clica em Exportar
                print("Localizando botão de exportação...", flush=True)
                btn_export = None
                for sel in selectors_export:
                    try:
                        btn_export = await page.wait_for_selector(sel, timeout=3000, state="visible")
                        if btn_export:
                            break
                    except: continue
                    
                if not btn_export:
                    print(f"ERRO: Botão de exportação não encontrado para o mês {i+1}.", flush=True)
                    await page.screenshot(path=f"export_not_found_m{i+1}.png")
                    continue

                # Download
                print("Disparando download...", flush=True)
                async with page.expect_download(timeout=60000) as download_info:
                    await btn_export.click()
                    download = await download_info.value
                    
                    temp_filename = f"zap_temp_m{i+1}.xlsx"
                    save_path = os.path.join(BASE_DIR, temp_filename)
                    await download.save_as(save_path)
                    print(f"Relatório temporário salvo: {save_path}", flush=True)
                    downloaded_files.append(save_path)
                
                # Um pequeno delay entre as buscas
                await asyncio.sleep(3)

            # --- CONSOLIDAR RELATÓRIOS ---
            if downloaded_files:
                print("--- Consolidando relatórios ---", flush=True)
                all_dataframes = []
                for file_path in downloaded_files:
                    try:
                        df = pd.read_excel(file_path)
                        all_dataframes.append(df)
                    except Exception as df_e:
                        print(f"Erro ao ler {file_path}: {df_e}")
                
                if all_dataframes:
                    df_final = pd.concat(all_dataframes, ignore_index=True)
                    final_path = os.path.join(BASE_DIR, FILENAME)
                    df_final.to_excel(final_path, index=False)
                    print(f"--- SUCESSO! Relatório consolidado salvo em: {final_path} ---", flush=True)
                
                # Limpeza dos temporários
                for file_path in downloaded_files:
                    if os.path.exists(file_path):
                        os.remove(file_path)
            else:
                print("Nenhum relatório foi baixado com sucesso.", flush=True)

        except Exception as e:

            print(f"Erro durante o processo: {e}", flush=True)
            await page.screenshot(path="automation_error.png")

        print("Finalizando robô...", flush=True)
        await asyncio.sleep(2)
        # Para persistent_context no Camoufox/Playwright, usamos close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_automated_download())
