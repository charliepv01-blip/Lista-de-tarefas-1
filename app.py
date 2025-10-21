# app.py
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date

# --- CONFIGURAÇÃO DA CONEXÃO COM SUPABASE ---

# Pega as credenciais do Supabase de st.secrets
# st.cache_resource garante que a conexão só seja inicializada uma vez.
@st.cache_resource
def init_connection():
    try:
        # Credenciais lidas do secrets.toml (local) ou Secrets (Streamlit Cloud)
        url: str = st.secrets["supabase"]"https://bochkjykezvrlbbivzgv.supabase.co"
        key: str = st.secrets["supabase"]"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJvY2hranlrZXp2cmxiYml2emd2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEwNzE1MDgsImV4cCI6MjA3NjY"
        
        supabase: Client = create_client(url, key)
        return supabase
    except KeyError:
        st.error("Erro de configuração: As credenciais do Supabase (url e key) não foram encontradas.")
        return None
    except Exception as e:
        st.error(f"Erro ao inicializar a conexão com Supabase: {e}")
        return None

supabase = init_connection()

# --- FUNÇÕES DE PERSISTÊNCIA (CRUD) PARA TAREFAS ---

# 1. Leitura de Tarefas (excluindo as apagadas)
@st.cache_data(ttl=60) # Cache de 60 segundos para evitar sobrecarga no banco
def get_tarefas():
    if supabase is None: return pd.DataFrame()
    try:
        # Busca tarefas que não foram marcadas como apagadas
        res = supabase.table("tarefas").select("*").eq("is_deleted", False).order("data_vencimento", desc=False).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Erro ao buscar tarefas: {e}")
        return pd.DataFrame()

# 2. Criação de Tarefa
def add_tarefa(titulo, data_vencimento):
    if supabase is None: return False
    try:
        data = {'titulo': titulo}
        # Adiciona a data de vencimento se ela for fornecida
        if data_vencimento:
            data['data_vencimento'] = str(data_vencimento) # Converte para string no formato YYYY-MM-DD

        supabase.table("tarefas").insert(data).execute()
        st.cache_data.clear() # Limpa o cache para recarregar a lista
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar tarefa: {e}")
        return False

# 3. Atualização de Tarefa (Marcar como concluída/incompleta)
def mark_tarefa_complete(id_tarefa, status):
    if supabase is None: return False
    try:
        supabase.table("tarefas").update({"concluida": status}).eq("id", id_tarefa).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar tarefa: {e}")
        return False

# 4. Exclusão Lógica de Tarefa (Enviada para a Lixeira)
def soft_delete_tarefa(id_tarefa, titulo_tarefa):
    if supabase is None: return False
    try:
        # Marca a tarefa como deletada (Soft Delete)
        supabase.table("tarefas").update({"is_deleted": True}).eq("id", id_tarefa).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao mover a tarefa '{titulo_tarefa}' para a lixeira: {e}")
        return False

# --- FUNÇÕES DAS PÁGINAS (SEÇÕES DO MENU) ---

