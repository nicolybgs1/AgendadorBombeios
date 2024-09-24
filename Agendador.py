#!/usr/bin/env python
# coding: utf-8

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

# Função para calcular a hora de fim e a duração
def calculate_end_time_and_duration(row):
    flow_rate = get_flow_rate(row['Produto'], row['Companhia'])
    
    if flow_rate:
        try:
            start_datetime = pd.to_datetime(tomorrow.strftime("%Y-%m-%d") + " " + row['Início'])
            duration_hours = row['Cota'] / flow_rate  # Duração em horas
            end_datetime = start_datetime + pd.Timedelta(hours=duration_hours)
            row['Fim'] = end_datetime.strftime("%H:%M")
            duration = end_datetime - start_datetime
            row['Duração'] = f"{duration.components.hours:02}:{duration.components.minutes:02}"
        except ValueError:
            st.error("Formato de hora de início inválido. Use HH:MM.")
            row['Fim'] = None
            row['Duração'] = None
    return row

# Botão para adicionar a entrada de dados
if st.button("Adicionar Bombeio"):
    if "data" not in st.session_state:
        st.session_state.data = []

    tomorrow = pd.to_datetime("today") + pd.Timedelta(days=1)

    new_data = {
        "Companhia": company,
        "Produto": product,
        "Cota": quota,
        "Início": start_time,
        "Fim": "",
        "Duração": ""
    }

    st.session_state.data.append(new_data)

    st.success("Bombeio adicionado com sucesso!")

# Exibir os dados adicionados e permitir edição
if "data" in st.session_state:
    df = pd.DataFrame(st.session_state.data)

    # Calcular automaticamente a hora de fim e a duração ao editar
    df = df.apply(calculate_end_time_and_duration, axis=1)

    # Exibir o editor de dados
    st.subheader("Dados de Bombeios Agendados (Editáveis)")
    edited_df = st.data_editor(df, use_container_width=True)

    # Atualizar o estado com o DataFrame editado
    st.session_state.data = edited_df.to_dict('records')

    # Criar gráfico de Gantt usando Altair
    st.subheader("Gráfico Gantt de Bombeios")

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Início:T', axis=alt.Axis(format='%H:%M')),
        x2='Fim:T',
        y='Companhia:N',
        color='Produto:N',
        tooltip=['Companhia', 'Produto', 'Cota', 'Início', 'Fim', 'Duração']
    ).properties(
        title='Gráfico Gantt'
    )

    st.altair_chart(chart, use_container_width=True)

    
