import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import exchangelib
from exchangelib import Credentials, Account, DELEGATE

st.set_page_config(
    page_title="Assistente",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para limpar a sessão
def limpar_sessao():
    if st.sidebar.button("Desconectar"):
        for key in ['outlook_account', 'events']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Configuração da autenticação do Outlook
def inicializar_outlook():
    # Exibe status da conexão na sidebar
    with st.sidebar:
        if 'outlook_account' in st.session_state:
            st.success("✓ Conectado ao Outlook")
            st.write(f"Email: {st.session_state.outlook_account.primary_smtp_address}")
            if st.button("Desconectar", type="secondary"):
                for key in ['outlook_account', 'events']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Desconectado com sucesso!")
                st.rerun()
        else:
            st.warning("⚠ Não conectado")
            if st.button("Fazer Login", type="primary", key="btn_login"):
                st.session_state.show_login = True
                st.rerun()  # Força a atualização da página
    
    # Dialog de login
    if st.session_state.get('show_login', False):
        dialog = st.dialog("Login no Outlook")
        with dialog:
            st.subheader("Conecte-se ao Outlook")
            
            # Campos de login
            email = st.text_input("Email do Outlook", key="email_input")
            senha = st.text_input("Senha", type="password", key="senha_input")
            
            # Botões de ação
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Conectar", type="primary", key="btn_connect", use_container_width=True):
                    if not email or not senha:
                        st.error("Por favor, preencha email e senha!")
                    else:
                        try:
                            with st.spinner("Conectando ao Outlook..."):
                                credentials = Credentials(email, senha)
                                account = Account(
                                    primary_smtp_address=email,
                                    credentials=credentials,
                                    autodiscover=True,
                                    access_type=DELEGATE
                                )
                                # Testa a conexão
                                account.calendar.view()
                                st.session_state.outlook_account = account
                                st.session_state.show_login = False
                                st.success("✓ Conectado com sucesso!")
                                st.rerun()
                        except Exception as e:
                            erro = str(e)
                            if "unauthorized" in erro.lower():
                                st.error("❌ Email ou senha incorretos!")
                            elif "autodiscover" in erro.lower():
                                st.error("❌ Não foi possível encontrar a conta. Verifique o email.")
                            else:
                                st.error(f"❌ Erro na conexão: {erro}")
            
            with col_btn2:
                if st.button("Cancelar", type="secondary", key="btn_cancel", use_container_width=True):
                    st.session_state.show_login = False
                    st.rerun()

    return st.session_state.get('outlook_account')

# Função para sincronizar eventos do Outlook
def sincronizar_eventos_outlook():
    account = inicializar_outlook()
    if not account:
        return []
    
    try:
        eventos = []
        calendar = account.calendar
        data_atual = datetime.now()
        
        with st.spinner("Sincronizando eventos..."):
            # Busca eventos dos últimos 30 dias até 60 dias no futuro
            for item in calendar.view(
                start=data_atual - timedelta(days=30),
                end=data_atual + timedelta(days=60)
            ):
                eventos.append({
                    "title": item.subject,
                    "start": item.start.isoformat(),
                    "end": item.end.isoformat(),
                    "description": item.body or "",
                    "id": str(item.id),
                    "location": item.location or "",
                    "participants": ", ".join([a.email_address for a in item.required_attendees])
                })
        return eventos
    except Exception as e:
        st.error(f"Erro ao sincronizar eventos: {str(e)}")
        return []

# Função para criar evento no Outlook
def criar_evento_outlook(titulo, inicio, fim, notas, participantes=None, local=None):
    account = inicializar_outlook()
    if not account:
        return False
    
    try:
        calendar = account.calendar
        evento = calendar.new_event()
        evento.subject = titulo
        evento.start = inicio
        evento.end = fim
        evento.body = notas
        
        if participantes:
            for email in [e.strip() for e in participantes.split(',')]:
                if email:
                    evento.required_attendees.add(email)
        
        if local:
            evento.location = local
            
        evento.save()
        return True
    except Exception as e:
        st.error(f"Erro ao criar evento: {str(e)}")
        return False

def excluir_evento(idx, evento_id=None):
    try:
        if evento_id:
            account = inicializar_outlook()
            if account:
                try:
                    evento = account.calendar.get(id=evento_id)
                    evento.delete()
                except Exception as e:
                    st.error(f"Erro ao excluir evento do Outlook: {str(e)}")
                    return
        
        if idx < len(st.session_state.events):
            st.session_state.events.pop(idx)
            st.success("Evento excluído com sucesso!")
            st.rerun()
    except Exception as e:
        st.error(f"Erro ao excluir evento: {str(e)}")

st.header("Assistente de agendamento")
st.subheader("Ferramenta de assistência para agendamento de reuniões")

st.write("Olá! Sou o Assistente de Agendamento integrado com Outlook.")

# Botão para sincronizar com Outlook
if st.button("Sincronizar com Outlook"):
    eventos_outlook = sincronizar_eventos_outlook()
    if eventos_outlook:
        st.session_state.events = eventos_outlook
        st.success("Eventos sincronizados com sucesso!")

# Inicializa a lista de eventos na sessão se não existir
if 'events' not in st.session_state:
    st.session_state.events = []

# Formulário para adicionar novo evento
with st.sidebar:
    st.subheader("Adicionar Novo Evento")
    with st.form("novo_evento"):
        titulo = st.text_input("Título do Evento")
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data de Início")
            hora_inicio = st.time_input("Hora de Início")
        with col2:
            data_fim = st.date_input("Data de Término")
            hora_fim = st.time_input("Hora de Término")
        
        participantes = st.text_input("Participantes (emails separados por vírgula)")
        local = st.text_input("Local ou Link da Reunião")
        notas = st.text_area("Notas do Evento")
        
        # Adicione estas validações no formulário de novo evento
        if st.form_submit_button("Adicionar Evento"):
            if not titulo:
                st.error("O título do evento é obrigatório!")
            else:
                inicio = datetime.combine(data_inicio, hora_inicio)
                fim = datetime.combine(data_fim, hora_fim)
                
                if inicio >= fim:
                    st.error("A data/hora de início deve ser anterior à data/hora de término!")
                elif inicio < datetime.now():
                    st.warning("Atenção: Você está criando um evento no passado!")
                    confirmar_passado = True
                else:
                    confirmar_passado = False
                
                if not confirmar_passado or st.checkbox("Confirmar criação no passado", key="confirm_past"):
                    # Criar evento no Outlook
                    if criar_evento_outlook(titulo, inicio, fim, notas, participantes, local):
                        novo_evento = {
                            "title": titulo,
                            "start": inicio.isoformat(),
                            "end": fim.isoformat(),
                            "description": notas,
                            "location": local,
                            "participants": participantes
                        }
                        st.session_state.events.append(novo_evento)
                        st.success("Evento adicionado com sucesso!")
                        st.rerun()

    # Lista de eventos existentes
    st.subheader("Eventos Existentes")
    for idx, evento in enumerate(st.session_state.events):
        with st.expander(f"{evento['title']} - {evento['start'][:10]}"):
            if st.button("Excluir", key=f"del_{idx}"):
                st.session_state.events.pop(idx)
                st.rerun()
            
            if 'description' in evento:
                st.text("Notas:")
                st.write(evento['description'])

calendar_options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay,listWeek"
    },
    "editable": True,
    "selectable": True,
    "eventClick": {"enable": True},
    "eventDrop": {"enable": True},
    "eventResize": {"enable": True}
}

calendar(events=st.session_state.events, options=calendar_options)