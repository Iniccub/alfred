import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, timedelta
from departamentos import departamentos
from colaboradores_por_departamento import colaboradores_por_departamento
import banco_eventos
import os  # Manter apenas os imports necessários


# Função para carregar eventos
def carregar_eventos():
    try:
        return banco_eventos.eventos_db
    except Exception as e:
        st.error(f"Erro ao carregar eventos: {e}")
    return []

# Função para salvar eventos
def salvar_eventos_arquivo():
    try:
        with open('banco_eventos.py', 'w', encoding='utf-8') as f:
            f.write('eventos_db = [\n')
            for idx, evento in enumerate(st.session_state.events):
                # Adiciona 4 espaços de indentação
                f.write('    ' + repr(evento))
                # Adiciona vírgula e quebra de linha se não for o último elemento
                if idx < len(st.session_state.events) - 1:
                    f.write(',\n')
                else:
                    f.write('\n')
            f.write(']')
    except Exception as e:
        st.error(f"Erro ao salvar eventos: {e}")

# Função para salvar evento individual
def salvar_evento(evento):
    if 'events' not in st.session_state:
        st.session_state.events = []
    st.session_state.events.append(evento)
    salvar_eventos_arquivo()
    # Removida a linha st.session_state.sync()

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
            margin-left: 40px;
            margin-right: auto;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Inicializa o estado da sessão para eventos se não existir
# Remover esta inicialização duplicada
if 'events' not in st.session_state:
    st.session_state.events = carregar_eventos()

# Substitua a função carregar_eventos
# Remover todo este bloco comentado
# def carregar_eventos():
#     try:
#         eventos = list(collection.find({}, {'_id': 0}))
#         return eventos
#     except Exception as e:
#         st.error(f"Erro ao carregar eventos: {e}")
#     return []

# def salvar_eventos_arquivo():
#     try:
#         collection.delete_many({})
#         if st.session_state.events:
#             collection.insert_many(st.session_state.events)
#     except Exception as e:
#         st.error(f"Erro ao salvar eventos: {e}")

# Inicializa o estado da sessão com eventos do arquivo
# Manter apenas esta inicialização
if 'events' not in st.session_state:
    st.session_state.events = carregar_eventos()

# Modifique a função salvar_evento para incluir o salvamento em arquivo
# Remover esta função duplicada
def salvar_evento(evento):
    if 'events' not in st.session_state:
        st.session_state.events = []
    st.session_state.events.append(evento)
    salvar_eventos_arquivo()
    # Removida a linha st.session_state.sync()

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
    data = st.date_input("Data da Reunião")
    hora_inicio = st.time_input("Hora de Início")
    duracao = st.number_input("Duração (horas)", min_value=0.5, max_value=8.0, value=1.0, step=0.5)
    
    # Detalhes da reunião
    titulo = st.text_input("Título da Reunião")
    descricao = st.text_area("Descrição")
    
    # Botão para agendar
    if st.button("Agendar Reunião"):
        if not titulo or not participantes:
            st.error("Por favor, preencha o título e selecione pelo menos um participante.")
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
                    st.error(f"Já existe uma reunião agendada para este horário: {evento['title']}")
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
    "locale": "pt-br"
}

# Exibe o calendário com os eventos
events = st.session_state.get('events', [])
calendar(events=events, options=calendar_options)

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
            with st.expander(f"{evento['title']} - {evento['start'][:10]}"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Editar", key=f"edit_button_{idx}"):  # Chave única para botão de editar
                        st.session_state.editing_event = idx
                        st.session_state.edit_title = evento['title']
                        st.session_state.edit_start = datetime.fromisoformat(evento['start'])
                        st.session_state.edit_end = datetime.fromisoformat(evento['end'])
                        st.session_state.edit_description = evento['description'].split('\n\n')[1] if '\n\n' in evento['description'] else ''
                        st.session_state.edit_dept = evento['description'].split('\n')[0].replace('Departamento: ', '')
                        st.session_state.edit_participants = evento['description'].split('\n')[1].replace('Participantes: ', '')
                        st.rerun()
                
                with col2:
                    if st.button("Cancelar Reunião", key=f"cancel_button_{idx}"):  # Chave única para botão de cancelar
                        events.pop(idx)
                        salvar_eventos_arquivo()
                        st.success("Reunião cancelada com sucesso!")
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
                
                st.session_state.events[st.session_state.editing_event] = evento_atualizado
                salvar_eventos_arquivo()
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