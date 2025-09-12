import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, timedelta
from departamentos import departamentos
from colaboradores_por_departamento import colaboradores_por_departamento
import os
from pymongo import MongoClient

# Remover a importação do mongodb.py
# from mongodb import user, secure_password, string

# Configuração do MongoDB Atlas com segredos do Streamlit
def get_database():
    try:
        # Tentar usar os segredos do Streamlit Cloud
        try:
            user = st.secrets["mongodb"]["username"]
            password = st.secrets["mongodb"]["password"]
            cluster_url = st.secrets["mongodb"]["cluster_url"]
            connection_string = f"mongodb+srv://{user}:{password}@{cluster_url}/?retryWrites=true&w=majority"
            
            # Conectar ao MongoDB Atlas
            client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Teste de conexão com timeout
            client.admin.command('ping')
            st.success("Conectado ao MongoDB Atlas com sucesso!")
            
            # Acessar o banco de dados 'alfredo_db'
            return client['alfredo_db']
            
        except Exception as e:
            st.warning(f"Não foi possível conectar usando segredos do Streamlit: {str(e)}")
            
            # Fallback para credenciais locais
            try:
                from mongodb import user, secure_password, string
                connection_string = string.replace('<db_password>', secure_password)
                
                # Conectar ao MongoDB Atlas com credenciais locais
                client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
                
                # Teste de conexão com timeout
                client.admin.command('ping')
                st.success("Conectado ao MongoDB Atlas com credenciais locais!")
                
                # Acessar o banco de dados 'alfredo_db'
                return client['alfredo_db']
            except Exception as local_error:
                st.error(f"Erro ao conectar com credenciais locais: {str(local_error)}")
                return None
            
    except Exception as e:
        st.error(f"Erro ao conectar ao MongoDB Atlas: {str(e)}")
        st.warning("Usando banco de dados local como fallback.")
        return None

# Função para carregar eventos do MongoDB
# Função para carregar eventos do MongoDB
def carregar_eventos():
    try:
        db = get_database()
        if db is not None:  # Corrigido: usar 'is not None' em vez de 'if db'
            # Obter a coleção 'eventos' (será criada se não existir)
            collection = db['eventos']
            
            # Buscar todos os eventos, excluindo o campo _id
            eventos_cursor = collection.find({}, {'_id': 0})
            
            # Converter para lista e garantir que todos os dados sejam serializáveis
            eventos = []
            for evento in eventos_cursor:
                # Converter qualquer ObjectId para string
                evento_serializable = {}
                for chave, valor in evento.items():
                    from bson import ObjectId
                    if isinstance(valor, ObjectId):
                        evento_serializable[chave] = str(valor)
                    else:
                        evento_serializable[chave] = valor
                eventos.append(evento_serializable)
            
            if eventos:
                st.success(f"Carregados {len(eventos)} eventos do MongoDB com sucesso!")
                return eventos
            else:
                st.warning("Nenhum evento encontrado no MongoDB. Usando dados locais.")
                import banco_eventos
                return banco_eventos.eventos_db
        else:
            # Fallback para o arquivo local se não conseguir conectar ao MongoDB
            import banco_eventos
            st.warning("Usando banco de dados local como fallback.")
            return banco_eventos.eventos_db
    except Exception as e:
        st.error(f"Erro ao carregar eventos: {e}")
        # Garantir que sempre retorne uma lista, mesmo em caso de erro
        import banco_eventos
        return banco_eventos.eventos_db

# Função para salvar eventos no MongoDB
# Função para salvar eventos no MongoDB
def salvar_eventos():
    try:
        db = get_database()
        if db is not None:  # Corrigido: usar 'is not None' em vez de 'if db'
            collection = db['eventos']
            # Limpar todos os eventos existentes
            collection.delete_many({})
            
            # Garantir que todos os eventos sejam serializáveis
            eventos_serializaveis = []
            for evento in st.session_state.events:
                # Converter qualquer ObjectId para string
                evento_serializable = {}
                for chave, valor in evento.items():
                    from bson import ObjectId
                    if isinstance(valor, ObjectId):
                        evento_serializable[chave] = str(valor)
                    else:
                        evento_serializable[chave] = valor
                eventos_serializaveis.append(evento_serializable)
            
            # Inserir os eventos atuais
            if eventos_serializaveis:
                result = collection.insert_many(eventos_serializaveis)
                st.success(f"Eventos salvos com sucesso! {len(result.inserted_ids)} eventos gravados no MongoDB.")
            else:
                st.warning("Nenhum evento para salvar.")
        else:
            st.error("Não foi possível conectar ao banco de dados. Alterações não foram salvas.")
            # Tenta fazer um backup local como fallback
            try:
                import json
                import os
                from datetime import datetime
                
                backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(backup_dir, f"backup_local_{timestamp}.json")
                
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.events, f, ensure_ascii=False, indent=4)
                
                st.info(f"Backup local criado em {backup_file}")
            except Exception as backup_error:
                st.error(f"Erro ao criar backup local: {backup_error}")
    except Exception as e:
        st.error(f"Erro ao salvar eventos: {str(e)}")
        st.exception(e)  # Mostra o traceback completo do erro

