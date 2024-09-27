import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
import os

# Nome do banco de dados SQLite
DB_FILE = "bombeios_agendados.db"

# Função para inicializar o banco de dados
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bombeios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            companhia TEXT,
            produto TEXT,
            cota INTEGER,
            inicio TIMESTAMP,
            fim TIMESTAMP,
            duracao TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Função para carregar os dados do SQLite
def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM bombeios", conn, parse_dates=["inicio", "fim"])
    conn.close()
    return df

# Função para salvar dados no SQLite
def save_data(company, product, quota, start_time, end_time, duration_str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bombeios (companhia, produto, cota, inicio, fim, duracao)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (company, product, quota, start_time, end_time, duration_str))
    conn.commit()
    conn.close()

# Função para remover um bombeio
def remove_data(bombeio_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bombeios WHERE id = ?', (bombeio_id,))
    conn.commit()
    conn.close()

# Função para editar um bombeio
def edit_data(bombeio_id, company, product, quota, start_time, end_time, duration_str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE bombeios
        SET companhia = ?, produto = ?, cota = ?, inicio = ?, fim = ?, duracao = ?
        WHERE id = ?
    ''', (company, product, quota, start_time, end_time, duration_str, bombeio_id))
    conn.commit()
    conn.close()

# Função para calcular a taxa de bombeio
def get_flow_rate(product, company):
    if product == "GAS":
        return 500
    elif product == "S10":
        return 1200 if company in ["POO", "PET"] else 600
    elif product == "S500":
        return 560
    elif product == "QAV":
        return 240
    elif product == "OC":
        return 300
    else:
        return None

# Função para calcular o tempo de fim e a duração
def calculate_end_time(start_datetime, quota, flow_rate):
    duration_hours = quota / flow_rate
    end_datetime = start_datetime + pd.Timedelta(hours=duration_hours)
    duration_str = f"{int(duration_hours):02d}:{int((duration_hours - int(duration_hours)) * 60):02d}"
    return end_datetime, duration_str

# Inicializar o banco de dados na primeira execução
init_db()

# Configura a página
st.set_page_config(layout="wide")
st.title("Agendador de Bombeios")

# Seletor de data
data_selecionada = st.date_input("Selecione uma data", pd.to_datetime("today"))
st.markdown(f"**Data Selecionada:** {data_selecionada.strftime('%d/%m/%Y')}")

# Listas de opções para Companhia e Produto
company_options = ["POO", "PET", "SIM", "PTS", "FIC", "CJ", "TCT", "TRR", "TSO", "RM", "OPL", "CRS", "TOR", "DM", "SHE"]
product_options = ["GAS", "S10", "S500", "QAV", "OC"]

# Inputs para coleta de dados
company = st.selectbox("Companhia", company_options)
product = st.selectbox("Produto", product_options)
quota = st.number_input("Cota", min_value=0, step=1)
start_time = st.text_input("Hora de Início (HH:MM)", "00:00")

# Inicializar o DataFrame com os dados do banco
df = load_data()

# Adicionar novo bombeio
if st.button("Adicionar Bombeio"):
    flow_rate = get_flow_rate(product, company)
    if flow_rate:
        try:
            start_datetime = pd.to_datetime(data_selecionada.strftime("%Y-%m-%d") + " " + start_time)
            end_datetime, duration_str = calculate_end_time(start_datetime, quota, flow_rate)

            save_data(company, product, quota, start_datetime, end_datetime, duration_str)
            st.success("Bombeio adicionado com sucesso!")
        except ValueError:
            st.error("Formato de hora de início inválido. Use HH:MM.")
    else:
        st.error("Produto ou Companhia inválidos. Verifique os valores.")

# Filtrar dados pela data selecionada
df_filtered = df[df['inicio'].dt.normalize() == pd.to_datetime(data_selecionada)]

# Exibir bombeios filtrados
if not df_filtered.empty:
    st.subheader(f"Dados de Bombeios Agendados para {data_selecionada.strftime('%d/%m/%Y')}")
    for index, row in df_filtered.iterrows():
        cols = st.columns([4, 1, 1])
        with cols[0]:
            st.write(row.to_frame().T)
        with cols[1]:
            if st.button(f"Remover", key=f"remove_{index}"):
                remove_data(row['id'])
                st.success(f"Bombeio da companhia {row['companhia']} removido com sucesso!")
        with cols[2]:
            if st.button(f"Editar", key=f"edit_{index}"):
                # Lógica para editar (similar à adição)
                pass

# Criar gráfico de Gantt
if not df_filtered.empty:
    st.subheader(f"Gráfico Gantt de Bombeios para {data_selecionada.strftime('%d/%m/%Y')}")
    df_filtered['Companhia_Horarios'] = df_filtered.apply(lambda row: f"{row['companhia']} ({row['inicio'].strftime('%H:%M')} - {row['fim'].strftime('%H:%M')})", axis=1)

    chart = alt.Chart(df_filtered).mark_bar().encode(
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

