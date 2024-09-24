# Exibir os dados adicionados
if not st.session_state.data.empty:
    st.subheader("Dados de Bombeios Agendados")

    # Exibir o DataFrame diretamente na interface
    st.dataframe(st.session_state.data)

    # Cria colunas para os dados e os botões de edição e remoção
    for index, row in st.session_state.data.iterrows():
        cols = st.columns([4, 1, 1])  # Ajuste a proporção conforme necessário
        with cols[0]:
            st.write(row.to_frame().T)  # Exibe a linha do DataFrame
        with cols[1]:
            if st.button(f"Editar", key=f"edit_{index}"):
                # Implementar lógica de edição aqui
                with st.form(key=f"form_edit_{index}"):
                    edited_company = st.text_input("Companhia", value=row['Companhia'])
                    edited_product = st.text_input("Produto", value=row['Produto'])
                    edited_quota = st.number_input("Cota", min_value=0, step=1, value=row['Cota'])
                    edited_start_time = st.text_input("Hora de Início (HH:MM)", value=row['Início'].strftime('%H:%M'))

                    submit_button = st.form_submit_button(label="Salvar alterações")
                    if submit_button:
                        # Atualiza os dados no DataFrame
                        st.session_state.data.at[index, 'Companhia'] = edited_company
                        st.session_state.data.at[index, 'Produto'] = edited_product
                        st.session_state.data.at[index, 'Cota'] = edited_quota
                        st.session_state.data.at[index, 'Início'] = pd.to_datetime(
                            tomorrow.strftime("%Y-%m-%d") + " " + edited_start_time)
                        
                        # Recalcula o fim e a duração
                        flow_rate = get_flow_rate(edited_product, edited_company)
                        if flow_rate:
                            end_datetime, duration_str = calculate_end_time(st.session_state.data.at[index, 'Início'], edited_quota, flow_rate)
                            st.session_state.data.at[index, 'Fim'] = end_datetime
                            st.session_state.data.at[index, 'Duração'] = duration_str

                        # Salvar no CSV
                        save_data(st.session_state.data)
                        st.success("Alterações salvas com sucesso!")
                        st.experimental_rerun()  # Atualiza a página para refletir as mudanças

        with cols[2]:
            if st.button(f"Remover", key=f"remove_{index}"):
                st.session_state.data = st.session_state.data.drop(index).reset_index(drop=True)
                save_data(st.session_state.data)  # Salva os dados no CSV
                st.success(f"Bombeio da companhia {row['Companhia']} removido com sucesso!")
                st.experimental_rerun()  # Atualiza a página para refletir a mudança

    # Recalcular dados após edição
    recalculated_data = []
    for index, row in st.session_state.data.iterrows():
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

