import streamlit as st
import requests
import base64
from datetime import datetime

# CONFIGURAÇÕES
API_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="Saberius AI", page_icon="🦁", layout="wide")

st.markdown("""
    <style>
    div.stButton > button:first-child {background-color: #004aad; color: white; border-radius: 8px; font-weight: bold; height: 50px; width: 100%;}
    .match-card {background-color: #e3f2fd; padding: 20px; border-radius: 15px; border: 2px solid #2196f3; text-align: center; margin-bottom: 20px;}
    .match-avatar {width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 4px solid white; box-shadow: 0px 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

def converter_imagem_para_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        base64_str = base64.b64encode(bytes_data).decode()
        return f"data:{uploaded_file.type};base64,{base64_str}"
    return None

# SESSÃO
if 'access_token' not in st.session_state:
    st.session_state['access_token'] = None
    st.session_state['usuario_nome'] = None
    st.session_state['usuario_tipo'] = None
    st.session_state['usuario_foto'] = None
if 'resultado_match' not in st.session_state:
    st.session_state['resultado_match'] = None

# TELA DE LOGIN / CADASTRO
if not st.session_state['access_token']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🦁 Saberius</h1>", unsafe_allow_html=True)
        tab_login, tab_criar = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
        
        with tab_login:
            email_login = st.text_input("Email", placeholder="ceo@saberius.com", key="login_email")
            senha_login = st.text_input("Senha", type="password", key="login_pass")
            if st.button("ENTRAR", key="btn_entrar"):
                try:
                    st.write(f"Tentando conectar em: {API_URL}/token") # <--- Debug 1
                    data = {"username": email_login, "password": senha_login}
                    
                    # Tenta bater na porta
                    response = requests.post(f"{API_URL}/token", data=data)
                    
                    st.write(f"Status da Resposta: {response.status_code}") # <--- Debug 2
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        st.session_state['access_token'] = token_data['access_token']
                        st.session_state['usuario_nome'] = email_login.split("@")[0].title()
                        st.session_state['usuario_tipo'] = token_data['tipo_usuario']
                        foto = token_data.get('foto_usuario')
                        st.session_state['usuario_foto'] = foto if foto else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
                        st.success("Entrando...")
                        st.rerun()
                    else:
                        st.error(f"Login recusado pela API. O servidor disse: {response.text}")
                except Exception as e:
                    # AQUI ESTÁ O SEGREDO: Mostra o erro real em vermelho
                    st.error(f"❌ ERRO TÉCNICO REAL: {e}")

        with tab_criar:
            col_foto, col_dados = st.columns([1, 2])
            base64_foto = None
            with col_foto:
                arquivo_foto = st.file_uploader("Foto", type=['png', 'jpg'])
                if arquivo_foto:
                    st.image(arquivo_foto, width=100)
                    base64_foto = converter_imagem_para_base64(arquivo_foto)
            with col_dados:
                novo_nome = st.text_input("Nome", key="cad_nome")
                novo_email = st.text_input("Email", key="cad_email")
                novo_senha = st.text_input("Senha", type="password", key="cad_senha")
                tipo = st.selectbox("Sou:", ["cliente", "mentor"], key="cad_tipo")
                esp = st.text_input("Especialidade", key="cad_esp") if "mentor" in tipo else None
                val = st.number_input("Valor Hora", min_value=0.0, key="cad_val") if "mentor" in tipo else None
            
            if st.button("CRIAR CONTA", key="btn_criar"):
                tipo_back = "cliente" if "cliente" in tipo else "mentor"
                payload = {"nome": novo_nome, "email": novo_email, "senha": novo_senha, "tipo": tipo_back, "especialidade": esp, "valor_hora": val, "foto": base64_foto}
                try:
                    if requests.post(f"{API_URL}/usuarios/", json=payload).status_code == 200: st.success("Criado! Faça login.")
                    else: st.error("Erro ao criar.")
                except: st.error("Erro conexão")

# ÁREA LOGADA
else:
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    c_foto, c_nome, c_logout = st.columns([1, 4, 1])
    with c_foto:
        if st.session_state['usuario_foto']:
            st.markdown(f'<img src="{st.session_state["usuario_foto"]}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;">', unsafe_allow_html=True)
    with c_nome: st.write(f"### Olá, {st.session_state['usuario_nome']}")
    with c_logout:
        if st.button("Sair 🚪"): st.session_state['access_token'] = None; st.rerun()

    if st.session_state['usuario_tipo'] == 'admin':
        st.write("### Painel CEO")
        try:
            dados = requests.get(f"{API_URL}/admin/resumo/", headers=headers).json()
            k1, k2, k3 = st.columns(3)
            k1.metric("Faturamento", f"R$ {dados['faturamento']}")
            k2.metric("Usuários", dados['usuarios'])
            k3.metric("Mentores", dados['mentores'])
        except: st.error("Erro API")
    else:
        tab_busca, tab_minhas = st.tabs(["🔍 Buscar", "📂 Minhas Mentorias"])
        with tab_busca:
            if st.session_state['usuario_tipo'] == 'cliente':
                txt = st.text_area("O que você precisa?", height=80)
                if st.button("BUSCAR"):
                    res = requests.post(f"{API_URL}/recomendacao/", json={"texto_usuario": txt}).json()
                    st.session_state['resultado_match'] = res
                
                if st.session_state['resultado_match']:
                    res = st.session_state['resultado_match']
                    if res.get('encontrou'):
                        foto_m = res.get('foto', "https://cdn-icons-png.flaticon.com/512/149/149071.png")
                        st.markdown(f"<div class='match-card'><img src='{foto_m}' class='match-avatar'><h3>{res['nome']}</h3><p>{res['motivo']}</p><h4>R$ {res['valor']}</h4></div>", unsafe_allow_html=True)
                        if st.button("Agendar"):
                            requests.post(f"{API_URL}/transacoes/", json={"mentor_id": res['id'], "valor": res['valor'], "data_agendada": str(datetime.now())}, headers=headers)
                            st.success("Agendado!")
                    else: st.warning("Nenhum mentor encontrado.")
            else: st.info("Painel do Mentor")
        
        with tab_minhas:
            try:
                agendamentos = requests.get(f"{API_URL}/minhas-transacoes/", headers=headers).json()
                for a in agendamentos: st.write(f"📅 {a['data'][:10]} - {a['nome_outro_lado']} (R$ {a['valor']})")
            except: pass