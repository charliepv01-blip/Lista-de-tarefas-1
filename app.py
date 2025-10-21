# app.py
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os 

# --- CONFIGURAÇÃO DA CONEXÃO COM SUPABASE ---

# Pega as credenciais do Supabase de st.secrets
# st.cache_resource garante que a conexão só seja inicializada uma vez.
@st.cache_resource
def init_connection():
    try:
        # Credenciais lidas do secrets.toml (local) ou Secrets (Streamlit Cloud)
        url: str = st.secrets["supabase"]["https://jiuacegblmqcpwiwowds.supabase.co"]
        key: str = st.secrets["supabase"]["sb_publishable_Q5_f3mZME4y_7gMxs1IoBA_u1WImXiR"]
        
        supabase: Client = create_client(url, key)
        return supabase
    except KeyError:
        st.error("Erro de configuração: As credenciais do Supabase (url e key) não foram encontradas.")
        return None
    except Exception as e:
        st.error(f"Erro ao inicializar a conexão com Supabase: {e}")
        return None

supabase = init_connection()

# --- FUNÇÃO EXEMPLO PARA BUSCAR DADOS ---
# Usada para demonstração ou desenvolvimento inicial
@st.cache_data(ttl=600)
def fetch_data(table_name: str):
    if supabase is None:
        return pd.DataFrame()
        
    try:
        response = supabase.table(table_name).select("*").execute()
        
        if response.data is None:
             st.warning(f"Nenhum dado encontrado na tabela '{table_name}'.")
             return pd.DataFrame()

        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados da tabela '{table_name}': {e}")
        st.warning("Verifique o nome da tabela e permissões RLS no Supabase.")
        return pd.DataFrame()


# --- FUNÇÕES DAS PÁGINAS (AS SEÇÕES DO SEU MENU) ---

def show_tarefas():
    st.title("📋 Tarefas Principais")
    st.markdown("Aqui você pode criar, visualizar, editar e concluir suas tarefas.")
    st.info("Esta seção fará o CRUD (Criar, Ler, Atualizar, Deletar) na tabela principal de tarefas do Supabase.")
    # PRÓXIMA IMPLEMENTAÇÃO: Lógica para Tarefas

def show_subtarefas():
    st.title("📌 Subtarefas")
    st.markdown("Gerencie os passos menores necessários para completar suas tarefas principais.")
    st.info("Implementação futura: Lógica para ligar subtarefas a uma Tarefa principal.")
    # PRÓXIMA IMPLEMENTAÇÃO: Lógica para Subtarefas

def show_anotacoes():
    st.title("📝 Anotações e Ideias")
    st.markdown("Um bloco de notas simples e pesquisável para salvar informações rapidamente.")
    st.info("Implementação futura: Salvar notas longas na tabela 'notes' do Supabase.")
    # PRÓXIMA IMPLEMENTAÇÃO: Lógica para Anotações

def show_agendas():
    st.title("🗓️ Agendas / Compromissos")
    st.markdown("Gerencie seus compromissos e horários com datas e horários específicos.")
    st.info("Esta seção focará em eventos agendados, possivelmente recorrentes.")
    # PRÓXIMA IMPLEMENTAÇÃO: Lógica para Agendas

def show_calendario_visual():
    st.title("📆 Calendário Visual")
    st.markdown("Visualização integrada de Tarefas e Agendas em um formato de calendário interativo.")
    st.warning("Requer a instalação de uma biblioteca externa de calendário, como `streamlit-calendar`.")
    # PRÓXIMA IMPLEMENTAÇÃO: Integração visual

def show_lixeira():
    st.title("🗑️ Lixeira")
    st.markdown("Recupere ou exclua permanentemente itens excluídos de outras seções (Soft-Delete).")
    st.info("Esta funcionalidade depende de uma coluna 'is_deleted' nas tabelas do Supabase.")
    # PRÓXIMA IMPLEMENTAÇÃO: Lógica para Lixeira

# --- LÓGICA DE NAVEGAÇÃO PRINCIPAL ---

# 1. Mapeamento das páginas para as funções
PAGES = {
    "Tarefas": show_tarefas,
    "Subtarefas": show_subtarefas,
    "Anotações": show_anotacoes,
    "Agendas": show_agendas,
    "Calendário Visual": show_calendario_visual,
    "---": None, # Separador
    "Lixeira": show_lixeira
}

# 2. SIDEBAR (MENU)
st.sidebar.title("Menu Principal")

# Seleção da página usando um radio button na sidebar
selection = st.sidebar.radio("Navegar", list(PAGES.keys()))

st.sidebar.markdown("---")
# Exibir status da conexão no sidebar
if supabase is not None:
    st.sidebar.success("Supabase Conectado ✅")
else:
    st.sidebar.error("Supabase Desconectado ❌")

# 3. RENDERIZAÇÃO DA PÁGINA SELECIONADA
if selection == "---" or selection not in PAGES:
    # Página Inicial Padrão
    st.title("🚀 Bem-vindo ao Seu Web App de Produtividade!")
    st.markdown("Use o menu lateral para navegar entre as funcionalidades de **Tarefas**, **Agendas** e **Anotações**.")
    st.write("Status do Projeto: Estrutura base pronta.")
else:
    # Chama a função correspondente à seleção
    PAGES[selection]()
    