def show_tarefas():
    st.title("📋 Tarefas Principais")

    # 1. Formulário de Criação
    with st.form("form_nova_tarefa", clear_on_submit=True):
        st.subheader("Adicionar Nova Tarefa")
        
        novo_titulo = st.text_input("Título da Tarefa", max_chars=255)
        
        # Garante que a data mínima é hoje
        data_vencimento = st.date_input("Data de Vencimento (opcional)", value=None, min_value=date.today())

        submit_button = st.form_submit_button("Adicionar Tarefa")
        
        if submit_button:
            if novo_titulo:
                if add_tarefa(novo_titulo, data_vencimento):
                    st.success("Tarefa adicionada com sucesso!")
                else:
                    st.error("Falha ao adicionar a tarefa.")
            else:
                st.warning("O título da tarefa é obrigatório.")

    st.markdown("---")

    # 2. Exibição e Interação com as Tarefas Existentes
    st.subheader("Suas Tarefas")
    
    # Busca os dados (usa o cache)
    tarefas_df = get_tarefas()

    if tarefas_df.empty:
        st.info("Nenhuma tarefa encontrada. Adicione uma acima!")
    else:
        # Ordena tarefas: Incompletas primeiro, depois por data de vencimento
        tarefas_df['concluida_int'] = tarefas_df['concluida'].astype(int)
        tarefas_df = tarefas_df.sort_values(by=['concluida_int', 'data_vencimento'], ascending=[True, True])
        
        # Converte para lista de dicionários para fácil iteração
        tarefas_list = tarefas_df.to_dict('records')
        
        for tarefa in tarefas_list:
            
            is_checked = tarefa['concluida']
            
            # Layout: Checkbox | Título/Data | Botão Excluir
            col_check, col_title_due, col_delete = st.columns([0.5, 5, 0.5])

            # Checkbox para Conclusão
            with col_check:
                # Se o estado for alterado...
                if col_check.checkbox("", value=is_checked, key=f"check_{tarefa['id']}") != is_checked:
                    mark_tarefa_complete(tarefa['id'], not is_checked)
                    st.experimental_rerun() # Atualiza a página após a modificação

            # Título e Data de Vencimento
            with col_title_due:
                # Estilo de texto riscado para tarefas concluídas
                if is_checked:
                    st.markdown(f"~~**{tarefa['titulo']}**~~")
                else:
                    st.markdown(f"**{tarefa['titulo']}**")
                
                # Exibe a data de vencimento
                if tarefa['data_vencimento']:
                    data_formatada = pd.to_datetime(tarefa['data_vencimento']).strftime('%d/%m/%Y')
                    st.caption(f"Vence: {data_formatada}")
                else:
                    st.caption("Sem prazo")
            
            # Botão de Excluir (Soft Delete)
            with col_delete:
                if st.button("🗑️", key=f"delete_{tarefa['id']}", help="Enviar para Lixeira"):
                    if soft_delete_tarefa(tarefa['id'], tarefa['titulo']):
                        st.success(f"Tarefa '{tarefa['titulo']}' enviada para a Lixeira.")
                        st.experimental_rerun() # Recarrega para remover o item da lista
    
    st.markdown("---")
    st.info(f"Tarefas ativas: {len(tarefas_df[tarefas_df['concluida'] == False])} | Concluídas: {len(tarefas_df[tarefas_df['concluida'] == True])}")


def show_subtarefas():
    st.title("📌 Subtarefas")
    st.markdown("Gerencie os passos menores necessários para completar suas tarefas principais.")
    st.warning("Esta seção será implementada em seguida. Ela listará as tarefas principais e permitirá adicionar passos para cada uma.")

def show_anotacoes():
    st.title("📝 Anotações e Ideias")
    st.markdown("Um bloco de notas simples e pesquisável para salvar informações rapidamente.")
    st.info("Implementação futura: Salvar notas longas na tabela 'anotacoes' do Supabase.")

def show_agendas():
    st.title("🗓️ Agendas / Compromissos")
    st.markdown("Gerencie seus compromissos e horários com datas e horários específicos.")
    st.info("Esta seção focará em eventos agendados, possivelmente recorrentes.")

def show_calendario_visual():
    st.title("📆 Calendário Visual")
    st.markdown("Visualização integrada de Tarefas e Agendas em um formato de calendário interativo.")
    st.warning("Requer a instalação de uma biblioteca externa de calendário, como `streamlit-calendar`.")

def show_lixeira():
    st.title("🗑️ Lixeira")
    st.markdown("Recupere ou exclua permanentemente itens excluídos de outras seções (Soft-Delete).")
    st.info("Esta funcionalidade depende da coluna 'is_deleted' nas tabelas.")

# --- LÓGICA DE NAVEGAÇÃO PRINCIPAL ---

PAGES = {
    "Tarefas": show_tarefas,
    "Subtarefas": show_subtarefas,
    "Anotações": show_anotacoes,
    "Agendas": show_agendas,
    "Calendário Visual": show_calendario_visual,
    "---": None, 
    "Lixeira": show_lixeira
}

st.sidebar.title("Menu Principal")
selection = st.sidebar.radio("Navegar", list(PAGES.keys()))

st.sidebar.markdown("---")
if supabase is not None:
    st.sidebar.success("Supabase Conectado ✅")
else:
    st.sidebar.error("Supabase Desconectado ❌")

if selection == "---" or selection not in PAGES:
    st.title("🚀 Bem-vindo ao Seu Web App de Produtividade!")
    st.markdown("Use o menu lateral para navegar entre as funcionalidades.")
else:
    PAGES[selection]()

