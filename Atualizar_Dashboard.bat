@echo off
setlocal
cd /d "%~dp0"
echo --- INICIANDO ATUALIZAÇÃO DO DASHBOARD ---

echo 1/3 Baixando dados da Telefonia...
python download_telefonia.py

echo 2/3 Baixando dados do WhatsApp...
python whatsapp_automated_download.py

echo 3/3 Processando dados finais...
python export_data.py

echo --- SUCESSO! ---
echo Abrindo o Dashboard...
start python visualizar_dashboard.py
pause
