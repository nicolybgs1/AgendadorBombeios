import streamlit as st
import pandas as pd
import altair as alt
import firebase_admin
from firebase_admin import credentials, firestore

# Configurar a página
st.set_page_config(layout="wide")

cred = credentials.Certificate({
    "type": st.secrets["firebase"]["type"],
    "project_id": st.secrets["firebase"]["project_id"],
    "private_key_id": st.secrets["firebase"]["private_key_id"],
    "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),
    "client_email": st.secrets["firebase"]["client_email"],
    "client_id": st.secrets["firebase"]["client_id"]
})

firebase_admin.initialize_app(cred)

# Função para carregar dados do Firestore
def load_data():
    docs = db.collection('bombeios').stream()
    data = []
    for doc in docs:
        data.append(doc.to_dict())
    return pd.DataFrame(data)

# Função para salvar dados no Firestore
def save_data(df):
    for index, row in df.iterrows():
        doc_ref = db.collection('bombeios').document(f"{row['Início']}_{row['Companhia']}")
        doc_ref.set(row.to_dict())

# Configura o layout da página
st.set_page_config(layout="wide")

# Título da página
st.title("Agendador de Bombeios")

# Adicionar um seletor de data para o filtro
data_selecionada = st.date_input("Selecione uma data", pd.to_datetime("today"))

# Exibir a data selecionada no início da página
st.markdown(f"**Data Selecionada:** {data_selecionada.strftime('%d/%m/%Y')}")

# Lista de opções para Companhia e Produto
company_options = ["POO", "PET", "SIM", "PTS", "FIC", "CJ", "TCT", "TRR", "TSO", "RM", "OPL", "CRS", "TOR", "DM", "SHE"]
product_options = ["GAS", "S10", "S500", "QAV", "OC"]

# Inputs para coletar os dados com listas suspensas
company = st.selectbox("Companhia", company_options)  # Selectbox para escolher a companhia
product = st.selectbox("Produto", product_options)  # Selectbox para escolher o produto
quota = st.number_input("Cota", min_value=0, step=1)
start_time = st.text_input("Hora de Início (HH:MM)", "00:00")

# Função para calcular a taxa de bombeio
def get_flow_rate(product, company):
    if product == "GAS":
        return 500
    elif product == "S10":
        if company in ["POO", "PET"]:
            return 1200
        else:
            return 600
    elif product == "S500":
        return 560
    elif product == "QAV":
        return 240
    elif product == "OC":
        return 300
    else:
        return None  # Caso o produto não esteja definido

# Função para calcular a hora de fim e duração
def calculate_end_time(start_datetime, quota, flow_rate):
    duration_hours = quota / flow_rate  # Duração em horas
    end_datetime = start_datetime + pd.Timedelta(hours=duration_hours)
    duration_str = f"{int(duration_hours):02d}:{int((duration_hours - int(duration_hours)) * 60):02d}"  # Formato HH:MM
    return end_datetime, duration_str

# Inicializar o estado da sessão
if "data" not in st.session_state:
    st.session_state.data = load_data()

# Verificar se o DataFrame está vazio e inicializá-lo se necessário
if st.session_state.data is None or not isinstance(st.session_state.data, pd.DataFrame):
    st.session_state.data = pd.DataFrame(columns=["Companhia", "Produto", "Cota", "Início", "Fim", "Duração"])

# Cálculo inicial de fim e duração
if st.button("Adicionar Bombeio"):
    flow_rate = get_flow_rate(product, company)
    
    if flow_rate:
        try:
            # Combina a data selecionada com a hora de início inserida
            start_datetime = pd.to_datetime(data_selecionada.strftime("%Y-%m-%d") + " " + start_time)
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

