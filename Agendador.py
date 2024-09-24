import streamlit as st
import pandas as pd
import altair as alt
import os

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

# Configura o layout da página
st.set_page_config(layout="wide")

# Título da página
st.title("Agendador de Bombeios")

# Exibir a data de amanhã no início da página
tomorrow = pd.to_datetime("today") + pd.Timedelta(days=1)
st.markdown(f"**Data:** {tomorrow.strftime('%d/%m/%Y')}")

# Inicializar o estado da sessão
if "data" not in st.session_state:
    st.session_state.data = load_data()

# Inputs para coletar os dados
company = st.text_input("Companhia")
product = st.text_input("Produto")
quota = st.number_input("Cota", min_value=0, step=1)
start_time = st.text_input("Hora de Início (HH:MM)", "00:00")

# Função para calcular a taxa de bombeio
def get_flow_rate(product, company):
    if product == "GAS":
        return 500
    elif product == "S10":
        if company in ["POOL", "VIBRA"]:
            return 1200
        else:
            return 600
    elif product == "S500":
        return 560
    elif product == "QAV":
        return 240
    elif product == "OC1A":
        return 300
    else:
        return None  # Caso o produto não esteja definido

# Função para calcular a hora de fim e duração
def calculate_end_time(start_datetime, quota, flow_rate):
    duration_hours = quota / flow_rate  # Duração em horas
    end_datetime = start_datetime + pd.Timedelta(hours=duration_hours)
    duration_str = f"{int(duration_hours):02d}:{int((duration_hours - int(duration_hours)) * 60):02d}"  # Formato HH:MM
    return end_datetime, duration_str

# Cálculo inicial de fim e duração
if st.button("Adicionar Bombeio"):
    flow_rate = get_flow_rate(product, company)
    
    if flow_rate:
        try:
            start_datetime = pd.to_datetime(tomorrow.strftime("%Y-%m-%d") + " " + start_time)
            end_datetime, duration_str = calculate_end_time(start_datetime, quota, flow_rate)

            # Cria novo DataFrame com os dados do bombeio
            new_bomb = pd.DataFrame([{
                "Companhia": company,
                "Produto": product,
                "Cota": quota,
                "Início": start_datetime,
                "Fim": end_datetime,
                "Duração": duration_str
            }])
            
            # Adiciona novo bombeio usando pd.concat
            st.session_state.data = pd.concat([st.session_state.data, new_bomb], ignore_index=True)
            save_data(st.session_state.data)  # Salva os dados no CSV
            st.success("Bombeio adicionado com sucesso!")
        except ValueError:
            st.error("Formato de hora de início inválido. Use HH:MM.")
    else:
        st.error("Produto ou Companhia inválidos. Verifique os valores.")

# Exibir os dados adicionados
if not st.session_state.data.empty:
    st.subheader("Dados de Bombeios Agendados")

    # Cria colunas para os dados e os botões de edição e remoção
    for index, row in st.session_state.data.iterrows():
        cols = st.columns([4, 1, 1])  # Ajuste a proporção conforme necessário
        with cols[0]:
            st.write(row.to_frame().T)  # Exibe a linha do DataFrame
            
        with cols[1]:
            if st.button(f"Editar", key=f"edit_{index}"):
                # Campos para edição
                edited_company = st.text_input("Companhia", value=row['Companhia'], key=f"edit_company_{index}")
                edited_product = st.text_input("Produto", value=row['Produto'], key=f"edit_product_{index}")
                edited_quota = st.number_input("Cota", min_value=0, step=1, value=row['Cota'], key=f"edit_quota_{index}")
                edited_start_time = st.text_input("Hora de Início (HH:MM)", value=row['Início'].strftime('%H:%M'), key=f"edit_start_time_{index}")

                if st.button("Salvar alterações", key=f"save_{index}"):
                    # Atualiza os dados no DataFrame
                    flow_rate = get_flow_rate(edited_product, edited_company)
                    if flow_rate:
                        try:
                            start_datetime = pd.to_datetime(tomorrow.strftime("%Y-%m-%d") + " " + edited_start_time)
                            end_datetime, duration_str = calculate_end_time(start_datetime, edited_quota, flow_rate)

                            # Aplicar alterações
                            st.session_state.data.at[index, 'Companhia'] = edited_company
                            st.session_state.data.at[index, 'Produto'] = edited_product
                            st.session_state.data.at[index, 'Cota'] = edited_quota
                            st.session_state.data.at[index, 'Início'] = start_datetime
                            st.session_state.data.at[index, 'Fim'] = end_datetime
                            st.session_state.data.at[index, 'Duração'] = duration_str

                            # Salvar no CSV
                            save_data(st.session_state.data)
                            st.success("Alterações salvas com sucesso!")
                            st.experimental_rerun()  # Atualiza a página para refletir as mudanças
                        except ValueError:
                            st.error("Formato de hora de início inválido. Use HH:MM.")
                    else:
                        st.error("Produto ou Companhia inválidos. Verifique os valores.")

        with cols[2]:
            if st.button(f"Remover", key=f"remove_{index}"):
                st.session_state.data = st.session_state.data.drop(index).reset_index(drop=True)
                save_data(st.session_state.data)  # Salva os dados no CSV
                st.success(f"Bombeio da companhia {row['Companhia']} removido com sucesso!")
                st.experimental_rerun()  # Atualiza a página para refletir a mudança

    # Criar gráfico de Gantt usando Altair
    st.subheader("Gráfico Gantt de Bombeios")

    # Converte o DataFrame recalculado em gráfico
    chart_data = st.session_state.data

    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Início:T', axis=alt.Axis(format='%H:%M')),
        x2='Fim:T',
        y='Companhia:N',
        color='Produto:N',
        tooltip=['Companhia', 'Produto', 'Cota', 'Início:T', 'Fim:T', 'Duração']
    ).properties(width=800)

    # Exibe o gráfico
    st.altair_chart(chart)
else:
    st.write("Nenhum bombeio agendado.")

