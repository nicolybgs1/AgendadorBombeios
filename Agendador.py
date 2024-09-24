import streamlit as st
import pandas as pd
import altair as alt

# Título da página
st.title("Agendador de Bombeios")

# Exibir a data de amanhã no início da página
tomorrow = pd.to_datetime("today") + pd.Timedelta(days=1)
st.markdown(f"**Data:** {tomorrow.strftime('%d/%m/%Y')}")

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

# Inicializa a lista de dados na sessão
if "data" not in st.session_state:
    st.session_state.data = []

# Cálculo inicial de fim e duração
if st.button("Adicionar Bombeio"):
    flow_rate = get_flow_rate(product, company)
    
    if flow_rate:
        try:
            # Aqui, a hora de início deve ser convertida corretamente
            start_datetime = pd.to_datetime(tomorrow.strftime("%Y-%m-%d") + " " + start_time)
            end_datetime, duration_str = calculate_end_time(start_datetime, quota, flow_rate)

            # Verifica se o bombeio já existe e atualiza ou adiciona
            existing = next((item for item in st.session_state.data if item['Companhia'] == company and item['Produto'] == product), None)
            if existing:
                # Atualiza os dados existentes
                existing['Cota'] = quota
                existing['Início'] = start_datetime
                existing['Fim'] = end_datetime
                existing['Duração'] = duration_str
            else:
                # Adiciona novo bombeio
                st.session_state.data.append({
                    "Companhia": company,
                    "Produto": product,
                    "Cota": quota,
                    "Início": start_datetime,
                    "Fim": end_datetime,
                    "Duração": duration_str
                })
            st.success("Bombeio adicionado/atualizado com sucesso!")
        except ValueError:
            st.error("Formato de hora de início inválido. Use HH:MM.")
    else:
        st.error("Produto ou Companhia inválidos. Verifique os valores.")

# Exibir os dados adicionados
if st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("Dados de Bombeios Agendados")

    # Permitir edição dos dados
    edited_df = st.data_editor(df, key="data_editor", use_container_width=True)

    # Atualizar dados após edição
    st.session_state.data = edited_df.to_dict(orient='records')

    # Criar gráfico de Gantt usando Altair
    st.subheader("Gráfico Gantt de Bombeios")

    chart = alt.Chart(edited_df).mark_bar().encode(
        x=alt.X('Início:T', axis=alt.Axis(format='%H:%M')),
        x2='Fim:T',
        y='Companhia:N',
        color='Produto:N',
        tooltip=['Companhia', 'Produto', 'Cota', 'Início:T', 'Fim:T', 'Duração']
    ).properties(
        title='Gráfico Gantt'
    )

    st.altair_chart(chart, use_container_width=True)

