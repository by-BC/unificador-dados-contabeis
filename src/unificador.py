import pandas as pd
import os

def unificar_extratos():
    # Definindo os caminhos dos arquivos baseados na estrutura do projeto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_bb = os.path.join(base_dir, 'data', 'inputs', 'extrato_BB.csv')
    file_cef = os.path.join(base_dir, 'data', 'inputs', 'extrato_CEF.csv')
    output_file = os.path.join(base_dir, 'data', 'consolidado_final.csv')

    # Garantir que o diretório de saída existe
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 1. Ler os dois arquivos CSV
    df_bb = pd.read_csv(file_bb)
    df_cef = pd.read_csv(file_cef)

    # 2. Renomear as colunas para o padrão único: ['data', 'descricao', 'valor']
    df_bb = df_bb.rename(columns={
        'Data': 'data',
        'Lançamento': 'descricao',
        'Valor': 'valor'
    })

    df_cef = df_cef.rename(columns={
        'Dt_Movimento': 'data',
        'Historico': 'descricao',
        'Valor_BRL': 'valor'
    })

    # 3. Concatenar os DataFrames
    # Por que usar o método pd.concat() em vez de loops manuais?
    # O Pandas utiliza operações vetorizadas em C sob o capô. Iterar linha por linha 
    # (com for-loops) no Python é extremamente lento. O pd.concat() é altamente otimizado 
    # para unir estruturas de dados em bloco, resultando em um código muito mais limpo, 
    # legível e absurdamente mais rápido, especialmente com grandes volumes de dados contábeis.
    df_consolidado = pd.concat([df_bb, df_cef], ignore_index=True)

    # 4. Salvar o resultado no novo arquivo consolidado
    df_consolidado.to_csv(output_file, index=False)
    print(f"Arquivo consolidado criado com sucesso em: {output_file}")

if __name__ == '__main__':
    unificar_extratos()
