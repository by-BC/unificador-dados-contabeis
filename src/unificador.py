import os
import pandas as pd
from ofxparse import OfxParser
import re
from datetime import datetime

# Dicionário de Bancos (Baseado no seu mapeamento FID)
BANCOS_MAPEADOS = {
    '001': 'Banco do Brasil',
    '004': 'Banco do Nordeste',
    '074': 'Banco Safra',
    '104': 'Caixa Econômica Federal',
    '237': 'Bradesco',
    '382': 'Tribanco'
}

def extrair_cnpj(memo):
    """Busca um padrão de 14 dígitos no texto, ignora CPFs e aplica a máscara de CNPJ."""
    if not memo:
        return ""
    # Pega apenas os números da descrição
    numeros = re.sub(r'[^0-9]', '', memo)
    
    # Procura blocos exatos de 14 dígitos (ignorando se achar 11)
    if len(numeros) >= 14:
        match = re.search(r'\d{14}', numeros)
        if match:
            cnpj = match.group(0)
            # Aplica a máscara padrão: XX.XXX.XXX/XXXX-XX
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return ""

def determinar_tipo(tipo_ofx, valor):
    """Aplica a regra de ouro do seu mapeamento: o sinal do valor define o tipo real."""
    if float(valor) >= 0:
        return 'CREDITO'
    else:
        return 'DEBITO'

def formatar_data(data_ofx, banco_id):
    """Aplica a regra de data específica (BB usa AA, resto usa AAAA)"""
    if not data_ofx:
        return ""
    
    # O ofxparse já converte para objeto datetime do Python automaticamente
    if banco_id == '001': # Banco do Brasil (DD/MM/AA)
        return data_ofx.strftime('%d/%m/%y')
    else: # Restante (DD/MM/AAAA)
        return data_ofx.strftime('%d/%m/%Y')

def ofx_to_dataframe(caminho_arquivo):
    """Lê um arquivo OFX e converte para as regras da Analisegroup."""
    nome_arquivo = os.path.basename(caminho_arquivo)
    
    if not caminho_arquivo.lower().endswith('.ofx'):
        print(f"❌ Erro: {nome_arquivo} não é um arquivo OFX válido.")
        return None

    try:
        with open(caminho_arquivo, 'rb') as f:
            ofx = OfxParser.parse(f)
    except Exception as e:
        print(f"❌ Erro ao ler {nome_arquivo}: {e}")
        return None

    # Identificação do Banco
    banco_id = ofx.account.routing_number
    nome_banco = BANCOS_MAPEADOS.get(banco_id, "Banco não identificado")

    dados_extraidos = []

    for transacao in ofx.account.statement.transactions:
        valor = float(transacao.amount)
        
        linha = {
            'nome_arquivo': nome_arquivo,
            'data': formatar_data(transacao.date, banco_id),
            'banco': nome_banco,
            'valor': valor,
            'tipo': determinar_tipo(transacao.type, valor),
            'cnpj': extrair_cnpj(transacao.memo),
            'complemento_historico': transacao.memo if transacao.memo else transacao.id
        }
        dados_extraidos.append(linha)

    df = pd.DataFrame(dados_extraidos)
    return df

# --- ÁREA DE TESTE (EXECUÇÃO) ---
if __name__ == "__main__":
    pasta_inputs = os.path.join("data", "inputs")
    pasta_saida = "data"
    
    os.makedirs(pasta_inputs, exist_ok=True)
    os.makedirs(pasta_saida, exist_ok=True)
    
    arquivos = [f for f in os.listdir(pasta_inputs) if f.lower().endswith('.ofx')]
    
    if not arquivos:
        print("⚠️ Nenhum arquivo .ofx encontrado na pasta data/inputs.")
    else:
        todos_os_dados = [] # Lista para guardar as tabelas de todos os bancos
        
        for arquivo in arquivos:
            caminho = os.path.join(pasta_inputs, arquivo)
            print(f"🔄 Lendo: {arquivo}...")
            
            df_resultado = ofx_to_dataframe(caminho)
            
            if df_resultado is not None and not df_resultado.empty:
                todos_os_dados.append(df_resultado)
                print(f"   ✔️ {len(df_resultado)} transações extraídas.")

        # Se temos dados, vamos consolidar!
        if todos_os_dados:
            print("\n📦 Consolidando todos os arquivos...")
            
            # O poder do Pandas: junta todas as tabelas uma embaixo da outra
            df_consolidado = pd.concat(todos_os_dados, ignore_index=True)
            
            caminho_saida = os.path.join(pasta_saida, "analise_consolidado_final.csv")
            
            df_consolidado.to_csv(caminho_saida, sep=';', index=False, encoding='utf-8-sig')
            
            print(f"✅ SUCESSO! Arquivo ÚNICO gerado com {len(df_consolidado)} transações no total.")
            print(f"📂 Salvo em: {caminho_saida}")