import streamlit as st
import pandas as pd
import sqlite3
import os
import altair as alt

# Nome do arquivo SQLite para armazenamento
DB_FILE = "bombeios.db"

# Função para criar a tabela se não existir
def create_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bombeios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            companhia TEXT NOT NULL,
            produto TEXT NOT NULL,
            cota INTEGER NOT NULL,
            inicio TEXT NOT NULL,
            fim TEXT NOT NULL,
            duracao TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Função para carregar dados do banco de dados
def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM bombeios", conn, parse_dates=["inicio", "fim"])
    conn.close()
    return df

# Inicializar a aplicação
create_table()  # Cria a tabela se não existir

# Carregar os dados na inicialização
if 'data' not in st.session_state:
    st.session_state.data = load_data()  # Carrega os dados do banco de dados

# Exibir dados na interface
st.dataframe(st.session_state.data)

# Função para salvar dados no banco de dados
def save_data(company, product, quota, start_time, end_time, duration_str):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bombeios (companhia, produto, cota, inicio, fim, duracao)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            company,
            product,
            quota,
            start_time.strftime("%Y-%m-%d %H:%M"),  # Converte para string
            end_time.strftime("%Y-%m-%d %H:%M"),    # Converte para string
            duration_str
        ))
        conn.commit()
        st.success("Dados salvos com sucesso!")
    except sqlite3.Error as e:
        st.error(f"Erro ao salvar dados no banco de dados: {e}")
    finally:
        conn.close()

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

# Função para calcular a hora de fim e duração
def calculate_end_time(start_datetime, quota, flow_rate):
    duration_hours = quota / flow_rate  # Duração em horas
    end_datetime = start_datetime + pd.Timedelta(hours=duration_hours)
    duration_str = f"{int(duration_hours):02d}:{int((duration_hours - int(duration_hours)) * 60):02d}"  # Formato HH:MM
    return end_datetime, duration_str

# Cria a tabela no início do aplicativo
create_table()

# Configura o layout da página
st.set_page_config(layout="wide")

# Título da página
st.title("Agendador de Bombeios")

# Adicionar um seletor de data para o filtro
data_selecionada = st.date_input("Selecione uma data", pd.to_datetime("today"))

# Exibir a data selecionada no início da página
st.markdown(f"**Data Selecionada:** {data_selecionada.strftime('%d/%m/%Y')}")

# Lista de opções para Companhia e Produto
company_options = ["POO", "PET", "SIM", "PTS", "FIC", "CJ", "TCT", "TRR", "TSO", "RM", "OPL", "CRS", "TOR", "DM", "SHE"]
product_options = ["GAS", "S10", "S500", "QAV", "OC"]

# Inputs para coletar os dados com listas suspensas
company = st.selectbox("Companhia", company_options)  # Selectbox para escolher a companhia
product = st.selectbox("Produto", product_options)  # Selectbox para escolher o produto
quota = st.number_input("Cota", min_value=0, step=1)
start_time = st.text_input("Hora de Início (HH:MM)", "00:00")

# Inicializar o estado da sessão
if "data" not in st.session_state:
    st.session_state.data = load_data()

# Cálculo inicial de fim e duração
if st.button("Adicionar Bombeio"):
    flow_rate = get_flow_rate(product, company)
    
    if flow_rate:
        try:
            # Combina a data selecionada com a hora de início inserida
            start_datetime = pd.to_datetime(data_selecionada.strftime("%Y-%m-%d") + " " + start_time)
            end_datetime, duration_str = calculate_end_time(start_datetime, quota, flow_rate)

            # Chama a função para salvar os dados
            save_data(company, product, quota, start_datetime, end_datetime, duration_str)
            st.session_state.data = load_data()  # Recarrega os dados após adicionar
        except ValueError:
            st.error("Formato de hora de início inválido. Use HH:MM.")
    else:
        st.error("Produto ou Companhia inválidos. Verifique os valores.")

