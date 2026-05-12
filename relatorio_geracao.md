# Relatório de Geração do Dashboard ZapTel

## Visão Geral
Este documento descreve passo a passo o que foi feito para gerar o relatório exibido em `resumo_dashboard.html`.

## 1. Preparação do Ambiente
- **Sistema Operacional:** macOS (versão especificada pelo usuário).
- **Diretório de Trabalho:** `/Users/robertocamargo/programas/ZapTel`.
- **Dependências:**
  - Python 3.x
  - Bibliotecas listadas em `requirements.txt` (pandas, numpy, etc.)
  - Um *virtual environment* (`venv`) foi criado para isolar as dependências.

## 2. Scripts Principais
| Script | Função | Principais Etapas |
|--------|--------|-------------------|
| `download_telefonia.py` | Recupera arquivos de chamadas telefônicas a partir da API ou de arquivos CSV. | 1. Conecta à fonte de dados.<br>2. Faz download dos arquivos históricos (abril até a data atual). |
| `download_whatsapp.py` | (se aplicável) Baixa mensagens do WhatsApp para análise. | Similar ao script de telefonia, porém usando a API do WhatsApp. |
| `export_data.py` | Processa os arquivos brutos e gera arquivos CSV consolidados. | 1. Lê os arquivos baixados.<br>2. Aplica filtro de data **"primeiro dia do mês anterior até hoje"**.<br>3. Normaliza campos de data/hora.<br>4. Agrupa dados por período (Este Mês, Mês Passado). |
| `Atualizar_Dashboard.sh` | Automatiza a execução dos scripts acima e atualiza o HTML. | 1. Ativa o virtual environment.<br>2. Executa `download_telefonia.py`, `download_whatsapp.py` e `export_data.py`.<br>3. Copia/gera `resumo_dashboard.html` com os dados processados. |

## 3. Lógica de Filtro de Data
- Utilizamos a biblioteca `datetime` para calcular a data inicial:
  ```python
  from datetime import date, timedelta
  today = date.today()
  first_day_prev_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
  ```
- O filtro é aplicado em `export_data.py` para considerar somente registros entre `first_day_prev_month` e `today`.

## 4. Geração do HTML (`resumo_dashboard.html`)
- O script de exportação salva os resultados consolidados em arquivos CSV.
- O HTML lê esses CSV usando **JavaScript** (ou via template Jinja se for servidor) e preenche:
  - Contagem total de chamadas.
  - Tempo total de conversa.
  - Comparativo "Este Mês" vs "Mês Passado".
- O layout foi aprimorado com cores corporativas, tipografia Google Fonts (`Inter`) e micro‑animações para melhorar a percepção visual.

## 5. Execução Automática
- O usuário pode iniciar a atualização manualmente:
  ```bash
  cd /Users/robertocamargo/programas/ZapTel
  ./Atualizar_Dashboard.sh
  ```
- Para execução contínua, pode‑se criar um *cron job* que chama o script diariamente.

## 6. Validação
- Após a execução, abra `resumo_dashboard.html` em um navegador.
- Verifique se os valores exibidos correspondem aos dados dos CSV gerados em `data/`.
- Compare os totais de "Este Mês" e "Mês Passado" com os registros brutos para garantir a integridade.

## 7. Próximos Passos
- **Automação completa:** Integrar o script ao fluxo CI/CD para gerar o dashboard em produção.
- **Monitoramento:** Adicionar logs de execução e notificação por e‑mail em caso de falha.
- **Escalabilidade:** Suportar múltiplas fontes de dados (ex.: API de voz) sem alterar a lógica de filtro.

---
*Este documento foi criado automaticamente para registrar o processo de geração do relatório do dashboard ZapTel.*
