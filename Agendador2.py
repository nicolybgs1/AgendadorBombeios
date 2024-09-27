import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# Nome do arquivo SQLite para armazenamento
DB_FILE = "bombeios.db"

# Função para criar a tabela de bombeios
def create_table():
    with sqlite3.connect(DB_FILE) as conn:
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

# Função para carregar os dados do banco de dados
def load_data():
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql_query("SELECT * FROM bombeios", conn, parse_dates=["inicio", "fim"])

# Função para salvar dados no banco de dados
def save_data(company, product, quota, start_time, end_time, duration_str):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bombeios (companhia, produto, cota, inicio, fim, duracao)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                company,
                product,
                quota,
                start_time.strftime("%Y-%m-%d %H:%M"),
                end_time.strftime("%Y-%m-%d %H:%M"),
                duration_str
            ))
            conn.commit()
            st.success("Dados salvos com sucesso!")
    except sqlite3.Error as e:
        st.error(f"Erro ao salvar dados no banco de dados: {e}")

# Função para calcular a taxa de bombeio
def get_flow_rate(product, company):
    flow_rates = {
        "GAS": 500,
        "S10": 1200 if company in ["POO", "PET"] else 600,
        "S500": 560,
        "QAV": 240,
        "OC": 300
    }
    return flow_rates.get(product, None)

# Função para calcular hora de fim e duração
def calculate_end_time(start_datetime, quota, flow_rate):
    duration_hours = quota / flow_rate
    end_datetime = start_datetime + pd.Timedelta(hours=duration_hours)
    duration_str = f"{int(duration_hours):02d}:{int((duration_hours - int(duration_hours)) * 60):02d}"
    return end_datetime, duration_str

# Cria a tabela ao iniciar o aplicativo
create_table()

# Configura o layout da página
st.set_page_config(layout="wide")
st.title("Agendador de Bombeios")

# Seleção da data
data_selecionada = st.date_input("Selecione uma data", pd.to_datetime("today"))
st.markdown(f"**Data Selecionada:** {data_selecionada.strftime('%d/%m/%Y')}")

# Opções para Companhia e Produto
company_options = ["POO", "PET", "SIM", "PTS", "FIC", "CJ", "TCT", "TRR", "TSO", "RM", "OPL", "CRS", "TOR", "DM", "SHE"]
product_options = ["GAS", "S10", "S500", "QAV", "OC"]

# Inputs para coletar dados
company = st.selectbox("Companhia", company_options)
product = st.selectbox("Produto", product_options)
quota = st.number_input("Cota", min_value=0, step=1)
start_time = st.text_input("Hora de Início (HH:MM)", "00:00")

# Carregar dados na inicialização
if 'data' not in st.session_state:
    try:
        st.session_state.data = load_data()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

# Exibir dados carregados
if 'data' in st.session_state and st.session_state.data is not None:
    st.dataframe(st.session_state.data)
else:
    st.warning("Nenhum dado disponível para exibir.")

# Adicionar bombeio
if st.button("Adicionar Bombeio"):
    flow_rate = get_flow_rate(product, company)
    if flow_rate:
        try:
            start_datetime = pd.to_datetime(f"{data_selecionada} {start_time}")
            end_datetime, duration_str = calculate_end_time(start_datetime, quota, flow_rate)
            save_data(company, product, quota, start_datetime, end_datetime, duration_str)
            st.session_state.data = load_data()  # Atualiza os dados após adicionar
        except ValueError:
            st.error("Formato de hora de início inválido. Use HH:MM.")
    else:
        st.error("Produto ou Companhia inválidos. Verifique os valores.")