# Exibir os dados adicionados filtrados pela data selecionada
if not st.session_state.data.empty:
    st.subheader(f"Dados de Bombeios Agendados para {data_selecionada.strftime('%d/%m/%Y')}")
    
    # Filtrar os dados com base na data selecionada
    df = st.session_state.data[st.session_state.data["inicio"].dt.normalize() == pd.to_datetime(data_selecionada)]

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
                    # Remove o bombeio do banco de dados
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM bombeios WHERE id = ?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.session_state.data = load_data()  # Recarrega os dados após remover
                    st.success(f"Bombeio da companhia {row['companhia']} removido com sucesso!")
            with cols[2]:
                if st.button(f"Editar", key=f"edit_{index}"):
                    st.session_state.edit_index = index

        # Verifica se há uma linha em edição
        edit_index = st.session_state.get('edit_index', None)  # Obtém o índice da linha em edição
        if edit_index is not None and edit_index < len(df):
            st.subheader("Editar Bombeio")

            # Preenche os campos com os dados atuais da linha selecionada
            edit_company = st.text_input("Companhia", value=df.loc[edit_index, "companhia"])
            edit_product = st.text_input("Produto", value=df.loc[edit_index, "produto"])
            edit_quota = st.number_input("Cota", min_value=0, step=1, value=int(df.loc[edit_index, "cota"]))
            edit_start_time = st.text_input("Hora de Início (HH:MM)", value=df.loc[edit_index, "inicio"].strftime("%H:%M"))

# Botão para salvar a edição
if st.button("Salvar Edição"):
    try:
        # Calcula novos valores com base nas edições
        start_datetime = pd.to_datetime(data_selecionada.strftime("%Y-%m-%d") + " " + edit_start_time)
        flow_rate = get_flow_rate(edit_product, edit_company)
        end_datetime, duration_str = calculate_end_time(start_datetime, edit_quota, flow_rate)

        # Salva os dados editados no banco de dados
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bombeios 
            SET companhia = ?, produto = ?, cota = ?, inicio = ?, fim = ?, duracao = ?
            WHERE id = ?
        ''', (
            edit_company,
            edit_product,
            edit_quota,
            start_datetime.strftime("%Y-%m-%d %H:%M"),  # Converte para string
            end_datetime.strftime("%Y-%m-%d %H:%M"),    # Converte para string
            duration_str,
            df.loc[edit_index, "id"]  # ID da linha a ser atualizada
        ))
        conn.commit()
        conn.close()

        # Atualiza o DataFrame no estado da sessão
        st.session_state.data.loc[edit_index, "companhia"] = edit_company
        st.session_state.data.loc[edit_index, "produto"] = edit_product
        st.session_state.data.loc[edit_index, "cota"] = edit_quota
        st.session_state.data.loc[edit_index, "inicio"] = start_datetime
        st.session_state.data.loc[edit_index, "fim"] = end_datetime
        st.session_state.data.loc[edit_index, "duracao"] = duration_str

        # Exibe a mensagem de sucesso e limpa o índice de edição
        st.success("Bombeio editado com sucesso!")
        st.session_state.edit_index = None
    except ValueError:
        st.error("Erro ao editar os dados. Verifique os valores inseridos.")

# Criar uma nova coluna com o nome da companhia e os horários de início e fim
if not st.session_state.data.empty:
    st.session_state.data["Companhia_Horarios"] = st.session_state.data.apply(
        lambda row: f"{row['companhia']} ({row['inicio'].strftime('%H:%M')} - {row['fim'].strftime('%H:%M')})", axis=1)

# Criar gráfico de Gantt usando Altair
if not st.session_state.data.empty:
    st.subheader(f"Gráfico Gantt de Bombeios para {data_selecionada.strftime('%d/%m/%Y')}")

    # Filtrar os dados para o gráfico com base na data selecionada
    chart_data = st.session_state.data[st.session_state.data["inicio"].dt.normalize() == pd.to_datetime(data_selecionada)]
    
    if chart_data.empty:
        st.write("Nenhum dado para o gráfico na data selecionada.")
    else:
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('inicio:T', axis=alt.Axis(format='%H:%M')),
            x2='fim:T',
            y=alt.Y('Companhia_Horarios:N', title='Companhia', sort='-x'),
            color=alt.Color('produto:N', title='Produto', scale=alt.Scale(scheme='category10')),
            tooltip=['companhia', 'produto', 'cota', 'inicio', 'fim', 'duracao']
        ).properties(
            title='Bombeios Agendados',
            width=800,
            height=400
        )
        st.altair_chart(chart, use_container_width=True)
else:
    st.write("Não há nenhum bombeio agendado.")
