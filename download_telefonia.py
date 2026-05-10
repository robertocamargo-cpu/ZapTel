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

            # Configurar datas (Últimos 30 dias)
            hoje_dt = datetime.now()
            de_dt = hoje_dt - timedelta(days=30)
            str_de = de_dt.strftime("%d/%m/%Y")
            str_ate = hoje_dt.strftime("%d/%m/%Y")
            print(f"Buscando período solicitado: {str_de} até {str_ate}")

            # Abrir Filtro
            filter_is_visible = await page.is_visible('form#cdr-tenant-form')
            if not filter_is_visible:
                print("Abrindo painel de filtro...")
                await page.click('button.openFilter')
                await asyncio.sleep(2)
            
            # Aplicar filtros via digitação direta para maior confiabilidade
            print("Configurando daterangepicker via digitação...")
            daterange_input = page.locator('input.date-range-time')
            await daterange_input.click()
            await page.keyboard.press("Meta+A")
            await page.keyboard.press("Backspace")
            full_range = f"{str_de} 00:00 - {str_ate} 23:59"
            await daterange_input.type(full_range)
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
            await page.keyboard.press("Escape") # Garante que o picker fechou
            await asyncio.sleep(1)

            # Tenta com CURRENT primeiro
            print("Selecionando 'CURRENT' e buscando...")
            await page.evaluate("document.querySelector('select[name=\"CallRecordBillingTenant[record_selection]\"]').value = 'CURRENT'")
            await page.evaluate("document.querySelector('select[name=\"CallRecordBillingTenant[record_selection]\"]').dispatchEvent(new Event('change'))")
            await page.evaluate("document.querySelector('input[type=\"submit\"][value=\"Buscar\"]').click()")
            
            # Aguarda a tabela atualizar
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(8)
            
            no_results = await page.is_visible("text=No results found")
            if no_results:
                print("Nenhum resultado em CURRENT. Tentando ARCHIVE...")
                if not await page.is_visible('form#cdr-tenant-form'):
                    await page.click('button.openFilter')
                await page.evaluate("document.querySelector('select[name=\"CallRecordBillingTenant[record_selection]\"]').value = 'ARCHIVE'")
                await page.evaluate("document.querySelector('select[name=\"CallRecordBillingTenant[record_selection]\"]').dispatchEvent(new Event('change'))")
                await page.click('input[type="submit"][value="Buscar"]')
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(8)

            print("Busca concluída.")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(5)
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "debug_telefonia_resultados.png"), full_page=True)

            # FECHAR O PAINEL DE FILTRO
            print("Fechando painel de filtro...")
            await page.evaluate("""() => {
                const closeBtn = document.querySelector('a.displayFilterBox, button.openFilter');
                if (closeBtn && document.querySelector('form#cdr-tenant-form')?.offsetParent !== null) {
                    closeBtn.click();
                }
            }""")
            await asyncio.sleep(2)

            # Iniciar exportação
            print("Iniciando exportação...")
            export_toggle = page.locator('a#toggleOptions')
            await export_toggle.first.scroll_into_view_if_needed()
            await export_toggle.first.click(force=True)
            await asyncio.sleep(2)
            
            # Screenshot das opções
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "debug_telefonia_export_options.png"))
            
            print("Selecionando primeira opção de Exportação...")
            # Tenta clicar na primeira opção da lista que contenha "Export"
            export_option = page.locator('.dropdown-menu li:visible').first
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