# Função para salvar evento individual
def salvar_evento(evento):
    if 'events' not in st.session_state:
        st.session_state.events = []
    st.session_state.events.append(evento)
    salvar_eventos()

# Função para atualizar um evento existente
def atualizar_evento(idx, evento_atualizado):
    if 0 <= idx < len(st.session_state.events):
        st.session_state.events[idx] = evento_atualizado
        salvar_eventos()
        return True
    return False

# Função para excluir um evento
def excluir_evento(idx):
    if 0 <= idx < len(st.session_state.events):
        st.session_state.events.pop(idx)
        salvar_eventos()
        return True
    return False

# Configuração da página
st.set_page_config(
    page_title="Alfredo Augustinus",
    page_icon="icon.png",
    layout="wide",
)

# Layout do cabeçalho com colunas
col1, col2 = st.columns([1, 4])

with col1:
    st.image("alfred.png", width=150)

with col2:
    st.title("Alfredo Augustinus")
    st.subheader("Assistente para agendamento de reuniões e controle de indicador de participação")

with st.sidebar:
    st.image("redelius.png", width=200)

# Aplicar estilo CSS para centralizar imagens na sidebar
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] [data-testid="stImage"] {
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Inicializar o estado da sessão com eventos do MongoDB
if 'events' not in st.session_state:
    st.session_state.events = carregar_eventos()

# Sidebar para agendamento
with st.sidebar:
    st.header("Agendar Nova Reunião")
    
    # Seleção de departamento
    departamento = st.selectbox("Selecione o Departamento", departamentos)
    
    # Filtra colaboradores do departamento selecionado
    colaboradores_dept = [
        nome for nome, depts in colaboradores_por_departamento.items()
        if departamento in depts
    ]
    
    # Seleção de participantes
    participantes = st.multiselect(
        "Selecione os Participantes",
        colaboradores_dept
    )
    
    # Data e hora
    data = st.date_input("Data da Reunião", min_value=datetime.now().date())
    hora_inicio = st.time_input("Hora de Início")
    duracao = st.number_input("Duração (horas)", min_value=0.5, max_value=8.0, value=1.0, step=0.5)
    
    # Detalhes da reunião
    titulo = st.text_input("Título da Reunião")
    descricao = st.text_area("Descrição")
    
    # Botão para agendar
    if st.button("Agendar Reunião"):
        if not titulo or not participantes:
            st.error("Por favor, preencha o título e selecione pelo menos um participante.")
        elif hora_inicio.hour < 8 or (hora_inicio.hour + int(duracao)) > 18:
            st.error("Por favor, agende reuniões apenas em horário comercial (8h às 18h).")
        else:
            # Calcula hora de término
            inicio_dt = datetime.combine(data, hora_inicio)
            fim_dt = inicio_dt + timedelta(hours=duracao)
            
            # Verifica se já existe reunião agendada para o mesmo horário
            conflito = False
            for evento in st.session_state.events:
                evento_inicio = datetime.fromisoformat(evento['start'].replace('Z', '+00:00'))
                evento_fim = datetime.fromisoformat(evento['end'].replace('Z', '+00:00'))
                
                if (inicio_dt >= evento_inicio and inicio_dt < evento_fim) or \
                   (fim_dt > evento_inicio and fim_dt <= evento_fim) or \
                   (inicio_dt <= evento_inicio and fim_dt >= evento_fim):
                    conflito = True
                    st.error(f"""Conflito de horário detectado:
                             \nReunião: {evento['title']}
                             \nHorário: {evento_inicio.strftime('%H:%M')} - {evento_fim.strftime('%H:%M')}""")
                    break
            
            if not conflito:
                # Adiciona novo evento
                novo_evento = {
                    "title": titulo,
                    "start": inicio_dt.isoformat(),
                    "end": fim_dt.isoformat(),
                    "description": f"Departamento: {departamento}\nParticipantes: {', '.join(participantes)}\n\n{descricao}"
                }
                
                salvar_evento(novo_evento)
                st.success("Reunião agendada com sucesso!")
                st.rerun()

# Configurações do calendário
calendar_options = {
    "initialView": "dayGridMonth",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay,listWeek"
    },
    "editable": True,
    "selectable": True,
    "locale": "pt-br",
    "eventDisplay": "block",
    "displayEventTime": True,
    "eventTimeFormat": {
        "hour": "2-digit",
        "minute": "2-digit",
        "hour12": False
    },
    "businessHours": {
        "daysOfWeek": [1, 2, 3, 4, 5],
        "startTime": "08:00",
        "endTime": "18:00"
    },
    "slotMinTime": "08:00:00",
    "slotMaxTime": "18:00:00",
    "firstDay": 0,
    "weekends": True,
    "dayMaxEvents": 3,  # Mostra apenas 2 eventos por dia
    "moreLinkText": "mais eventos",  # Texto do botão em português
    "moreLinkClick": "popover",  # Abre um popover ao clicar no botão
    "views": {
        "dayGrid": {
            "dayMaxEvents": 2  # Confirma a configuração para a visualização de grade
        }
    }
}