# Exibir dados agendados
if not st.session_state.data.empty:
    st.subheader(f"Dados de Bombeios Agendados para {data_selecionada.strftime('%d/%m/%Y')}")
    df = st.session_state.data[st.session_state.data["inicio"].dt.normalize() == pd.to_datetime(data_selecionada)]
    
    if df.empty:
        st.write("Nenhuma programação encontrada para a data selecionada.")
    else:
        for index, row in df.iterrows():
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.write(row.to_frame().T)
            with cols[1]:
                if st.button(f"Remover", key=f"remove_{index}"):
                    with sqlite3.connect(DB_FILE) as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM bombeios WHERE id = ?", (row['id'],))
                        conn.commit()
                    st.session_state.data = load_data()
                    st.success(f"Bombeio da companhia {row['companhia']} removido com sucesso!")
            with cols[2]:
                if st.button(f"Editar", key=f"edit_{index}"):
                    st.session_state.edit_index = index

# Edição de dados
edit_index = st.session_state.get('edit_index', None)
if edit_index is not None and edit_index < len(df):
    st.subheader("Editar Bombeio")
    edit_company = st.text_input("Companhia", value=df.loc[edit_index, "companhia"])
    edit_product = st.text_input("Produto", value=df.loc[edit_index, "produto"])
    edit_quota = st.number_input("Cota", min_value=0, step=1, value=int(df.loc[edit_index, "cota"]))
    edit_start_time = st.text_input("Hora de Início (HH:MM)", value=df.loc[edit_index, "inicio"].strftime("%H:%M"))

    if st.button("Salvar Edição"):
        try:
            # Converte a hora de início usando apenas o formato HH:MM
            start_datetime = pd.to_datetime(f"{data_selecionada} {edit_start_time}", format="%Y-%m-%d %H:%M")

            flow_rate = get_flow_rate(edit_product, edit_company)

            if flow_rate is None:
                st.error("Produto ou Companhia inválidos. Verifique os valores.")
            else:
                end_datetime, duration_str = calculate_end_time(start_datetime, edit_quota, flow_rate)

                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE bombeios 
                        SET companhia = ?, produto = ?, cota = ?, inicio = ?, fim = ?, duracao = ?
                        WHERE id = ?
                    ''', (
                        edit_company,
                        edit_product,
                        edit_quota,
                        start_datetime.strftime("%Y-%m-%d %H:%M"),
                        end_datetime.strftime("%Y-%m-%d %H:%M"),
                        duration_str,
                        df.loc[edit_index, "id"]
                    ))
                    conn.commit()

                # Atualiza o DataFrame na sessão
                st.session_state.data.at[edit_index, "companhia"] = edit_company
                st.session_state.data.at[edit_index, "produto"] = edit_product
                st.session_state.data.at[edit_index, "cota"] = edit_quota
                st.session_state.data.at[edit_index, "inicio"] = start_datetime
                st.session_state.data.at[edit_index, "fim"] = end_datetime
                st.session_state.data.at[edit_index, "duracao"] = duration_str

                st.success("Bombeio editado com sucesso!")
                st.session_state.edit_index = None
        except ValueError as ve:
            st.error(f"Erro de valor: {ve}. Verifique os valores inseridos.")
        except Exception as e:
            st.error(f"Erro ao editar os dados: {e}")

# Criar gráfico de Gantt usando Altair
if not st.session_state.data.empty:
    st.session_state.data["Companhia_Horarios"] = st.session_state.data.apply(
        lambda row: f"{row['companhia']} ({row['inicio'].strftime('%H:%M')} - {row['fim'].strftime('%H:%M')})", axis=1)

    st.subheader(f"Gráfico Gantt de Bombeios para {data_selecionada.strftime('%d/%m/%Y')}")
    chart_data = st.session_state.data[st.session_state.data["inicio"].dt.normalize() == pd.to_datetime(data_selecionada)]
    
    if chart_data.empty:
        st.write("Nenhum dado para o gráfico na data selecionada.")
    else:
        chart = alt.Chart(chart_data).mark_bar().encode(
            x='inicio:T',
            x2='fim:T',
            y='Companhia_Horarios:N',
            tooltip=['companhia', 'produto', 'cota', 'inicio', 'fim', 'duracao']
        ).properties(width=700, height=400)

        st.altair_chart(chart)

