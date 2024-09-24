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
            st.experimental_rerun()  # Recarrega a página para refletir a mudança
        except ValueError:
            st.error("Formato de hora de início inválido. Use HH:MM.")
    else:
        st.error("Produto ou Companhia inválidos. Verifique os valores.")

# Exibir os dados adicionados
if not st.session_state.data.empty:
    st.subheader("Dados de Bombeios Agendados")
    df = st.session_state.data.copy()  # Cria uma cópia do DataFrame para edição

    # Editar ou remover linhas
    for index, row in df.iterrows():
        with st.expander(f"Bombeio {index + 1}: {row['Companhia']}"):
            # Exibe campos editáveis para cada coluna
            companhia_edit = st.text_input(f"Companhia {index+1}", row['Companhia'], key=f"companhia_{index}")
            produto_edit = st.text_input(f"Produto {index+1}", row['Produto'], key=f"produto_{index}")
            cota_edit = st.number_input(f"Cota {index+1}", value=int(row['Cota']), min_value=0, step=1, key=f"cota_{index}")
            inicio_edit = st.text_input(f"Início {index+1} (HH:MM)", row['Início'].strftime("%H:%M"), key=f"inicio_{index}")

            # Botão para salvar edições
            if st.button(f"Salvar alterações {index+1}", key=f"salvar_{index}"):
                try:
                    # Atualiza os dados editados
                    start_datetime = pd.to_datetime(tomorrow.strftime("%Y-%m-%d") + " " + inicio_edit)
                    flow_rate = get_flow_rate(produto_edit, companhia_edit)
                    if flow_rate:
                        end_datetime, duration_str = calculate_end_time(start_datetime, cota_edit, flow_rate)

                        # Atualiza o DataFrame com os novos valores
                        st.session_state.data.loc[index, "Companhia"] = companhia_edit
                        st.session_state.data.loc[index, "Produto"] = produto_edit
                        st.session_state.data.loc[index, "Cota"] = cota_edit
                        st.session_state.data.loc[index, "Início"] = start_datetime
                        st.session_state.data.loc[index, "Fim"] = end_datetime
                        st.session_state.data.loc[index, "Duração"] = duration_str

                        # Salvar no CSV
                        save_data(st.session_state.data)
                        st.success("Alterações salvas com sucesso!")
                        st.experimental_rerun()  # Recarrega a página para refletir a mudança
                    else:
                        st.error("Taxa de bombeio não encontrada para o produto ou companhia.")
                except ValueError:
                    st.error("Formato de hora de início inválido. Use HH:MM.")

            # Botão para remover bombeio
            if st.button(f"Remover bombeio {index+1}", key=f"remover_{index}"):
                st.session_state.data = st.session_state.data.drop(index).reset_index(drop=True)
                save_data(st.session_state.data)  # Salva os dados no CSV
                st.success(f"Bombeio da companhia {row['Companhia']} removido com sucesso!")
                st.experimental_rerun()  # Recarrega a página para refletir a mudança

    # Recalcular dados após edição
    recalculated_data = []
    for index, row in df.iterrows():
        flow_rate = get_flow_rate(row['Produto'], row['Companhia'])
        try:
            # Converte a hora de início para datetime
            start_datetime = pd.to_datetime(row['Início'])

            if flow_rate is not None:
                # Recalcula hora de fim e duração
                end_datetime, duration_str = calculate_end_time(start_datetime, row['Cota'], flow_rate)

                # Adiciona os dados recalculados
                recalculated_data.append({
                    "Companhia": row['Companhia'],
                    "Produto": row['Produto'],
                    "Cota": row['Cota'],
                    "Início": start_datetime,
                    "Fim": end_datetime,
                    "Duração": duration_str
                })
            else:
                # Mantém os dados se o fluxo não for válido
                recalculated_data.append(row.to_dict())  
        except Exception as e:
            st.error(f"Erro ao processar a hora de início: {e}")
            recalculated_data.append(row.to_dict())  # Mantém os dados se houver erro

    # Atualiza o estado da sessão com os dados recalculados
    st.session_state.data = pd.DataFrame(recalculated_data)
    save_data(st.session_state.data)  # Salva os dados recalculados no CSV

    # Criar gráfico de Gantt usando Altair
    st.subheader("Gráfico Gantt de Bombeios")

    # Converte o DataFrame recalculado em gráfico
    chart_data = st.session_state.data
    
# Criar o gráfico com tooltip para exibir a duração
chart = alt.Chart(chart_data).mark_bar().encode(
    x=alt.X('Início:T', axis=alt.Axis(format='%H:%M')),
    x2='Fim:T',
    y='Companhia:N',
    color='Produto:N',
    tooltip=['Companhia', 'Produto', 'Cota', 'Início:T', 'Fim:T', 'Duração']  # Adiciona a duração no tooltip
).properties(width=800)

    # Exibe o gráfico
    st.altair_chart(chart)
else:
    st.write("Nenhum bombeio agendado.")