# Adicione estilos CSS personalizados para o calendário
st.markdown("""
    <style>
        .fc-event {
            border: none !important;
            background-color: #4D268C !important;
            color: white !important;
            padding: 3px !important;
            border-radius: 3px !important;
            font-size: 0.6em !important;  /* Reduz o tamanho da fonte dos eventos */
        }
        .fc-event:hover {
            background-color: #5D369C !important;
        }
        .fc-toolbar-title {
            color: #4D268C !important;
        }
        .fc-button-primary {
            background-color: #4D268C !important;
            border-color: #4D268C !important;
        }
        .fc-button-primary:hover {
            background-color: #5D369C !important;
            border-color: #5D369C !important;
        }
        .fc-day-today {
            background-color: #F5F3FA !important;
        }
        .fc-event-title {
            white-space: normal !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            font-size: 0.6em !important;  /* Reduz o tamanho da fonte dos títulos */
        }
        .fc-event-time {
            font-size: 0.6em !important;  /* Reduz o tamanho da fonte do horário */
        }
    </style>
""", unsafe_allow_html=True)

# Exibe o calendário com os eventos
events = st.session_state.get('events', [])
try:
    calendar(events=events, options=calendar_options)
except Exception as e:
    st.error(f"Erro ao carregar o calendário: {str(e)}")
    st.info("Por favor, verifique se a biblioteca streamlit-calendar está instalada corretamente")