# Exibir os dados adicionados filtrados pela data selecionada
if not st.session_state.data.empty:
    st.subheader(f"Dados de Bombeios Agendados para {data_selecionada.strftime('%d/%m/%Y')}")
    
    # Filtrar os dados com base na data selecionada
    df = st.session_state.data[st.session_state.data["Início"].dt.normalize() == pd.to_datetime(data_selecionada)]

    if df.empty:
        st.write("Nenhuma programação encontrada para a data selecionada.")
    else:
        # Variável para armazenar a linha em edição
        edit_index = st.session_state.get('edit_index', None)

        # Cria colunas para os dados e os botões
        for index, row in df.iterrows():
            cols = st.columns([4, 1, 1])  # Ajuste a proporção conforme necessário
            with cols[0]:
                st.write(row.to_frame().T)  # Exibe a linha do DataFrame
            with cols[1]:
                if st.button(f"Remover", key=f"remove_{index}"):
                    st.session_state.data = st.session_state.data.drop(index).reset_index(drop=True)
                    save_data(st.session_state.data)  # Salva os dados no CSV
                    st.success(f"Bombeio da companhia {row['Companhia']} removido com sucesso!")
            with cols[2]:
                if st.button(f"Editar", key=f"edit_{index}"):
                    st.session_state.edit_index = index

        # Verifica se há uma linha em edição
        if edit_index is not None and edit_index < len(df):
            st.subheader("Editar Bombeio")

            # Preenche os campos com os dados atuais da linha selecionada
            edit_company = st.text_input("Companhia", value=df.loc[edit_index, "Companhia"])
            edit_product = st.text_input("Produto", value=df.loc[edit_index, "Produto"])
            edit_quota = st.number_input("Cota", min_value=0, step=1, value=int(df.loc[edit_index, "Cota"]))
            edit_start_time = st.text_input("Hora de Início (HH:MM)", value=df.loc[edit_index, "Início"].strftime("%H:%M"))

            # Botão para salvar a edição
            if st.button("Salvar Edição"):
                try:
                    # Calcula novos valores com base nas edições
                    start_datetime = pd.to_datetime(df.loc[edit_index, "Início"].strftime("%Y-%m-%d") + " " + edit_start_time)
                    flow_rate = get_flow_rate(edit_product, edit_company)
                    end_datetime, duration_str = calculate_end_time(start_datetime, edit_quota, flow_rate)

                    # Atualiza a linha com os novos valores
                    st.session_state.data.loc[edit_index, "Companhia"] = edit_company
                    st.session_state.data.loc[edit_index, "Produto"] = edit_product
                    st.session_state.data.loc[edit_index, "Cota"] = edit_quota
                    st.session_state.data.loc[edit_index, "Início"] = start_datetime
                    st.session_state.data.loc[edit_index, "Fim"] = end_datetime
                    st.session_state.data.loc[edit_index, "Duração"] = duration_str

                    # Salva os dados editados no CSV
                    save_data(st.session_state.data)

                    # Exibe a mensagem de sucesso e limpa o índice de edição
                    st.success("Bombeio editado com sucesso!")
                    st.session_state.edit_index = None
                except ValueError:
                    st.error("Erro ao editar os dados. Verifique os valores inseridos.")

# Criar uma nova coluna com o nome da companhia e os horários de início e fim
if not st.session_state.data.empty:
    st.session_state.data["Companhia_Horarios"] = st.session_state.data.apply(
        lambda row: f"{row['Companhia']} ({row['Início'].strftime('%H:%M')} - {row['Fim'].strftime('%H:%M')})", axis=1)

# Criar gráfico de Gantt usando Altair
if not st.session_state.data.empty:
    st.subheader(f"Gráfico Gantt de Bombeios para {data_selecionada.strftime('%d/%m/%Y')}")

    # Filtrar os dados para o gráfico com base na data selecionada
    chart_data = st.session_state.data[st.session_state.data["Início"].dt.normalize() == pd.to_datetime(data_selecionada)]
    
    if chart_data.empty:
        st.write("Nenhum dado para o gráfico na data selecionada.")
    else:
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('Início:T', axis=alt.Axis(format='%H:%M')),
            x2='Fim:T',
            y=alt.Y('Companhia_Horarios:N', title='Companhia', sort='-x'),
            color=alt.Color('Produto:N', title='Produto', scale=alt.Scale(scheme='category10')),
            tooltip=['Companhia', 'Produto', 'Cota', 'Início', 'Fim', 'Duração']
        ).properties(
            title='Bombeios Agendados',
            width=800,
            height=400
        )
        st.altair_chart(chart, use_container_width=True)
else:
    st.write("Não há nenhum bombeio agendado.")
