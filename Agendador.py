import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime

# Nome do arquivo CSV para armazenamento
DATA_FILE = "bombeios_agendados.csv"

# Função para carregar dados do CSV
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["Início", "Fim"])
    else:
        return pd.DataFrame(columns=["Companhia", "Produto", "Cota", "Início", "Fim", "Duração"])

# Função para salvar dados no CSV
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Função para calcular a taxa de bombeio
def get_flow_rate(product, company):
    if product == "GAS":
        return 500
    elif product == "S10":
        return 1200 if company in ["POOL", "VIBRA"] else 600
    elif product == "S500":
        return 560
    elif product == "QAV":
        return 240
    elif product == "OC1A":
        return 300
    else:
        return None

# Função para calcular a hora de fim e duração
def calculate_end_time(start_datetime, quota, flow_rate):
    duration_hours = quota / flow_rate
    end_datetime = start_datetime + pd.Timedelta(hours=duration_hours)
    duration_str = f"{int(duration_hours):02d}:{int((duration_hours - int(duration_hours)) * 60):02d}"
    return end_datetime, duration_str

# Função para validar a hora de início
def validate_start_time(start_time):
    try:
        return pd.to_datetime(start_time, format="%H:%M", errors='raise').time()
    except ValueError:
        return None

# Configura o layout da página
st.set_page_config(layout="wide")

# Título da página
st.title("Agendador de Bombeios")

# Inicializar o estado da sessão
if "data" not in st.session_state:
    st.session_state.data = load_data()

# Inputs para coletar os dados
company = st.text_input("Companhia")
product = st.text_input("Produto")
quota = st.number_input("Cota", min_value=0, step=1)
start_time = st.text_input("Hora de Início (HH:MM)", "00:00")

# Adicionando novo bombeio
if st.button("Adicionar Bombeio"):
    flow_rate = get_flow_rate(product, company)
    if flow_rate:
        start_time_obj = validate_start_time(start_time)
        if start_time_obj is not None:
            today = datetime.today()
            start_datetime = datetime.combine(today, start_time_obj)
            end_datetime, duration_str = calculate_end_time(start_datetime, quota, flow_rate)

            new_bomb = pd.DataFrame([{
                "Companhia": company,
                "Produto": product,
                "Cota": quota,
                "Início": start_datetime,
                "Fim": end_datetime,
                "Duração": duration_str
            }])

            # Atualiza o DataFrame no estado da sessão
            st.session_state.data = pd.concat([st.session_state.data, new_bomb], ignore_index=True)
            save_data(st.session_state.data)  # Salva os dados no CSV
            st.success("Bombeio adicionado com sucesso!")
            st.experimental_rerun()  # Atualiza a página para refletir as mudanças

        else:
            st.error("Formato de hora de início inválido. Use HH:MM.")

# Botão para baixar o CSV atualizado
st.download_button(
    label="Baixar CSV Atualizado",
    data=st.session_state.data.to_csv(index=False).encode('utf-8'),
    file_name='bombeios_agendados.csv',
    mime='text/csv',
)

# Exibir os dados adicionados e permitir edição ou remoção
if not st.session_state.data.empty:
    st.subheader("Dados de Bombeios Agendados")
    for index, row in st.session_state.data.iterrows():
        cols = st.columns([4, 1, 1])

        with cols[0]:
            st.write(row.to_frame().T)

        with cols[1]:
            if st.button(f"Editar", key=f"edit_{index}"):
                # Inputs para edição
                edited_company = st.text_input("Companhia", value=row['Companhia'], key=f"edit_company_{index}")
                edited_product = st.text_input("Produto", value=row['Produto'], key=f"edit_product_{index}")
                edited_quota = st.number_input("Cota", min_value=0, step=1, value=row['Cota'], key=f"edit_quota_{index}")
                edited_start_time = st.text_input("Hora de Início (HH:MM)", value=row['Início'].strftime('%H:%M'), key=f"edit_start_time_{index}")

                # Salvar alterações
                if st.button("Salvar alterações", key=f"save_{index}"):
                    flow_rate = get_flow_rate(edited_product, edited_company)
                    if flow_rate:
                        start_time_obj = validate_start_time(edited_start_time)
                        if start_time_obj is not None:
                            today = datetime.today()
                            start_datetime = datetime.combine(today, start_time_obj)
                            end_datetime, duration_str = calculate_end_time(start_datetime, edited_quota, flow_rate)

                            # Atualiza o DataFrame com as alterações
                            st.session_state.data.at[index, 'Companhia'] = edited_company
                            st.session_state.data.at[index, 'Produto'] = edited_product
                            st.session_state.data.at[index, 'Cota'] = edited_quota
                            st.session_state.data.at[index, 'Início'] = start_datetime
                            st.session_state.data.at[index, 'Fim'] = end_datetime
                            st.session_state.data.at[index, 'Duração'] = duration_str

                            save_data(st.session_state.data)  # Salvar no CSV
                            st.success("Alterações salvas com sucesso!")
                            st.experimental_rerun()  # Atualiza a página para refletir as mudanças

                        else:
                            st.error("Formato de hora de início inválido. Use HH:MM.")
                    else:
                        st.error("Produto ou Companhia inválidos. Verifique os valores.")

        with cols[2]:
            if st.button(f"Remover", key=f"remove_{index}"):
                st.session_state.data = st.session_state.data.drop(index).reset_index(drop=True)
                save_data(st.session_state.data)
                st.success(f"Bombeio da companhia {row['Companhia']} removido com sucesso!")
                st.experimental_rerun()  # Atualiza a página para refletir as mudanças

    # Gráfico de Gantt usando Altair
    st.subheader("Gráfico Gantt de Bombeios")
    chart_data = st.session_state.data

    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Início:T', axis=alt.Axis(format='%H:%M')),
        x2='Fim:T',
        y='Companhia:N',
        color='Produto:N',
        tooltip=['Companhia', 'Produto', 'Cota', 'Início:T', 'Fim:T', 'Duração']
    ).properties(width=800)

    st.altair_chart(chart)
else:
    st.write("Nenhum bombeio agendado.")



