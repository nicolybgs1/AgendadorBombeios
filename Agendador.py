#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

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

# Calcular a hora de fim com base na cota e taxa de bombeio
flow_rate = get_flow_rate(product, company)
if flow_rate:
    try:
        start_datetime = pd.to_datetime(tomorrow.strftime("%Y-%m-%d") + " " + start_time)
        duration_hours = quota / flow_rate  # Duração em horas
        end_datetime = start_datetime + pd.Timedelta(hours=duration_hours)

        # Formatar a hora de fim
        end_time = end_datetime.strftime("%H:%M")
        st.text(f"Hora de Fim Calculada: {end_time}")
    except ValueError:
        st.error("Formato de hora de início inválido. Use HH:MM.")
        start_datetime = pd.NaT
        end_datetime = pd.NaT
        end_time = None
else:
    st.error("Produto ou Companhia inválidos. Verifique os valores.")

# Botão para adicionar a entrada de dados
if st.button("Adicionar Bombeio"):
    if "data" not in st.session_state:
        st.session_state.data = []

    tomorrow = pd.to_datetime("today") + pd.Timedelta(days=1)

    if pd.notna(start_datetime) and pd.notna(end_datetime):
        # Cálculo e formatação da duração como HH:MM
        duration = end_datetime - start_datetime
        duration_str = f"{duration.components.hours:02}:{duration.components.minutes:02}"

        st.session_state.data.append({
            "Companhia": company,
            "Produto": product,
            "Cota": quota,
            "Início": start_datetime,
            "Fim": end_datetime,
            "Duração": duration_str
        })
        st.success("Bombeio adicionado com sucesso!")
    else:
        st.error("Erro ao adicionar o bombeio.")

# Exibir os dados adicionados
if "data" in st.session_state:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("Dados de Bombeios Agendados")
    st.write(df)
        
    # Garantir que as colunas 'Início' e 'Fim' estão no formato datetime
    df['Início'] = pd.to_datetime(df['Início'], errors='coerce')
    df['Fim'] = pd.to_datetime(df['Fim'], errors='coerce')

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

    
