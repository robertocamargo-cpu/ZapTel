import pandas as pd
import json
import os

# === CONFIGURAÇÃO DE CAMINHOS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === TELEFONIA ===
# Tenta carregar o relatório baixado pela automação, caso contrário usa o anterior
file_tel = os.path.join(BASE_DIR, 'Tenant_CallRecordReport.xlsx')
if not os.path.exists(file_tel):
    # Procura por qualquer arquivo que comece com Tenant_CallRecordReport e pegue o primeiro
    search_dir = BASE_DIR
    found = [f for f in os.listdir(search_dir) if f.startswith('Tenant_CallRecordReport')]
    if found:
        file_tel = os.path.join(search_dir, found[0])
    else:
        file_tel = os.path.join(BASE_DIR, 'atendimento tel.xlsx')

df_tel = pd.read_excel(file_tel)

ramal_nome = {
    1000: 'Roberto', 1001: 'Ana Helena', 1002: 'Paulo', 1003: 'Arnaldo',
    1004: 'Alessandra', 1005: 'Juliana', 1006: 'Angelita Francisco', 1007: 'Fernando',
    1008: 'Aurora', 1010: 'Vinicius', 1012: 'Poliane',
}

outbound = df_tel[(df_tel['Direção Chamada'] == 'OUTBOUND') & (df_tel['Minuto da chamada'] > 0.30)].copy()
outbound['nome'] = outbound['Origem'].map(ramal_nome).fillna('Desconhecido')
outbound['ramal'] = outbound['Origem'].astype(int)
outbound['data'] = pd.to_datetime(outbound['Tempo Início']).dt.strftime('%Y-%m-%d')
outbound['tempo_seg'] = (outbound['Minuto da chamada'] * 60).astype(int)

tel_records = outbound[['nome', 'ramal', 'data', 'tempo_seg']].to_dict(orient='records')

# Descobrir range de datas
tel_dates = pd.to_datetime(outbound['Tempo Início'])
print(f"Telefonia: {tel_dates.min()} a {tel_dates.max()}")

# === WHATSAPP ===
path_zap = os.path.join(BASE_DIR, 'atendimento zap.xlsx')
if os.path.exists(path_zap):
    # Usando engine openpyxl para maior compatibilidade se necessário
    df_zap = pd.read_excel(path_zap)
    
    # Identifica a coluna de data (DATA no formato padrão do SMBOT)
    # Tenta 'DATA', depois 'DATACRIACAO', depois 'DATACRIACAO'
    col_data_zap = 'DATA'
    for c in ['DATA', 'DATACRIACAO', 'DATA CRIACAO']:
        if c in df_zap.columns:
            col_data_zap = c
            break
    
    print(f"WhatsApp colunas: {list(df_zap.columns)}")
    print(f"WhatsApp DATA ({col_data_zap}) sample: {df_zap[col_data_zap].head(2).tolist()}")
    
    # Otimiza a conversão de data usando dayfirst=True para formato brasileiro DD/MM/YYYY
    df_zap['data_dt'] = pd.to_datetime(df_zap[col_data_zap], dayfirst=True, errors='coerce')
    df_zap['data'] = df_zap['data_dt'].dt.strftime('%Y-%m-%d')
    
    df_zap['ATENDENTE'] = df_zap['ATENDENTE'].fillna('Sem atendente')
    df_zap['STATUS'] = df_zap['STATUS'].fillna('DESCONHECIDO')
    
    # Remove linhas onde a data não pôde ser convertida
    df_zap = df_zap.dropna(subset=['data'])
    
    zap_records = df_zap[['ATENDENTE', 'STATUS', 'data']].rename(
        columns={'ATENDENTE': 'atendente', 'STATUS': 'status'}
    ).to_dict(orient='records')
    
    zap_dates = df_zap['data_dt']
    print(f"WhatsApp: {zap_dates.min()} a {zap_dates.max()} ({len(zap_records)} registros)")
else:
    print("AVISO: Arquivo de WhatsApp não encontrado em:", path_zap)
    zap_records = []
    zap_dates = pd.Series([pd.Timestamp.now()]) # Fallback

# Pegar range geral
all_min = min(tel_dates.min(), zap_dates.min()).strftime('%Y-%m-%d')
all_max = max(tel_dates.max(), zap_dates.max()).strftime('%Y-%m-%d')

result = {
    'telefonia': tel_records,
    'whatsapp': zap_records,
    'date_range': {'min': all_min, 'max': all_max}
}

# Define o caminho de saída para a pasta (mesmo diretório do script)
output_path = os.path.join(BASE_DIR, 'full_data.json')

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False)

print(f"\nfull_data.json gerado em: {output_path}")
print(f"{len(tel_records)} registros telefonia, {len(zap_records)} registros whatsapp")
print(f"Range: {all_min} a {all_max}")
