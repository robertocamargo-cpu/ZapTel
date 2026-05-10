#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
echo "--- INICIANDO ATUALIZAÇÃO DO DASHBOARD ---"

echo "1/3 Baixando dados da Telefonia..."
python3 download_telefonia.py

echo "2/3 Baixando dados do WhatsApp..."
python3 whatsapp_automated_download.py

echo "3/3 Processando dados finais..."
python3 export_data.py

echo "--- SUCESSO! ---"
echo "Abrindo o Dashboard..."
python3 visualizar_dashboard.py
