import streamlit as st
import pandas as pd
import altair as alt
import os
import pyodbc

# Configura a conexão ao SQL Server
def get_sql_server_connection():
    conn = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=192.168.16.80\kern;'
        'DATABASE=KernSQL;'
        'UID=UserPowerBI;'
        'PWD=eod.pwb.24'
    )
    return conn

# Função para carregar o histórico de bombeios anteriores do SQL Server
def load_pump_schedule_history(company, product):
    conn = get_sql_server_connection()
    query = f"""
        SELECT TOP 1 HoraBombIni
        FROM tbBombeios
        WHERE CodCia = '{company}' 
          AND CodProd = '{product}'
        ORDER BY HoraBombIni DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()

    # Verifica se encontrou algum registro e retorna a hora
    if not df.empty:
        return df['HoraBombIni'].iloc[0]  # Retorna a hora de início mais recente
    else:
        return None  # Retorna None se não houver histórico

# Função para sugerir o próximo horário de início com base no histórico de bombeios
def suggest_start_time(company, product):
    last_start_time = load_pump_schedule_history(company, product)
    
    if last_start_time:
        # Sugere 15 minutos após o último horário registrado
        suggested_start_time = (pd.to_datetime(last_start_time) + pd.Timedelta(minutes=15)).time()
        return suggested_start_time
    else:
        # Caso não haja histórico, sugere o horário padrão (00:00)
        return pd.to_datetime("00:00").time()

# Função para carregar dados do CSV local
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["Início", "Fim"])
    else:
        return pd.DataFrame(columns=["Companhia", "Produto", "Cota", "Início", "Fim", "Duração"])

# Função para salvar dados no CSV local
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Função para calcular a taxa de bombeio
def get_flow_rate(product, company):
    if product == "GAS":
        return 500
    elif product == "S10":
        if company in ["POO", "PET"]:
            return 1200
        else:
            return 600
    elif product == "S500":
        return 560
    elif product == "QAV":
        return 240
    elif product == "OC":
        return 300
    else:
        return None  # Caso o produto não esteja definido

# Função para calcular a hora de fim e a duração do bombeio
def calculate_end_time(start_datetime, quota, flow_rate):
    duration_hours = quota / flow_rate  # Duração em horas
    end_datetime = start_datetime + pd.Timedelta(hours=duration_hours)
    duration_str = f"{int(duration_hours):02d}:{int((duration_hours - int(duration_hours)) * 60):02d}"  # Formato HH:MM
    return end_datetime, duration_str

# Configura o layout da página
st.set_page_config(layout="wide")

# Título da página
st.title("Agendador de Bombeios")

# Adicionar um seletor de data para o filtro
data_selecionada = st.date_input("Selecione uma data", pd.to_datetime("today"))

# Exibir a data selecionada
st.markdown(f"**Data Selecionada:** {data_selecionada.strftime('%d/%m/%Y')}")

# Lista de opções para Companhia e Produto
company_options = ["POO", "PET", "SIM", "PTS", "FIC", "CJ", "TCT", "TRR", "TSO", "RM", "OPL", "CRS", "TOR", "DM", "SHE"]
product_options = ["GAS", "S10", "S500", "QAV", "OC"]

# Inputs para coletar os dados com listas suspensas
company = st.selectbox("Companhia", company_options)  # Selectbox para escolher a companhia
product = st.selectbox("Produto", product_options)  # Selectbox para escolher o produto
quota = st.number_input("Cota", min_value=0, step=1)

# Sugere o horário de início com base no histórico de bombeios no SQL Server
suggested_time = suggest_start_time(company, product, data_selecionada)
start_time = st.time_input("Hora de Início (HH:MM)", suggested_time)

# Inicializar o estado da sessão
if "data" not in st.session_state:
    st.session_state.data = load_data()

# Verificar se o DataFrame está vazio e inicializá-lo se necessário
if st.session_state.data is None or not isinstance(st.session_state.data, pd.DataFrame):
    st.session_state.data = pd.DataFrame(columns=["Companhia", "Produto", "Cota", "Início", "Fim", "Duração"])

# Cálculo de fim e duração do bombeio ao adicionar um novo bombeio
if st.button("Adicionar Bombeio"):
    flow_rate = get_flow_rate(product, company)
    
    if flow_rate:
        try:
            # Combina a data selecionada com a hora de início inserida
            start_datetime = pd.to_datetime(data_selecionada.strftime("%Y-%m-%d") + " " + start_time.strftime("%H:%M"))
            end_datetime, duration_str = calculate_end_time(start_datetime, quota, flow_rate)

            # Cria um novo DataFrame com os dados do bombeio
            new_bomb = pd.DataFrame([{
                "Companhia": company,
                "Produto": product,
                "Cota": quota,
                "Início": start_datetime,
                "Fim": end_datetime,
                "Duração": duration_str
            }])
            
            # Adiciona o novo bombeio ao DataFrame existente
            st.session_state.data = pd.concat([st.session_state.data, new_bomb], ignore_index=True)
            save_data(st.session_state.data)  # Salva os dados no CSV local
            st.success("Bombeio adicionado com sucesso!")
        except ValueError:
            st.error("Formato de hora de início inválido. Use HH:MM.")
    else:
        st.error("Produto ou Companhia inválidos. Verifique os valores.")

# Exibir os dados adicionados filtrados pela data selecionada
if not st.session_state.data.empty:
    st.subheader(f"Dados de Bombeios Agendados para {data_selecionada.strftime('%d/%m/%Y')}")
    
    # Filtrar os dados com base na data selecionada
    df = st.session_state.data[st.session_state.data["Início"].dt.normalize() == pd.to_datetime(data_selecionada)]
    
    if df.empty:
        st.write("Nenhuma programação encontrada para a data selecionada.")
    else:
        # Variável para armazenar a linha em edição
        edit_index = st.session_state.get('edit_index', None)

        # Cria colunas para os dados e os botões
        for index, row in df.iterrows():
            cols = st.columns([4, 1, 1])  # Ajuste a proporção conforme necessário
            with cols[0]:
                st.write(row.to_frame().T)  # Exibe a linha do DataFrame
            with cols[1]:
                if st.button(f"Remover", key=f"remove_{index}"):
                    st.session_state.data = st.session_state.data.drop(index).reset_index(drop=True)
                    save_data(st.session_state.data)  # Salva os dados no CSV local
                    st.success(f"Bombeio da companhia {row['Companhia']} removido com sucesso!")
            with cols[2]:
                if st.button(f"Editar", key=f"edit_{index}"):
                    st.session_state.edit_index = index

        # Verifica se há uma linha em edição
        if edit_index is not None and edit_index < len(df):
            st.subheader("Editar Bombeio")

            # Preenche os campos com os dados atuais da linha selecionada
            edit_company = st.text_input("Companhia", value=df.loc[edit_index, "Companhia"])
            edit_product = st.text_input("Produto", value=df.loc[edit_index, "Produto"])
            edit_quota = st.number_input("Cota", min_value=0, step=1, value=int(df.loc[edit_index, "Cota"]))
            edit_start_time = st.text_input("Hora de Início (HH:MM)", value=df.loc[edit_index, "Início"].strftime("%H:%M"))

            # Botão para salvar a edição
            if st.button("Salvar Edição"):
                try:
                    # Calcula novos valores com base nas edições
                    start_datetime = pd.to_datetime(df.loc[edit_index, "Início"].strftime("%Y-%m-%d") + " " + edit_start_time)
                    flow_rate = get_flow_rate(edit_product, edit_company)
                    end_datetime, duration_str = calculate_end_time(start_datetime, edit_quota, flow_rate)

                    # Atualiza a linha com os novos valores
                    st.session_state.data.loc[edit_index, "Companhia"] = edit_company
                    st.session_state.data.loc[edit_index, "Produto"] = edit_product
                    st.session_state.data.loc[edit_index, "Cota"] = edit_quota
                    st.session_state.data.loc[edit_index, "Início"] = start_datetime
                    st.session_state.data.loc[edit_index, "Fim"] = end_datetime
                    st.session_state.data.loc[edit_index, "Duração"] = duration_str

                    save_data(st.session_state.data)  # Salva os dados no CSV local
                    st.session_state.edit_index = None  # Finaliza a edição
                    st.success("Edição salva com sucesso!")
                except ValueError:
                    st.error("Erro ao salvar a edição. Verifique os valores inseridos.")
else:
    st.write("Nenhum bombeio agendado ainda.")