# Exibe lista de reuniões agendadas
if events:
    col_header1, col_header2 = st.columns([2, 1])
    with col_header1:
        st.header("Reuniões Agendadas")
    with col_header2:
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        
        # Usa o mesmo estado de sessão que a página de Controle
        if 'mes_selecionado' not in st.session_state:
            st.session_state.mes_selecionado = meses[datetime.now().month - 1]
            
        mes_selecionado = st.selectbox(
            "Filtrar por Mês",
            meses,
            index=meses.index(st.session_state.mes_selecionado),
            key="filtro_mes",
            on_change=lambda: setattr(st.session_state, 'mes_selecionado', meses[meses.index(st.session_state.filtro_mes)])
        )
    
    # Filtra eventos do mês selecionado
    mes_numero = meses.index(mes_selecionado) + 1
    eventos_filtrados = [
        (idx, evento) for idx, evento in enumerate(events)
        if datetime.fromisoformat(evento['start'].replace('Z', '+00:00')).month == mes_numero
    ]
    
    # Na seção de exibição de eventos, ajuste os botões:
    if eventos_filtrados:
        for idx, evento in eventos_filtrados:
            with st.expander(f"{evento['title']} - {datetime.fromisoformat(evento['start'][:19]).strftime('%d/%m/%Y %H:%M')}"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Editar", key=f"edit_button_{idx}"):
                        st.session_state.editing_event = idx
                        st.session_state.edit_title = evento['title']
                        st.session_state.edit_start = datetime.fromisoformat(evento['start'])
                        st.session_state.edit_end = datetime.fromisoformat(evento['end'])
                        st.session_state.edit_description = evento['description'].split('\n\n')[1] if '\n\n' in evento['description'] else ''
                        st.session_state.edit_dept = evento['description'].split('\n')[0].replace('Departamento: ', '')
                        st.session_state.edit_participants = evento['description'].split('\n')[1].replace('Participantes: ', '')
                        st.rerun()
                
                with col2:
                    # Modificação na lógica de cancelamento
                    if 'confirmar_cancelamento' not in st.session_state:
                        st.session_state.confirmar_cancelamento = {}
                    
                    if st.button("Cancelar Reunião", key=f"cancel_button_{idx}"):
                        st.session_state.confirmar_cancelamento[idx] = True
                    
                    if st.session_state.confirmar_cancelamento.get(idx, False):
                        if st.button("Confirmar Cancelamento", key=f"confirm_cancel_{idx}"):
                            excluir_evento(idx)
                            st.session_state.confirmar_cancelamento.pop(idx, None)
                            st.success("Reunião cancelada com sucesso!")
                            st.rerun()
                        if st.button("Desistir", key=f"desistir_cancel_{idx}"):
                            st.session_state.confirmar_cancelamento.pop(idx, None)
                            st.rerun()

                st.write(evento['description'])

    # Modal de edição
    if 'editing_event' in st.session_state:
        st.sidebar.header("Editar Reunião")
        
        # Campos do formulário de edição com chaves únicas
        novo_titulo = st.sidebar.text_input("Título da Reunião", 
                                      value=st.session_state.edit_title, 
                                      key=f"edit_title_{st.session_state.editing_event}")
        
        nova_data = st.sidebar.date_input("Data da Reunião", 
                                    value=st.session_state.edit_start.date(), 
                                    key=f"edit_date_{st.session_state.editing_event}")
        
        nova_hora = st.sidebar.time_input("Hora de Início", 
                                    value=st.session_state.edit_start.time(), 
                                    key=f"edit_time_{st.session_state.editing_event}")
        
        nova_duracao = st.sidebar.number_input("Duração (horas)", 
                                         min_value=0.5, 
                                         max_value=8.0, 
                                         value=float((st.session_state.edit_end - st.session_state.edit_start).total_seconds() / 3600),
                                         step=0.5,
                                         key=f"edit_duration_{st.session_state.editing_event}")
        
        novo_dept = st.sidebar.text_input("Departamento", 
                                    value=st.session_state.edit_dept, 
                                    key=f"edit_dept_{st.session_state.editing_event}")
        
        novos_participantes = st.sidebar.text_input("Participantes", 
                                              value=st.session_state.edit_participants, 
                                              key=f"edit_participants_{st.session_state.editing_event}")
        
        nova_descricao = st.sidebar.text_area("Descrição", 
                                        value=st.session_state.edit_description, 
                                        key=f"edit_description_{st.session_state.editing_event}")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Salvar Alterações", key="save_edit"):
                inicio_dt = datetime.combine(nova_data, nova_hora)
                fim_dt = inicio_dt + timedelta(hours=nova_duracao)
                
                evento_atualizado = {
                    "title": novo_titulo,
                    "start": inicio_dt.isoformat(),
                    "end": fim_dt.isoformat(),
                    "description": f"Departamento: {novo_dept}\nParticipantes: {novos_participantes}\n\n{nova_descricao}"
                }
                
                atualizar_evento(st.session_state.editing_event, evento_atualizado)
                del st.session_state.editing_event
                st.success("Reunião atualizada com sucesso!")
                st.rerun()
        
        with col2:
            if st.button("Cancelar Edição", key="cancel_edit"):
                del st.session_state.editing_event
                st.rerun()

# Configuração de tema e cores
st.markdown(
    """
    <style>
        /* Cor primária para elementos principais */
        .stButton > button {
            background-color: #4D268C;
            color: white;
        }
        .stButton > button:hover {
            background-color: #5D369C;
        }
        
        /* Cores para sidebar */
        [data-testid="stSidebar"] {
            background-color: #F5F3FA;
        }
        
        /* Cores para headers */
        h1, h2, h3 {
            color: #4D268C;
        }
        
        /* Cores para links e elementos interativos */
        a {
            color: #4D268C;
        }
        
        /* Cores para elementos de sucesso e avisos */
        .stSuccess {
            background-color: #E8E3F5;
            border-left-color: #4D268C;
        }
        
        /* Cores para multiselect e selectbox */
        .stSelectbox, .stMultiSelect {
            border-color: #4D268C;
        }
        
        /* Cores para progress bar */
        .stProgress > div > div {
            background-color: #4D268C;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ...

# Adicione este código na sidebar ou em outra parte da interface
with st.sidebar:
    st.divider()
    st.subheader("Ferramentas de Diagnóstico")
    if st.button("Testar Conexão com MongoDB"):
        db = get_database()
        if db:
            try:
                # Tenta fazer uma operação simples
                collection = db['eventos']
                count = collection.count_documents({})
                st.success(f"Conexão bem-sucedida! Existem {count} eventos no banco de dados.")
            except Exception as e:
                st.error(f"Erro ao acessar a coleção: {str(e)}")
        else:
            st.error("Não foi possível estabelecer conexão com o MongoDB.")