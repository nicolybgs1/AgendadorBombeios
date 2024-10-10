import streamlit as st
import pandas as pd
import os
import pyodbc

# Defina DATA_FILE antes de usar
DATA_FILE = "data.csv"  # Substitua pelo caminho correto do seu CSV

# Configura a conexão ao SQL Server
def get_sql_server_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=192.168.16.80\sqlserver;'  # Certifique-se de que o nome do servidor está correto
            'DATABASE=KernSQL;'
            'UID=UserPowerBI;'
            'PWD=eod.pwb.24'
        )
        print("Conexão estabelecida com sucesso!")
        return conn
    except pyodbc.Error as e:
        print("Erro ao conectar ao SQL Server:", e)
        return None

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
    if not df.empty:
        return df['HoraBombIni'].iloc[0]
    else:
        return None

# Função para sugerir o próximo horário de início com base no histórico de bombeios
def suggest_start_time(company, product):
    last_start_time = load_pump_schedule_history(company, product)
    if last_start_time:
        suggested_start_time = (pd.to_datetime(last_start_time) + pd.Timedelta(minutes=15)).time()
        return suggested_start_time
    else:
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

# Demais funções (get_flow_rate, calculate_end_time) aqui

# Configura o layout da página
st.set_page_config(layout="wide")
st.title("Agendador de Bombeios")

data_selecionada = st.date_input("Selecione uma data", pd.to_datetime("today"))
st.markdown(f"**Data Selecionada:** {data_selecionada.strftime('%d/%m/%Y')}")

# Inputs e seleção de dados
company_options = ["POO", "PET", "SIM", "PTS", "FIC", "CJ", "TCT", "TRR", "TSO", "RM", "OPL", "CRS", "TOR", "DM", "SHE"]
product_options = ["GAS", "S10", "S500", "QAV", "OC"]
company = st.selectbox("Companhia", company_options)
product = st.selectbox("Produto", product_options)
quota = st.number_input("Cota", min_value=0, step=1)

# Sugere o horário de início com base no histórico de bombeios no SQL Server
suggested_time = suggest_start_time(company, product)

# Input para hora de início
start_time = st.time_input("Hora de Início (HH:MM)", suggested_time)

# Exibe a sugestão de horário
st.write(f"Sugestão de Hora de Início: {suggested_time}")

# Inicializa o estado da sessão
if "data" not in st.session_state:
    st.session_state.data = load_data()

# Adiciona um novo bombeio
if st.button("Adicionar Bombeio"):
    flow_rate = get_flow_rate(product, company)
    
    if flow_rate:
        # Sugere o próximo horário de início com base no histórico de bombeios
        suggested_start_time = suggest_start_time(company, product)
        start_datetime = pd.to_datetime(data_selecionada.strftime("%Y-%m-%d") + " " + suggested_start_time.strftime("%H:%M"))
        
        # Calcula a hora de término e duração
        end_datetime, duration_str = calculate_end_time(start_datetime, quota, flow_rate)

        # Cria o DataFrame para o novo bombeio
        new_bomb = pd.DataFrame([{
            "Companhia": company,
            "Produto": product,
            "Cota": quota,
            "Início": start_datetime,
            "Fim": end_datetime,
            "Duração": duration_str
        }])
        
        # Atualiza os dados da sessão e salva no CSV
        st.session_state.data = pd.concat([st.session_state.data, new_bomb], ignore_index=True)
        save_data(st.session_state.data)
        st.success("Bombeio adicionado com sucesso!")
    else:
        st.error("Produto ou Companhia inválidos. Verifique os valores.")

# Exibir os dados adicionados filtrados pela data selecionada
if not st.session_state.data.empty:
    st.subheader(f"Dados de Bombeios Agendados para {data_selecionada.strftime('%d/%m/%Y')}")
    
    df = st.session_state.data[st.session_state.data["Início"].dt.normalize() == pd.to_datetime(data_selecionada)]
    
    if df.empty:
        st.write("Nenhuma programação encontrada para a data selecionada.")
    else:
        st.write(df)  # Adicione uma linha para visualizar os dados filtrados
        # Lógica de edição e remoção conforme necessário

else:
    st.write("Nenhum bombeio agendado ainda.")
