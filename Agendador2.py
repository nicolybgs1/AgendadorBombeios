from google.cloud import firestore
import streamlit as st

# Configurações
project_id = st.secrets["firebase"]["project_id"]
client_email = st.secrets["firebase"]["client_email"]
private_key = st.secrets["firebase"]["private_key"]
universe_domain = st.secrets["firebase"]["universe_domain"]

# Inicializa o cliente Firestore
db = firestore.Client(
    project=project_id,
    credentials={
        "type": "service_account",
        "project_id": project_id,
        "client_email": client_email,
        "private_key": private_key,
        "universe_domain": universe_domain
    }
)

# Tenta acessar a coleção
try:
    docs = db.collection('bombeios').stream()
    for doc in docs:
        print(f'{doc.id} => {doc.to_dict()}')
except Exception as e:
    print(f"Ocorreu um erro: {e}")
