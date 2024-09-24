import streamlit as st
import pandas as pd
import os
import altair as alt

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

# Inicializar o estado da sessão
if "data" not in st.session_state:
    st.session_state.data = load_data()

# Verificar se o DataFrame está vazio e inicializá-lo se necessário
if st.session_state.data is None or not isinstance(st.session_state.data, pd.DataFrame):
    st.session_state.data = pd.DataFrame(columns=["Companhia", "Produto", "Cota", "Início", "Fim", "Duração"])

# Formulário para adicionar um novo bombeio
with st.form(key='add_bomb_form'):
    company = st.text_input("Companhia")
    product = st.text_input("Produto")
    quota = st.number_input("Cota", min_value=0, step=1)
    start_time = st.text_input("Hora de Início (HH:MM)", "00:00")
    submit_button = st.form_submit_button(label='Adicionar Bombeio')

    # Adicionar Bombeio
    if submit_button:
        try:
            start_datetime = pd.to_datetime(start_time, format='%H:%M')
            end_datetime = start_datetime + pd.Timedelta(hours=1)  # Exemplo: 1 hora de duração
            new_bomb = {
                "Companhia": company,
                "Produto": product,
                "Cota": quota,
                "Início": start_datetime,
                "Fim": end_datetime,
                "Duração": "01:00"  # Exemplo de duração
            }
            st.session_state.data = st.session_state.data.append(new_bomb, ignore_index=True)
            save_data(st.session_state.data)  # Salva os dados no CSV
            st.success("Bombeio adicionado com sucesso!")
        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")

# Exibir os dados
if not st.session_state.data.empty:
    st.subheader("Dados de Bombeios Agendados")
    st.dataframe(st.session_state.data, use_container_width=True)
    
    # Verificar os tipos de dados
    st.write("Tipos de Dados:")
    st.write(st.session_state.data.dtypes)

    # Selecionar linha para editar
    selected_index = st.selectbox("Selecione o índice da linha para editar", st.session_state.data.index)

    # Formulário para editar o bombeio selecionado
    with st.form(key='edit_bomb_form'):
        edit_company = st.text_input("Companhia", value=st.session_state.data.at[selected_index, 'Companhia'])
        edit_product = st.text_input("Produto", value=st.session_state.data.at[selected_index, 'Produto'])
        edit_quota = st.number_input("Cota", min_value=0, step=1, value=st.session_state.data.at[selected_index, 'Cota'])
        edit_start_time = st.text_input("Hora de Início (HH:MM)", value=st.session_state.data.at[selected_index, 'Início'].strftime('%H:%M'))
        edit_submit_button = st.form_submit_button(label='Salvar Alterações')

        # Salvar as alterações
        if edit_submit_button:
            try:
                edit_start_datetime = pd.to_datetime(edit_start_time, format='%H:%M')
                end_datetime = edit_start_datetime + pd.Timedelta(hours=1)  # Ajustar conforme necessário
                st.session_state.data.at[selected_index, 'Companhia'] = edit_company
                st.session_state.data.at[selected_index, 'Produto'] = edit_product
                st.session_state.data.at[selected_index, 'Cota'] = edit_quota
                st.session_state.data.at[selected_index, 'Início'] = edit_start_datetime
                st.session_state.data.at[selected_index, 'Fim'] = end_datetime
                st.session_state.data.at[selected_index, 'Duração'] = "01:00"  # Atualizar a duração conforme necessário

                save_data(st.session_state.data)  # Salva os dados no CSV
                st.success("Bombeio atualizado com sucesso!")
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")

    # Criar gráfico Gantt usando Altair
    st.subheader("Gráfico Gantt de Bombeios")

    # Converte o DataFrame recalculado em gráfico
    chart_data = st.session_state.data.copy()  # Copia o DataFrame para evitar manipulação direta

    if not chart_data.empty:
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Início:T', axis=alt.Axis(format='%H:%M')),
            x2='Fim:T',
            y=alt.Y('Companhia:N', sort='-x'),
            color='Produto:N',
            tooltip=['Companhia', 'Produto', 'Cota', 'Início:T', 'Fim:T', 'Duração']
        ).properties(
            title='Gráfico Gantt'
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Nenhum dado para mostrar no gráfico.")

else:
    st.write("Nenhum bombeio agendado.")
