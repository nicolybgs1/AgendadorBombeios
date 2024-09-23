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
end_time = st.text_input("Hora de Fim (HH:MM)", "00:00")

# Botão para adicionar a entrada de dados
if st.button("Adicionar Bombeio"):
    if "data" not in st.session_state:
        st.session_state.data = []

    tomorrow = pd.to_datetime("today") + pd.Timedelta(days=1)

    try:
        start_datetime = pd.to_datetime(tomorrow.strftime("%Y-%m-%d") + " " + start_time)
        end_datetime = pd.to_datetime(tomorrow.strftime("%Y-%m-%d") + " " + end_time)

        # Cálculo e formatação da duração como HH:MM
        duration = end_datetime - start_datetime
        duration_str = f"{duration.components.hours:02}:{duration.components.minutes:02}"
        
    except ValueError:
        st.error("Formato de hora inválido. Use HH:MM.")
        start_datetime = pd.NaT
        end_datetime = pd.NaT
        duration_str = None

    if pd.notna(start_datetime) and pd.notna(end_datetime):
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
    
# Botão para exportar os dados para Excel
if st.button("Exportar para Excel"):
    # Verifica se o DataFrame não está vazio
    if not df.empty:
        # Cria um arquivo em memória
        output = BytesIO()

        # Usando ExcelWriter com 'openpyxl' para escrever o arquivo Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Bombeios')
        
        # Move o ponteiro do arquivo para o início
        output.seek(0)

        # Fornece o arquivo para download
        st.download_button(
            label="Baixar Excel",
            data=output,
            file_name="bombeios_agendados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Não há dados para exportar.")

