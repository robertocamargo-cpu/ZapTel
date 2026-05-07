import asyncio
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

# Configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL_LOGIN = "https://portal-cloud.jrcpabx.com.br/index.php/site/login"
USERNAME = "Cliente_Roberto"
PASSWORD = "jc2001"
OUTPUT_DIR = BASE_DIR
FILENAME = "Tenant_CallRecordReport.xlsx"

async def download_report():
    async with async_playwright() as p:
        # Lançar navegador
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        try:
            # Adicionando lógica de retry para navegação inicial
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Acessando {URL_LOGIN} (Tentativa {attempt+1})...")
                    await page.goto(URL_LOGIN, wait_until="load", timeout=30000)
                    break
                except Exception as e:
                    if attempt == max_retries - 1: raise
                    print(f"Falha na navegação: {e}. Tentando novamente...")
                    await asyncio.sleep(5)

            # Login
            print("Realizando login...")
            await page.wait_for_selector('#username_admin_type', state="visible")
            await page.fill('#username_admin_type', USERNAME)
            await page.fill('#password_admin_type', PASSWORD)
            await page.click('button.btn-critical-primary')
            
            await page.wait_for_load_state("networkidle")
            print("Login realizado com sucesso.")

            # Navegar para relatórios detalhados com retry
            target_url = "https://portal-cloud.jrcpabx.com.br/index.php/0/tenant/callRecordBillingTenant/admin"
            for attempt in range(max_retries):
                try:
                    print(f"Navegando para Detalhado Chamadas (Tentativa {attempt+1})...")
                    await page.goto(target_url, wait_until="load", timeout=30000)
                    await page.wait_for_load_state("networkidle")
                    break
                except Exception as e:
                    if attempt == max_retries - 1: raise
                    print(f"Falha ao navegar para relatórios: {e}. Tentando novamente...")
                    await asyncio.sleep(5)
            
            print("Navegou para Detalhado Chamadas.")

            # Configurar datas (Hoje e Hoje - 1 mês)
            now = datetime.now()
            start_date = now - timedelta(days=90)
            date_str = f"{start_date.strftime('%Y-%m-%d')} 00:00 - {now.strftime('%Y-%m-%d')} 23:59"
            print(f"Filtrando período: {date_str}")

            # Abrir Filtro
            # Verifica se o painel de filtro já está visível para não fechá-lo acidentalmente
            filter_is_visible = await page.is_visible('form#cdr-tenant-form')
            if not filter_is_visible:
                print("Abrindo painel de filtro...")
                await page.wait_for_selector('button.openFilter', state="visible")
                await page.click('button.openFilter')
                await asyncio.sleep(2) # Aguarda painel abrir
            else:
                print("Painel de filtro já está aberto.")

            # Preencher data
            print(f"Preenchendo data: {date_str}")
            date_input = page.locator('input.date-range-time')
            await date_input.scroll_into_view_if_needed()
            await date_input.click() # Abre o picker
            await asyncio.sleep(2)
            
            # Garante que o foco está no input e limpa
            await page.keyboard.press("Control+a")
            await page.keyboard.press("Backspace")
            await asyncio.sleep(1)
            
            # Digita a data caractere por caractere para disparar eventos
            await page.keyboard.type(date_str, delay=100)
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
            
            # Clicar em Apply no date picker (essencial para daterangepicker)
            # Buscamos o botão dentro do widget do calendário que deve estar aberto
            apply_btn = page.locator('.daterangepicker:visible .applyBtn')
            if await apply_btn.count() > 0:
                print("Clicando no botão 'Apply' do calendário...")
                await apply_btn.click()
                await asyncio.sleep(1)
            else:
                print("Botão 'Apply' não encontrado ou não visível. Tentando prosseguir...")

            # Clicar em BUSCAR
            print("Clicando em BUSCAR...")
            # Usando seletor exato pelo valor para evitar outros botões 'btn-critical-primary'
            buscar_btn = page.locator('input[type="submit"][value="Buscar"]')
            await buscar_btn.wait_for(state="visible", timeout=10000)
            await buscar_btn.click()
            
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(5) # Espera extra para a tabela renderizar com os novos dados
            print("Busca realizada.")

            # Fechar painel de filtro (necessário para o Export aparecer)
            if await page.is_visible('form#cdr-tenant-form'):
                print("Fechando painel de filtro...")
                # Tenta clicar no botão "Back" ou no botão que fecha o filtro
                await page.locator('.displayFilterBox:visible').first.click()
                await asyncio.sleep(3)
            
            # Garante que o painel realmente fechou
            if await page.is_visible('form#cdr-tenant-form'):
                print("Tentando fechar filtro novamente via mouse...")
                await page.mouse.click(10, 10) # Clica em área neutra
                await asyncio.sleep(2)

            # Exportar
            print("Iniciando exportação...")
            # Aguarda o botão de opções estar presente
            export_toggle = page.locator('a#toggleOptions:visible')
            await export_toggle.first.wait_for(state="visible", timeout=15000)
            
            # Tenta clicar de forma robusta
            await export_toggle.first.scroll_into_view_if_needed()
            await export_toggle.first.click(force=True)
            await asyncio.sleep(2)
            
            # Tenta clicar em "EXPORT + Media" usando ID específico
            print("Selecionando opção EXPORT + Media...")
            export_option = page.locator('li#export-media-button:visible')
            await export_option.wait_for(state="visible", timeout=15000)
            
            async with page.expect_download() as download_info:
                await export_option.click(force=True)
            
            download = await download_info.value
            path = os.path.join(OUTPUT_DIR, FILENAME)
            await download.save_as(path)
            print(f"Relatório salvo em: {path}")

        except Exception as e:
            print(f"ERRO NO PROCESSO: {e}")
            error_path = os.path.join(OUTPUT_DIR, "error_debug.png")
            await page.screenshot(path=error_path, full_page=True)
            print(f"Screenshot salva em: {error_path}")
            # Salva também o código HTML para debug
            html_path = os.path.join(OUTPUT_DIR, "error_debug.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(await page.content())
            raise
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(download_report())
