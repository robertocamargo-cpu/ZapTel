import pandas as pd
import json
import os
from datetime import datetime

# === CONFIGURAÇÃO DE CAMINHOS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === TELEFONIA ===
path_new = os.path.join(BASE_DIR, 'Tenant_CallRecordReport.xlsx')
path_hist = os.path.join(BASE_DIR, 'atendimento tel.xlsx')

df_new = pd.read_excel(path_new) if os.path.exists(path_new) else pd.DataFrame()

if os.path.exists(path_hist):
    try:
        path_backup = path_hist.replace('.xlsx', '_backup.xlsx')
        import shutil
        shutil.copy2(path_hist, path_backup)
        df_hist = pd.read_excel(path_hist)
        print(f"Lendo histórico: {path_hist} ({len(df_hist)} registros)")
    except Exception as e:
        print(f"Erro ao ler histórico: {e}. Iniciando novo.")
        df_hist = pd.DataFrame()
else:
    df_hist = pd.DataFrame()

# Concatena e remove duplicatas baseadas no ID Chamada
if not df_new.empty:
    print(f"Lendo novo relatório: {path_new} ({len(df_new)} registros)")
    if not df_hist.empty:
        df_tel = pd.concat([df_hist, df_new], ignore_index=True)
        df_tel = df_tel.drop_duplicates(subset=['ID Chamada'], keep='last')
    else:
        df_tel = df_new
else:
    df_tel = df_hist

# Salva o histórico acumulado (Backup físico) - MANTÉM TUDO PARA O RELATÓRIO
if not df_tel.empty:
    df_tel.to_excel(path_hist, index=False)
    print(f"Histórico atualizado e salvo: {len(df_tel)} registros totais.")

# Normalização de nomes
NAME_MAP = {
    'Arnaldo': 'Arnaldo Acerbi', 'Arnaldo César': 'Arnaldo Acerbi', 'Arnaldo Acerbi': 'Arnaldo Acerbi',
    'Aurora': 'Aurora Dutra', 'Aurora Dutra': 'Aurora Dutra',
    'Juliana': 'Juliana Sanches', 'Juliana Sanches': 'Juliana Sanches',
    'Paulo': 'Paulo Vinicius', 'Paulo Vinicius': 'Paulo Vinicius',
    'Poliane': 'Poliane Medeiros', 'Poliane Medeiros': 'Poliane Medeiros',
    'Angelita': 'Angelita Francisco', 'Angelita Francisco': 'Angelita Francisco',
    'Roberto': 'Roberto Camargo', 'Roberto Camargo': 'Roberto Camargo'
}

def normalize_name(name):
    if not name or pd.isna(name): return 'Sem atendente'
    n = str(name).strip()
    return NAME_MAP.get(n, n)

hoje_dt = datetime.now()
# WhatsApp mantém 60 dias para cobrir o mês anterior
limite_zap = (hoje_dt - pd.Timedelta(days=60)).strftime('%Y-%m-%d')

# Processamento Telefonia (SEM LIMITE DE 30 DIAS NO PROCESSAMENTO, USA TUDO QUE TEM)
if not df_tel.empty:
    # Conversão robusta de data para o formato brasileiro ou ISO
    # O format='%Y-%m-%d %H:%M:%S' ou dayfirst=True ajudam conforme o que vem do portal
    df_tel['data_dt'] = pd.to_datetime(df_tel['Tempo Início'], errors='coerce')
    
    outbound = df_tel[(df_tel['Direção Chamada'] == 'OUTBOUND') & (df_tel['Minuto da chamada'] > 0.30)].copy()
    outbound['nome_raw'] = outbound['Chamador'].str.replace(r' \d+', '', regex=True)
    outbound['nome'] = outbound['nome_raw'].apply(normalize_name)
    outbound['ramal'] = outbound['Chamador'].str.extract(r'(\d+)')
    outbound['data'] = outbound['data_dt'].dt.strftime('%Y-%m-%d')
    outbound['tempo_seg'] = (outbound['Minuto da chamada'] * 60).astype(int)
    
    # Remove registros onde a data falhou na conversão
    outbound = outbound.dropna(subset=['data'])
    
    tel_records = outbound[['nome', 'ramal', 'data', 'tempo_seg']].to_dict(orient='records')
    print(f"Telefonia Dashboard (Histórico Total): {len(tel_records)} registros.")
else:
    tel_records = []

# === WHATSAPP ===
path_zap = os.path.join(BASE_DIR, 'atendimento zap.xlsx')
zap_records = []
if os.path.exists(path_zap):
    df_zap = pd.read_excel(path_zap)
    col_data_zap = 'DATA'
    for c in ['DATA', 'DATACRIACAO', 'DATA CRIACAO']:
        if c in df_zap.columns:
            col_data_zap = c
            break
    
    df_zap['data_dt'] = pd.to_datetime(df_zap[col_data_zap], dayfirst=True, errors='coerce')
    df_zap['data'] = df_zap['data_dt'].dt.strftime('%Y-%m-%d')
    
    # Filtra 60 dias para WhatsApp
    df_zap = df_zap[df_zap['data'] >= limite_zap].dropna(subset=['data'])
    
    df_zap['ATENDENTE'] = df_zap['ATENDENTE'].fillna('Sem atendente')
    df_zap['atendente'] = df_zap['ATENDENTE'].apply(normalize_name)
    df_zap['STATUS'] = df_zap['STATUS'].fillna('DESCONHECIDO')
    
    zap_records = df_zap[['atendente', 'STATUS', 'data']].rename(
        columns={'STATUS': 'status'}
    ).to_dict(orient='records')
    print(f"WhatsApp Dashboard (60 dias): {len(zap_records)} registros.")

# === MOSTRUÁRIO ===
path_mostruario = os.path.join(BASE_DIR, 'mostruario.xlsx')
mostruario_records = []
if os.path.exists(path_mostruario):
    excel_mostruario = pd.ExcelFile(path_mostruario)
    mes_map = {
        'Janeiro': '01', 'Fevereiro': '02', 'Março': '03', 'Abril': '04',
        'Maio': '05', 'Junho': '06', 'Julho': '07', 'Agosto': '08',
        'Setembro': '09', 'Outubro': '10', 'Novembro': '11', 'Dezembro': '12'
    }
    for sheet in excel_mostruario.sheet_names:
        if sheet in mes_map:
            df_mes = pd.read_excel(path_mostruario, sheet_name=sheet, skiprows=1)
            if not df_mes.empty and 'Vendedor' in df_mes.columns:
                vendedores = df_mes['Vendedor'].dropna()
                data_iso = f"2026-{mes_map[sheet]}-01"
                for v in vendedores:
                    v_norm = normalize_name(v)
                    mostruario_records.append({'vendedor': v_norm, 'data': data_iso})
    print(f"Mostruário: {len(mostruario_records)} registros processados.")

# Range para o Dashboard (Dia 1 do mês passado até hoje)
if hoje_dt.month == 1:
    mes_passado = 12
    ano_passado = hoje_dt.year - 1
else:
    mes_passado = hoje_dt.month - 1
    ano_passado = hoje_dt.year

all_min = f"{ano_passado:04d}-{mes_passado:02d}-01"
all_max = hoje_dt.strftime('%Y-%m-%d')

result = {
    'telefonia': tel_records,
    'whatsapp': zap_records,
    'mostruario': mostruario_records,
    'date_range': {'min': all_min, 'max': all_max}
}

output_path = os.path.join(BASE_DIR, 'full_data.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False)

print(f"\nfull_data.json gerado. Range: {all_min} a {all_max}")
