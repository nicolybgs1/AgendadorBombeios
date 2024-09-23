#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
import altair as alt
import re

# Título da página
st.title("Agendador de Bombeios")

# Exibir a data de amanhã no início da página
tomorrow = pd.to_datetime("today") + pd.Timedelta(days=1)
st.markdown(f"**Data:** {tomorrow.strftime('%d/%m/%Y')}")

# Inputs para coletar os dados
company = st.text_input("Companhia")
product = st.text_input("Produto")
quota = st.number_input("Cota", min_value=0.0, step=0.1)
start_time = st.text_input("Hora de Início (HH:MM)", "00:00")
end_time = st.text_input("Hora de Fim (HH:MM)", "00:00")

# Validação do formato das horas (HH:MM)
time_format = re.compile(r"^\d{2}:\d{2}$")
if not time_format.match(start_time) or not time_format.match(end_time):
    st.error("Formato de hora inválido. Use o formato HH:MM.")
else:
    # Botão para adicionar a entrada de dados
    if st.button("Adicionar Bombeio"):
        # Adiciona os dados em um DataFrame
        if "data" not in st.session_state:
            st.session_state.data = []

        # Combinar a data de amanhã com as horas de início e fim
        tomorrow = pd.to_datetime("today") + pd.Timedelta(days=1)

        # Converter as horas de texto para datetime apenas para calcular a diferença
        try:
            start_datetime = pd.to_datetime(tomorrow.strftime("%Y-%m-%d") + " " + start_time)
            end_datetime = pd.to_datetime(tomorrow.strftime("%Y-%m-%d") + " " + end_time)

            # Calcular a duração
            duration = end_datetime - start_datetime
        except ValueError:
            st.error("Erro ao converter as horas. Certifique-se de que as horas estejam corretas.")
            start_datetime = pd.NaT
            end_datetime = pd.NaT
            duration = None

        # Adicionar ao estado da sessão apenas se as datas forem válidas
        if pd.notna(start_datetime) and pd.notna(end_datetime):
            # Armazenar os valores de `datetime` para cálculos e os valores de `string` para exibição
            start_time_str = start_time  # Valor original em formato string
            end_time_str = end_time      # Valor original em formato string

            st.session_state.data.append({
                "Companhia": company,
                "Produto": product,
                "Cota": quota,
                "Início_Texto": start_time_str,  # Para exibição no gráfico
                "Fim_Texto": end_time_str,       # Para exibição no gráfico
                "Duração": duration
            })
            st.success("Bombeio adicionado com sucesso!")
        else:
            st.error("Erro ao adicionar o bombeio.")

# Exibir os dados adicionados
if "data" in st.session_state:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("Dados de Bombeios Agendados")
    st.write(df)

    if df.empty:
        st.warning("Nenhum dado disponível para exibir o gráfico.")
    else:
        # Criar gráfico de Gantt usando Altair (com 'Início_Texto' e 'Fim_Texto')
        st.subheader("Gráfico Gantt de Bombeios")

        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('Início_Texto:O', axis=alt.Axis(title='Hora de Início')),  # Usando texto no gráfico
            x2='Fim_Texto:O',  # Usando texto no gráfico
            y='Companhia:N',
            color='Produto:N',
            tooltip=['Companhia', 'Produto', 'Cota', 'Início_Texto', 'Fim_Texto', 'Duração']
        ).properties(
            title='Gráfico Gantt'
        )

        st.altair_chart(chart, use_container_width=True)


# In[4]:
