# app.py
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os # Importar para usar variáveis de ambiente (se necessário, mas vamos usar st.secrets)

# --- 1. CONFIGURAÇÃO DA CONEXÃO COM SUPABASE ---

# Pega as credenciais do Supabase de st.secrets
# Nota: Você precisará configurar estas secrets no Streamlit Cloud
# (no painel de configurações do seu app)
@st.cache_resource
def init_connection():
    # As credenciais são lidas automaticamente do arquivo .streamlit/secrets.toml
    # que você deve configurar no Streamlit Cloud.
    # Exemplo:
    # [supabase]
    # url = "SUA_URL_SUPABASE"
    # key = "SUA_CHAVE_SUPABASE"
    try:
        url: str = st.secrets["supabase"]["url"]
        key: str = st.secrets["supabase"]["key"]
        
        # Cria e retorna o cliente Supabase
        supabase: Client = create_client(url, key)
        return supabase
    except KeyError:
        st.error("Erro de configuração: As credenciais do Supabase (url e key) não foram encontradas no arquivo secrets.toml.")
        return None
    except Exception as e:
        st.error(f"Erro ao inicializar a conexão com Supabase: {e}")
        return None

# Inicializa o cliente Supabase
supabase = init_connection()

# --- 2. FUNÇÃO PARA BUSCAR DADOS ---

# Usa st.cache_data para evitar múltiplas chamadas ao banco de dados
# O tempo de cache é de 10 minutos (600 segundos)
@st.cache_data(ttl=600)
def fetch_data(table_name: str):
    if supabase is None:
        return pd.DataFrame() # Retorna DataFrame vazio se a conexão falhou
        
    try:
        # Busca todos os dados da tabela
        response = supabase.table(table_name).select("*").execute()
        
        # Verifica se houve erro na resposta
        if response.data is None:
             st.warning(f"Nenhum dado encontrado na tabela '{table_name}'.")
             return pd.DataFrame()

        # Converte a lista de dicionários para um DataFrame do Pandas
        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados da tabela '{table_name}': {e}")
        st.warning("Verifique se o nome da tabela e as permissões RLS no Supabase estão corretas.")
        return pd.DataFrame()

# --- 3. INTERFACE DO STREAMLIT ---

st.title("Web App Streamlit + Supabase")
st.subheader("Exemplo de Conexão com PostgreSQL via Supabase")

# Nome da sua tabela no Supabase (MUDE ESTE NOME)
TABLE_NAME = "seus_dados_aqui" 

# Botão para carregar/recarregar os dados
if st.button(f"Carregar Dados da Tabela '{TABLE_NAME}'"):
    with st.spinner("Carregando dados..."):
        data_df = fetch_data(TABLE_NAME)

        if not data_df.empty:
            st.success(f"Dados da tabela '{TABLE_NAME}' carregados com sucesso!")
            st.dataframe(data_df)
            
            # Exibe algumas estatísticas
            st.write(f"Total de linhas: {len(data_df)}")
        else:
            st.warning("Não foi possível carregar os dados. Verifique a conexão e o nome da tabela.")

# Dica: Sempre exiba o status da conexão ou um placeholder
if supabase is not None:
    st.markdown("✅ Conexão com Supabase inicializada.")
else:
    st.markdown("❌ Conexão com Supabase pendente ou falhou. Verifique `secrets.toml`.")
